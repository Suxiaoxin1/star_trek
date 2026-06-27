"""大模型选型路由

端点列表：
  GET /llm-selection/score            — 加权评分排名
  GET /llm-selection/matrix           — 原始对比矩阵
  GET /llm-selection/cost-calculator  — Token 费用估算
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RoleChecker
from app.database import get_db
from app.models import Competitor, CompetitorFeature, PricingHistory
from app.services.llm_scorer import (
    score_llm_competitors,
    get_cost_estimate,
    SCENARIO_WEIGHT_OVERRIDES,
    BUDGET_PRESETS,
    BASE_WEIGHTS,
)

router = APIRouter()

require_viewer = Depends(RoleChecker("admin", "analyst", "viewer"))


# ================================================================
#  1. 加权评分排名
# ================================================================

@router.get("/score", response_model=dict, summary="大模型加权评分排名")
async def llm_score(
    scenario: str = Query(
        "general",
        description="应用场景：code / customer_service / document / reasoning / general",
        pattern="^(code|customer_service|document|reasoning|general)$",
    ),
    budget_preset: str | None = Query(
        None,
        description="预算档次：small(500$/mo) / medium(5000$/mo) / large(50000$/mo)",
        pattern="^(small|medium|large)$",
    ),
    monthly_budget_usd: float | None = Query(
        None, ge=0, description="自定义月预算（USD），优先于 budget_preset"
    ),
    monthly_tokens: float = Query(
        10_000_000, ge=1000, description="预计月 Token 用量（默认 1000 万）"
    ),
    require_china_compliance: bool = Query(
        False, description="是否要求中国合规（True = 不合规直接排除）"
    ),
    db: AsyncSession = Depends(get_db),
    _user=require_viewer,
):
    """对所有活跃大模型竞品进行五维加权评分并降序排列。

    评分维度（可通过 scenario 调整权重）：
    - cost_efficiency   成本效益 (30%)
    - capability_match  能力匹配 (30%)
    - reliability       可靠性   (20%)
    - compliance        合规性   (10%)
    - ecosystem         生态完善 (10%)
    """
    results = await score_llm_competitors(
        db,
        scenario=scenario,
        monthly_budget_usd=monthly_budget_usd,
        budget_preset=budget_preset,
        monthly_tokens=monthly_tokens,
        require_china_compliance=require_china_compliance,
    )
    weights = SCENARIO_WEIGHT_OVERRIDES.get(scenario, BASE_WEIGHTS)
    return {
        "scenario": scenario,
        "weights": weights,
        "monthly_budget_usd": monthly_budget_usd or BUDGET_PRESETS.get(budget_preset or "medium"),
        "require_china_compliance": require_china_compliance,
        "total": len(results),
        "items": results,
    }


# ================================================================
#  2. 原始对比矩阵
# ================================================================

@router.get("/matrix", response_model=dict, summary="大模型功能对比矩阵")
async def llm_matrix(
    category: str | None = Query(
        None, description="功能分类筛选（capability / performance / operations / ecosystem）"
    ),
    db: AsyncSession = Depends(get_db),
    _user=require_viewer,
):
    """返回所有活跃大模型的功能对比矩阵，以竞品为行、功能点为列。"""
    # 查询所有活跃竞品
    comps = (
        await db.execute(select(Competitor).where(Competitor.is_active == True))
    ).scalars().all()

    # 查询所有功能点
    feat_q = select(CompetitorFeature)
    if category:
        feat_q = feat_q.where(CompetitorFeature.category == category)
    features = (await db.execute(feat_q)).scalars().all()

    # 收集所有唯一功能名称（保序）
    feature_names: list[str] = []
    seen: set[str] = set()
    for f in features:
        key = f"{f.category}::{f.feature_name}"
        if key not in seen:
            seen.add(key)
            feature_names.append(key)

    # 构建矩阵
    # { competitor_id -> { feature_key -> support_level } }
    comp_feature_map: dict[str, dict[str, str]] = {str(c.id): {} for c in comps}
    for f in features:
        cid = str(f.competitor_id)
        if cid in comp_feature_map:
            key = f"{f.category}::{f.feature_name}"
            comp_feature_map[cid][key] = f.support_level

    # 查询每个竞品的 metadata（用于展示 token 定价等基础信息）
    rows = []
    for comp in comps:
        meta = comp.metadata_ or {}
        row: dict = {
            "competitor_id":   str(comp.id),
            "name":            comp.name,
            "name_en":         comp.name_en,
            "flagship_model":  meta.get("flagship_model"),
            "context_window":  meta.get("context_window"),
            "input_price_per_1M":  meta.get("input_price_per_1M"),
            "output_price_per_1M": meta.get("output_price_per_1M"),
            "currency":        meta.get("currency", "USD"),
            "china_compliance": bool(meta.get("china_compliance", False)),
            "features":        comp_feature_map.get(str(comp.id), {}),
        }
        rows.append(row)

    return {
        "feature_names": feature_names,
        "total_competitors": len(rows),
        "total_features": len(feature_names),
        "matrix": rows,
    }


# ================================================================
#  3. Token 费用估算
# ================================================================

@router.get("/cost-calculator", response_model=dict, summary="Token 费用估算")
async def cost_calculator(
    competitor_id: UUID = Query(..., description="竞品 ID"),
    monthly_tokens: float = Query(10_000_000, ge=1000, description="月 Token 总用量"),
    input_ratio: float = Query(0.75, ge=0.0, le=1.0, description="输入 Token 占比（默认 75%）"),
    db: AsyncSession = Depends(get_db),
    _user=require_viewer,
):
    """根据竞品的 metadata 中 input/output_price_per_1M 字段估算月度/年度 Token 费用。

    费用 = (input_price × input_tokens + output_price × output_tokens) / 1_000_000
    """
    result = await get_cost_estimate(
        db,
        competitor_id=competitor_id,
        monthly_tokens=monthly_tokens,
        input_ratio=input_ratio,
    )
    return result


# ================================================================
#  4. 场景权重说明（辅助端点）
# ================================================================

@router.get("/scenarios", response_model=dict, summary="支持的场景及权重说明")
async def list_scenarios(_user=require_viewer):
    """返回所有支持的评分场景及对应的维度权重配置。"""
    return {
        "scenarios": {
            name: {
                "weights": weights,
                "description": {
                    "code":             "代码生成/调试：强调能力匹配，降低成本权重",
                    "customer_service": "客服对话：强调成本效益，中等能力要求",
                    "document":         "文档处理：强调能力和合规，适合企业办公",
                    "reasoning":        "复杂推理：极度强调能力，成本优先级最低",
                    "general":          "通用场景：平衡五维权重",
                }.get(name, ""),
            }
            for name, weights in SCENARIO_WEIGHT_OVERRIDES.items()
        },
        "budget_presets": {
            name: {"monthly_usd": usd}
            for name, usd in BUDGET_PRESETS.items()
        },
    }
