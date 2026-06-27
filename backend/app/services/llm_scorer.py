"""大模型选型评分引擎

五维加权评分：
  cost_efficiency   成本效益  30%
  capability_match  能力匹配  30%
  reliability       可靠性    20%
  compliance        合规性    10%
  ecosystem         生态完善  10%

支持：
  - 场景专属权重调整（代码/客服/文档/推理/通用）
  - 预算预设（小型/中型/大型团队）
  - china_compliance 一票否决
  - 返回带完整明细的评分列表（降序）
"""
from __future__ import annotations

import math
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Competitor, CompetitorFeature, PricingHistory

logger = logging.getLogger(__name__)

# ================================================================
#  常量配置
# ================================================================

# 基础权重
BASE_WEIGHTS: dict[str, float] = {
    "cost_efficiency":  0.30,
    "capability_match": 0.30,
    "reliability":      0.20,
    "compliance":       0.10,
    "ecosystem":        0.10,
}

# 场景专属权重覆盖（仅列出与基础权重不同的维度）
SCENARIO_WEIGHT_OVERRIDES: dict[str, dict[str, float]] = {
    "code": {
        "capability_match": 0.40,
        "cost_efficiency":  0.25,
        "reliability":      0.20,
        "compliance":       0.05,
        "ecosystem":        0.10,
    },
    "customer_service": {
        "cost_efficiency":  0.35,
        "capability_match": 0.25,
        "reliability":      0.20,
        "compliance":       0.10,
        "ecosystem":        0.10,
    },
    "document": {
        "capability_match": 0.35,
        "cost_efficiency":  0.30,
        "reliability":      0.15,
        "compliance":       0.15,
        "ecosystem":        0.05,
    },
    "reasoning": {
        "capability_match": 0.45,
        "cost_efficiency":  0.20,
        "reliability":      0.20,
        "compliance":       0.05,
        "ecosystem":        0.10,
    },
    "general": BASE_WEIGHTS,
}

# 月预算预设（USD）
BUDGET_PRESETS: dict[str, float] = {
    "small":  500.0,    # 小型团队 / 个人项目
    "medium": 5000.0,   # 中型团队
    "large":  50000.0,  # 大型企业
}

# 生态完善度基准（来源于 metadata.ecosystem_score，或按已知信息默认填充）
DEFAULT_ECOSYSTEM_SCORES: dict[str, float] = {
    "OpenAI":    0.95,
    "Anthropic": 0.80,
    "Google":    0.85,
    "DeepSeek":  0.70,
    "阿里云":    0.75,
    "百度":      0.70,
    "腾讯":      0.65,
    "字节跳动":  0.65,
    "智谱AI":    0.60,
    "Mistral":   0.65,
    "Meta":      0.72,
}


# ================================================================
#  评分函数（每项返回 0.0 ~ 1.0）
# ================================================================

def _score_cost(
    meta: dict[str, Any],
    monthly_budget: float,
    monthly_tokens: float = 10_000_000,
) -> float:
    """成本效益评分（对数映射，月 token 用量下的预算利用率）

    monthly_tokens: 预计每月 token 总用量（默认 1000 万）
    """
    try:
        input_price  = float(meta.get("input_price_per_1M",  meta.get("price_per_1M", 0)))
        output_price = float(meta.get("output_price_per_1M", input_price))
        # 假设输入:输出 = 3:1
        monthly_cost = (input_price * monthly_tokens * 0.75 + output_price * monthly_tokens * 0.25) / 1_000_000
        if monthly_cost <= 0:
            return 0.5  # 无价格信息，给中立分
        ratio = monthly_budget / monthly_cost  # 预算能覆盖多少倍
        # log 映射：ratio≥10 → 1.0；ratio=1 → 0.5；ratio<0.1 → ~0
        score = min(1.0, max(0.0, math.log10(ratio + 0.1) / math.log10(11)))
        return round(score, 4)
    except Exception:
        return 0.5


def _score_capability(meta: dict[str, Any], scenario: str) -> float:
    """能力匹配评分（基于 metadata 中的 benchmark 分值）"""
    # 优先读 scenario 专属 benchmark
    scenario_key = f"benchmark_{scenario}"
    if scenario_key in meta:
        return min(1.0, max(0.0, float(meta[scenario_key]) / 100.0))

    # 回退到通用 benchmark_score（归一化到 0~1）
    if "benchmark_score" in meta:
        return min(1.0, max(0.0, float(meta["benchmark_score"]) / 100.0))

    # 回退到 context_window 作为能力代理指标（≥128k 满分）
    ctx = meta.get("context_window", 0)
    if ctx:
        return min(1.0, math.log2(max(1, int(ctx)) / 4096) / math.log2(128000 / 4096))

    return 0.5


def _score_reliability(meta: dict[str, Any]) -> float:
    """可靠性评分（SLA / uptime / 速率限制综合）"""
    score = 0.5  # 默认中立

    # SLA 可用性（99.9% → 1.0，99% → 0.7，<99% → 线性）
    sla = meta.get("sla_uptime")
    if sla is not None:
        sla = float(sla)
        if sla >= 99.9:
            score = 1.0
        elif sla >= 99.0:
            score = 0.7 + (sla - 99.0) * 0.3
        else:
            score = max(0.0, sla / 99.0 * 0.7)
        return round(score, 4)

    # 无 SLA 数据时，用已知服务商历史口碑估算
    provider_reliability: dict[str, float] = {
        "OpenAI": 0.85, "Anthropic": 0.88, "Google": 0.92,
        "DeepSeek": 0.75, "阿里云": 0.85, "百度": 0.80,
    }
    provider = meta.get("provider", "")
    return provider_reliability.get(provider, 0.70)


def _score_compliance(meta: dict[str, Any], require_china: bool) -> float:
    """合规性评分

    require_china=True 时，china_compliance=False 直接返回 0（一票否决）。
    """
    china_ok = bool(meta.get("china_compliance", False))

    if require_china and not china_ok:
        return 0.0  # 一票否决

    base = 1.0 if china_ok else 0.5

    # 附加合规认证加分（ISO27001, SOC2, GDPR 各 +0.1，上限 1.0）
    bonus = 0.0
    for cert in ("iso27001", "soc2", "gdpr"):
        if meta.get(cert):
            bonus += 0.1
    return min(1.0, base + bonus)


def _score_ecosystem(meta: dict[str, Any], competitor_name: str) -> float:
    """生态完善度评分（SDK、文档、社区、插件生态）"""
    # 优先读取 metadata 中显式写入的 ecosystem_score
    if "ecosystem_score" in meta:
        return min(1.0, max(0.0, float(meta["ecosystem_score"])))

    # 回退到默认评分表（模糊匹配公司名）
    for key, val in DEFAULT_ECOSYSTEM_SCORES.items():
        if key in competitor_name or competitor_name in key:
            return val

    return 0.60  # 未知厂商给默认中低分


# ================================================================
#  主入口
# ================================================================

async def score_llm_competitors(
    db: AsyncSession,
    *,
    scenario: str = "general",
    monthly_budget_usd: float | None = None,
    budget_preset: str | None = None,
    monthly_tokens: float = 10_000_000,
    require_china_compliance: bool = False,
    competitor_ids: list[UUID] | None = None,
) -> list[dict[str, Any]]:
    """对数据库中的大模型竞品评分并排序

    Args:
        db: 异步数据库会话
        scenario: 应用场景（code/customer_service/document/reasoning/general）
        monthly_budget_usd: 月预算（USD），与 budget_preset 二选一
        budget_preset: 预算档次（small/medium/large）
        monthly_tokens: 预计月 token 用量
        require_china_compliance: 是否要求中国合规（一票否决不合规）
        competitor_ids: 限定评分的竞品 ID 列表（None = 全部活跃竞品）

    Returns:
        按总分降序排列的评分列表，每项包含 competitor_id、name、scores、total_score
    """
    # 1. 确定预算
    if monthly_budget_usd is None:
        if budget_preset and budget_preset in BUDGET_PRESETS:
            monthly_budget_usd = BUDGET_PRESETS[budget_preset]
        else:
            monthly_budget_usd = BUDGET_PRESETS["medium"]

    # 2. 确定权重
    weights = SCENARIO_WEIGHT_OVERRIDES.get(scenario, BASE_WEIGHTS)

    # 3. 查询竞品
    q = select(Competitor).where(Competitor.is_active == True)
    if competitor_ids:
        q = q.where(Competitor.id.in_(competitor_ids))
    competitors = (await db.execute(q)).scalars().all()

    results: list[dict[str, Any]] = []

    for comp in competitors:
        meta: dict[str, Any] = comp.metadata_ or {}

        # --- 各维度评分 ---
        s_cost       = _score_cost(meta, monthly_budget_usd, monthly_tokens)
        s_capability = _score_capability(meta, scenario)
        s_reliability = _score_reliability(meta)
        s_compliance = _score_compliance(meta, require_china_compliance)
        s_ecosystem  = _score_ecosystem(meta, comp.name)

        # 合规一票否决
        if s_compliance == 0.0 and require_china_compliance:
            total = 0.0
            vetoed = True
        else:
            total = (
                s_cost       * weights["cost_efficiency"]  +
                s_capability * weights["capability_match"] +
                s_reliability * weights["reliability"]     +
                s_compliance * weights["compliance"]       +
                s_ecosystem  * weights["ecosystem"]
            )
            vetoed = False

        results.append({
            "competitor_id":   str(comp.id),
            "name":            comp.name,
            "name_en":         comp.name_en,
            "tier":            comp.tier,
            "flagship_model":  meta.get("flagship_model"),
            "china_compliance": bool(meta.get("china_compliance", False)),
            "vetoed":          vetoed,
            "scores": {
                "cost_efficiency":  round(s_cost, 4),
                "capability_match": round(s_capability, 4),
                "reliability":      round(s_reliability, 4),
                "compliance":       round(s_compliance, 4),
                "ecosystem":        round(s_ecosystem, 4),
            },
            "weights":         weights,
            "total_score":     round(total, 4),
            "scenario":        scenario,
            "monthly_budget_usd": monthly_budget_usd,
        })

    # 降序排列（被否决的放末尾）
    results.sort(key=lambda x: (0 if x["vetoed"] else 1, x["total_score"]), reverse=True)
    return results


async def get_cost_estimate(
    db: AsyncSession,
    competitor_id: UUID,
    monthly_tokens: float = 10_000_000,
    input_ratio: float = 0.75,
) -> dict[str, Any]:
    """计算指定竞品的 token 费用估算"""
    q = select(Competitor).where(Competitor.id == competitor_id)
    comp = (await db.execute(q)).scalars().first()
    if not comp:
        return {"error": "竞品不存在"}

    meta = comp.metadata_ or {}
    input_price  = float(meta.get("input_price_per_1M", 0))
    output_price = float(meta.get("output_price_per_1M", input_price))
    currency     = meta.get("currency", "USD")

    input_tokens  = monthly_tokens * input_ratio
    output_tokens = monthly_tokens * (1 - input_ratio)
    monthly_cost  = (input_price * input_tokens + output_price * output_tokens) / 1_000_000

    return {
        "competitor_id":   str(competitor_id),
        "name":            comp.name,
        "flagship_model":  meta.get("flagship_model"),
        "currency":        currency,
        "input_price_per_1M":  input_price,
        "output_price_per_1M": output_price,
        "monthly_tokens":  monthly_tokens,
        "input_tokens":    input_tokens,
        "output_tokens":   output_tokens,
        "monthly_cost":    round(monthly_cost, 4),
        "annual_cost":     round(monthly_cost * 12, 4),
    }
