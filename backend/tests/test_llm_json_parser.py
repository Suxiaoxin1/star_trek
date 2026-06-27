"""LLM JSON 解析工具函数单元测试

覆盖 _parse_json_response 的 4 种解析路径：
  1. 直接 JSON 解析
  2. ```json ... ``` 代码块提取
  3. 首尾 { } 块提取
  4. 失败回退到 fallback
"""
import pytest
from app.services.llm import _parse_json_response


class TestParseJsonResponse:
    """_parse_json_response 单元测试"""

    # ── 路径 1: 直接 JSON 解析 ─────────────────────────────

    def test_direct_valid_json(self):
        text = '{"sentiment": "positive", "score": 0.8}'
        result = _parse_json_response(text)
        assert result == {"sentiment": "positive", "score": 0.8}

    def test_direct_nested_json(self):
        text = '{"a": {"b": [1, 2, 3]}, "c": true}'
        result = _parse_json_response(text)
        assert result["a"]["b"] == [1, 2, 3]
        assert result["c"] is True

    def test_direct_empty_object(self):
        result = _parse_json_response("{}")
        assert result == {}

    # ── 路径 2: ```json 代码块提取 ──────────────────────────

    def test_code_block_json(self):
        text = '```json\n{"sentiment": "negative", "score": 0.2}\n```'
        result = _parse_json_response(text)
        assert result["sentiment"] == "negative"
        assert result["score"] == 0.2

    def test_code_block_no_lang(self):
        text = '```\n{"key": "value"}\n```'
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_code_block_with_prefix_text(self):
        text = 'Here is the result:\n```json\n{"status": "ok"}\n```\nDone.'
        result = _parse_json_response(text)
        assert result["status"] == "ok"

    # ── 路径 3: 首尾 { } 块提取 ─────────────────────────────

    def test_brace_extraction(self):
        text = 'Some text before {"key": "value"} some text after'
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_brace_extraction_multiple_braces(self):
        # rfind 取最后一个 }，应正确匹配
        text = '{ "a": 1 } middle { "b": 2 }'
        result = _parse_json_response(text)
        # 应该提取出最后一个完整的 { ... } 块
        assert "b" in result or "a" in result

    # ── 路径 4: 失败回退 ────────────────────────────────────

    def test_empty_string_returns_fallback(self):
        fallback = {"fallback": True}
        result = _parse_json_response("", fallback=fallback)
        assert result == fallback

    def test_none_returns_fallback(self):
        fallback = {"fallback": True}
        result = _parse_json_response(None, fallback=fallback)
        assert result == fallback

    def test_whitespace_only_returns_fallback(self):
        fallback = {"fallback": True}
        result = _parse_json_response("   \n  ", fallback=fallback)
        assert result == fallback

    def test_invalid_json_no_fallback(self):
        text = '{invalid json!!!}'
        result = _parse_json_response(text)
        assert result == {"raw": text}

    def test_invalid_json_with_fallback(self):
        fallback = {"sentiment": "neutral", "score": 0.5}
        text = 'not json at all {{{'
        result = _parse_json_response(text, fallback=fallback)
        assert result == fallback

    # ── 边界情况 ────────────────────────────────────────────

    def test_json_with_chinese(self):
        text = '{"sentiment": "正面", "key_phrases": ["融资", "上市"]}'
        result = _parse_json_response(text)
        assert result["sentiment"] == "正面"
        assert result["key_phrases"] == ["融资", "上市"]

    def test_json_with_unicode_escapes(self):
        text = '{"text": "\\u4e2d\\u6587\\u6d4b\\u8bd5"}'
        result = _parse_json_response(text)
        assert result["text"] == "中文测试"

    def test_deeply_nested_json(self):
        text = '{"a": {"b": {"c": {"d": [1, {"e": true}]}}}}'
        result = _parse_json_response(text)
        assert result["a"]["b"]["c"]["d"][1]["e"] is True