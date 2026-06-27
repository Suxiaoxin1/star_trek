"""五维评分引擎单元测试

覆盖：
  - 各维度评分函数（成本/能力/可靠性/合规/生态）
  - 场景专属权重
  - 预算预设
  - 合规一票否决
  - 总分排序
"""
import pytest
from app.services.llm_scorer import (
    _score_cost,
    _score_capability,
    _score_reliability,
    _score_compliance,
    _score_ecosystem,
    BASE_WEIGHTS,
    SCENARIO_WEIGHT_OVERRIDES,
    BUDGET_PRESETS,
)


# ================================================================
#  成本效益评分
# ================================================================

class TestScoreCost:
    def test_low_cost_high_score(self):
        """低成本应得高分"""
        meta = {"input_price_per_1M": 0.5, "output_price_per_1M": 1.5}
        score = _score_cost(meta, monthly_budget=5000)
        assert score >= 0.7

    def test_high_cost_low_score(self):
        """高成本应得低分"""
        meta = {"input_price_per_1M": 30.0, "output_price_per_1M": 60.0}
        score = _score_cost(meta, monthly_budget=500)
        assert score <= 0.3

    def test_no_price_returns_neutral(self):
        """无价格信息返回中立分"""
        score = _score_cost({}, monthly_budget=5000)
        assert score == 0.5

    def test_zero_price_returns_neutral(self):
        """零价格返回中立分"""
        meta = {"input_price_per_1M": 0, "output_price_per_1M": 0}
        score = _score_cost(meta, monthly_budget=5000)
        assert score == 0.5

    def test_generic_price_field(self):
        """兼容 price_per_1M 通用字段"""
        meta = {"price_per_1M": 1.0}
        score = _score_cost(meta, monthly_budget=5000)
        assert 0.0 <= score <= 1.0


# ================================================================
#  能力匹配评分
# ================================================================

class TestScoreCapability:
    def test_scenario_benchmark(self):
        """优先使用 scenario 专属 benchmark"""
        meta = {"benchmark_code": 90}
        score = _score_capability(meta, "code")
        assert score == 0.9

    def test_generic_benchmark(self):
        """回退到通用 benchmark_score"""
        meta = {"benchmark_score": 80}
        score = _score_capability(meta, "general")
        assert score == 0.8

    def test_context_window_proxy(self):
        """无 benchmark 时使用 context_window 代理"""
        meta = {"context_window": 128000}
        score = _score_capability(meta, "general")
        assert score >= 0.9

    def test_small_context_window(self):
        """小窗口容量得分较低"""
        meta = {"context_window": 4096}
        score = _score_capability(meta, "general")
        assert score < 0.5

    def test_no_data_returns_neutral(self):
        """无任何数据返回中立分"""
        score = _score_capability({}, "general")
        assert score == 0.5


# ================================================================
#  可靠性评分
# ================================================================

class TestScoreReliability:
    def test_excellent_sla(self):
        """SLA >= 99.9% 得满分"""
        score = _score_reliability({"sla_uptime": 99.95})
        assert score == 1.0

    def test_good_sla(self):
        """SLA 99%~99.9% 线性插值"""
        score = _score_reliability({"sla_uptime": 99.5})
        assert 0.7 < score < 1.0

    def test_low_sla(self):
        """SLA < 99% 线性衰减"""
        score = _score_reliability({"sla_uptime": 98.0})
        assert score < 0.7

    def test_known_provider(self):
        """已知厂商有默认可靠性"""
        score = _score_reliability({"provider": "OpenAI"})
        assert score == 0.85

    def test_unknown_provider(self):
        """未知厂商给默认分"""
        score = _score_reliability({"provider": "UnknownVendor"})
        assert score == 0.70

    def test_no_data(self):
        """无 SLA 无 provider 使用默认"""
        score = _score_reliability({})
        assert score == 0.70


# ================================================================
#  合规性评分
# ================================================================

class TestScoreCompliance:
    def test_china_compliant_positive(self):
        """中国合规则得分高"""
        score = _score_compliance({"china_compliance": True}, require_china=True)
        assert score >= 1.0

    def test_non_compliant_veto(self):
        """不合规且要求中国合规 → 一票否决"""
        score = _score_compliance({"china_compliance": False}, require_china=True)
        assert score == 0.0

    def test_non_compliant_not_required(self):
        """不合规但不要求中国合规 → 中立分"""
        score = _score_compliance({"china_compliance": False}, require_china=False)
        assert score == 0.5

    def test_extra_certifications(self):
        """附加认证加分"""
        meta = {
            "china_compliance": True,
            "iso27001": True,
            "soc2": True,
            "gdpr": True,
        }
        score = _score_compliance(meta, require_china=True)
        assert score == 1.0  # 上限

    def test_partial_certifications(self):
        """部分认证适当加分"""
        meta = {"china_compliance": True, "iso27001": True}
        score = _score_compliance(meta, require_china=True)
        assert score == 1.1  # 1.0 + 0.1，会被 min(1.0) 截断


# ================================================================
#  生态完善度评分
# ================================================================

class TestScoreEcosystem:
    def test_explicit_score(self):
        """显式 ecosystem_score 优先"""
        score = _score_ecosystem({"ecosystem_score": 0.85}, "Any")
        assert score == 0.85

    def test_known_computer(self):
        """已知厂商模糊匹配"""
        score = _score_ecosystem({}, "OpenAI")
        assert score == 0.95

    def test_unknown_vendor(self):
        """未知厂商默认中低分"""
        score = _score_ecosystem({}, "TinyStartupLLM")
        assert score == 0.60

    def test_chinese_vendor(self):
        """中文厂商名匹配"""
        score = _score_ecosystem({}, "智谱AI")
        assert score == 0.60


# ================================================================
#  权重与场景
# ================================================================

class TestWeightsAndScenarios:
    def test_base_weights_sum_to_one(self):
        """基础权重之和为 1.0"""
        assert sum(BASE_WEIGHTS.values()) == pytest.approx(1.0)

    def test_scenario_weights_sum_to_one(self):
        """所有场景权重之和均为 1.0"""
        for name, weights in SCENARIO_WEIGHT_OVERRIDES.items():
            assert sum(weights.values()) == pytest.approx(1.0), f"{name} weights don't sum to 1"

    def test_code_scenario_emphasizes_capability(self):
        """代码场景下 capability_match 权重最高"""
        code_w = SCENARIO_WEIGHT_OVERRIDES["code"]["capability_match"]
        assert code_w == 0.40

    def test_reasoning_scenario_heavy_capability(self):
        """推理场景 capability_match 权重最高"""
        reason_w = SCENARIO_WEIGHT_OVERRIDES["reasoning"]["capability_match"]
        assert reason_w == 0.45

    def test_budget_presets_exist(self):
        """预算预设都存在且为正数"""
        for preset, amount in BUDGET_PRESETS.items():
            assert amount > 0