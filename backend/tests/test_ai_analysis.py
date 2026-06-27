"""AI 分析集成测试 — 使用 mock 模拟 LLM 调用

覆盖：
  - 情感分析全流程（含 JSON 解析）
  - 摘要提取全流程
  - 报告生成全流程
  - 多模型客户端池
  - Token 用量统计
  - 上下文压缩
  - 重试机制
"""
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta


# ================================================================
#  情感分析集成测试
# ================================================================

class TestSentimentAnalysisIntegration:
    """测试 llm_enhanced.analyze_sentiment 端到端流程"""

    @pytest.mark.asyncio
    async def test_sentiment_positive(self):
        """正面情感分析"""
        from app.services.llm_enhanced import analyze_sentiment
        mock_result = {"sentiment": "positive", "sentiment_score": 0.85, "confidence": 0.92}
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = json.dumps(mock_result)
            result = await analyze_sentiment("公司业绩大幅增长，市场份额显著提升")
            assert result["sentiment"] == "positive"
            assert result["sentiment_score"] == 0.85
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_sentiment_negative(self):
        """负面情感分析"""
        from app.services.llm_enhanced import analyze_sentiment
        mock_result = {"sentiment": "negative", "sentiment_score": 0.15, "confidence": 0.88}
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = json.dumps(mock_result)
            result = await analyze_sentiment("产品出现严重质量问题，用户投诉激增")
            assert result["sentiment"] == "negative"
            assert result["sentiment_score"] == 0.15

    @pytest.mark.asyncio
    async def test_sentiment_neutral(self):
        """中性情感分析"""
        from app.services.llm_enhanced import analyze_sentiment
        mock_result = {"sentiment": "neutral", "sentiment_score": 0.5, "confidence": 0.70}
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = json.dumps(mock_result)
            result = await analyze_sentiment("公司发布了常规季度财报")
            assert result["sentiment"] == "neutral"
            assert result["sentiment_score"] == 0.5

    @pytest.mark.asyncio
    async def test_sentiment_fallback_on_parse_failure(self):
        """LLM 返回非 JSON 时使用 fallback"""
        from app.services.llm_enhanced import analyze_sentiment
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "This is not JSON at all"
            result = await analyze_sentiment("测试文本")
            # fallback 应包含 sentiment 键
            assert "sentiment" in result

    @pytest.mark.asyncio
    async def test_sentiment_with_custom_model(self):
        """使用自定义模型和提供商"""
        from app.services.llm_enhanced import analyze_sentiment
        mock_result = {"sentiment": "positive", "sentiment_score": 0.8}
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = json.dumps(mock_result)
            result = await analyze_sentiment("测试", model="gpt-4", provider="openai")
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args
            assert call_kwargs.kwargs.get("model") == "gpt-4"
            assert call_kwargs.kwargs.get("provider") == "openai"


# ================================================================
#  摘要提取集成测试
# ================================================================

class TestSummaryExtractionIntegration:
    @pytest.mark.asyncio
    async def test_summary_extraction(self):
        """摘要提取"""
        from app.services.llm_enhanced import extract_summary
        mock_result = {
            "summary": "某公司宣布推出新一代大语言模型...",
            "key_points": ["新一代模型", "性能提升", "成本降低"],
            "impact_level": "high",
        }
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = json.dumps(mock_result)
            result = await extract_summary("长文本...")
            assert result["summary"] == mock_result["summary"]
            assert len(result["key_points"]) == 3
            assert result["impact_level"] == "high"

    @pytest.mark.asyncio
    async def test_summary_fallback_to_raw(self):
        """解析失败时回退到原始文本"""
        from app.services.llm_enhanced import extract_summary
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "no json here"
            result = await extract_summary("测试文本")
            assert "summary" in result or "raw" in result


# ================================================================
#  报告生成集成测试
# ================================================================

class TestReportGenerationIntegration:
    @pytest.mark.asyncio
    async def test_report_generation(self):
        """报告生成"""
        from app.services.llm_enhanced import generate_report
        mock_content = "# 竞品分析报告\n\n## 概述\n..."
        intel_data = [
            {"title": "竞品A发布新产品", "category": "产品发布", "sentiment": "negative", "importance": 5},
            {"title": "竞品B获得融资", "category": "融资", "sentiment": "negative", "importance": 4},
        ]
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_content
            result = await generate_report(
                title="Q2 竞品分析报告",
                intelligence_data=intel_data,
                report_type="quarterly",
            )
            assert result == mock_content
            # 验证传入的 messages 包含系统提示和用户内容
            call_args = mock_chat.call_args
            messages = call_args.kwargs.get("messages", [])
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert "Q2 竞品分析报告" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_report_with_competitor_info(self):
        """带竞品信息的报告生成"""
        from app.services.llm_enhanced import generate_report
        with patch("app.services.llm_enhanced.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "# Report"
            result = await generate_report(
                title="测试报告",
                intelligence_data=[],
                competitor_info={"name": "竞品A", "tier": "direct"},
            )
            assert result == "# Report"


# ================================================================
#  多模型客户端池
# ================================================================

class TestMultiClientPool:
    def test_list_models_empty(self):
        """无配置时返回空列表"""
        from app.services.llm_enhanced import get_pool
        pool = get_pool()
        # 如果 MODEL_CONFIGS_JSON 为空且没有 OPENAI_API_KEY，应为空
        with patch("app.config_multi_model.settings.MODEL_CONFIGS_JSON", ""):
            with patch("app.config.settings.OPENAI_API_KEY", ""):
                models = pool.list_models()
                assert models == []

    def test_list_models_with_default(self):
        """有默认配置时返回列表"""
        from app.services.llm_enhanced import get_pool
        pool = get_pool()
        with patch("app.config.settings.OPENAI_API_KEY", "test-key"):
            with patch("app.config.settings.OPENAI_API_BASE", ""):
                with patch("app.config.settings.OPENAI_MODEL", "gpt-4o-mini"):
                    models = pool.list_models()
                    assert len(models) >= 1
                    assert models[0]["id"] == "default"
                    assert models[0]["model_id"] == "gpt-4o-mini"

    def test_get_client_fallback(self):
        """获取不存在的 provider 时回退到默认"""
        from app.services.llm_enhanced import get_pool
        pool = get_pool()
        with patch("app.config.settings.OPENAI_API_KEY", "test-key"):
            with patch("app.config.settings.OPENAI_API_BASE", ""):
                client = pool.get_client("nonexistent_provider")
                assert client is not None

    def test_get_model_name(self):
        """模型名称解析"""
        from app.services.llm_enhanced import get_pool
        pool = get_pool()
        with patch("app.config.settings.OPENAI_MODEL", "gpt-4o-mini"):
            name = pool.get_model_name(None)
            assert name == "gpt-4o-mini"
            name_explicit = pool.get_model_name(None, model_id="claude-3-opus")
            assert name_explicit == "claude-3-opus"


# ================================================================
#  Token 用量统计
# ================================================================

class TestTokenUsageStats:
    def test_record_and_query(self):
        """记录用量并查询"""
        from app.services.llm_enhanced import record_token_usage, get_token_usage_summary
        record_token_usage("openai", "gpt-4", 1000, 500, 1500)
        record_token_usage("openai", "gpt-4", 2000, 1000, 3000)
        record_token_usage("anthropic", "claude-3", 500, 200, 700)

        summary = get_token_usage_summary(period="day")
        assert summary["call_count"] == 3
        assert summary["prompt_tokens"] == 3500
        assert summary["completion_tokens"] == 1700
        assert summary["total_tokens"] == 5200
        assert "openai" in summary["by_provider"]
        assert "anthropic" in summary["by_provider"]

    def test_filter_by_provider(self):
        """按提供商过滤"""
        from app.services.llm_enhanced import record_token_usage, get_token_usage_summary
        record_token_usage("openai", "gpt-4", 1000, 500, 1500)
        record_token_usage("anthropic", "claude-3", 500, 200, 700)

        openai_summary = get_token_usage_summary(period="day", provider="openai")
        assert openai_summary["call_count"] == 1
        assert openai_summary["total_tokens"] == 1500

    def test_period_filters(self):
        """不同周期过滤"""
        from app.services.llm_enhanced import record_token_usage, get_token_usage_summary
        record_token_usage("openai", "gpt-4", 1000, 500, 1500)

        for period in ["day", "week", "month"]:
            summary = get_token_usage_summary(period=period)
            assert "period" in summary
            assert summary["call_count"] >= 0


# ================================================================
#  上下文压缩
# ================================================================

class TestContextCompression:
    def test_compress_within_limit(self):
        """文本在限制内时原样返回"""
        from app.services.llm_enhanced import compress_context
        texts = ["short text"]
        result = compress_context(texts, max_tokens=1000)
        assert result == "short text"

    def test_compress_truncates(self):
        """超长文本被截断"""
        from app.services.llm_enhanced import compress_context
        long_text = "x" * 50000
        result = compress_context([long_text], max_tokens=1000)
        assert len(result) < len(long_text)

    def test_compress_multiple_texts(self):
        """多文本拼接"""
        from app.services.llm_enhanced import compress_context
        texts = ["text1", "text2", "text3"]
        result = compress_context(texts, max_tokens=10000)
        assert "text1" in result
        assert "text2" in result
        assert "text3" in result


# ================================================================
#  重试机制
# ================================================================

class TestRetryMechanism:
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_third_attempt(self):
        """第3次重试成功后返回结果"""
        from app.services.llm_enhanced import _retry_with_backoff, _RETRYABLE_ERRORS
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Temporary failure")
            return "success"

        result = await _retry_with_backoff(flaky_func, max_retries=3)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self):
        """超过最大重试次数后抛出异常"""
        from app.services.llm_enhanced import _retry_with_backoff
        async def always_fail():
            raise TimeoutError("Permanent failure")

        with pytest.raises(TimeoutError):
            await _retry_with_backoff(always_fail, max_retries=2, base_delay=0.01)

    @pytest.mark.asyncio
    async def test_non_retryable_error_raises_immediately(self):
        """非可重试错误（如 401）立即抛出"""
        from openai import AuthenticationError
        from app.services.llm_enhanced import _retry_with_backoff

        async def auth_error():
            raise AuthenticationError("Invalid API key", response=MagicMock(), body=None)

        with pytest.raises(AuthenticationError):
            await _retry_with_backoff(auth_error, max_retries=3)


# ================================================================
#  批量情感分析
# ================================================================

class TestBatchSentimentAnalysis:
    @pytest.mark.asyncio
    async def test_batch_success(self):
        """批量分析全部成功"""
        from app.services.llm_enhanced import batch_sentiment_analysis
        mock_result = {"sentiment": "positive", "sentiment_score": 0.8}
        with patch("app.services.llm_enhanced.analyze_sentiment", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result
            texts = ["文本1", "文本2", "文本3"]
            results = await batch_sentiment_analysis(texts)
            assert len(results) == 3
            assert mock_analyze.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self):
        """批量分析部分失败"""
        from app.services.llm_enhanced import batch_sentiment_analysis
        async def analyze_side_effect(text):
            if "bad" in text:
                raise ValueError("LLM error")
            return {"sentiment": "positive", "sentiment_score": 0.8}

        with patch("app.services.llm_enhanced.analyze_sentiment", new_callable=AsyncMock, side_effect=analyze_side_effect):
            texts = ["good text", "bad text", "also good"]
            results = await batch_sentiment_analysis(texts)
            assert len(results) == 3
            # 失败的条目应有 error 字段
            bad_result = [r for r in results if "error" in r]
            assert len(bad_result) == 1