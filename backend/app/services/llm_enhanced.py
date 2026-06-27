"""LLM 集成服务增强版 - 多模型客户端池 + 重试 + Token 统计"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIError
from loguru import logger

from app.config_multi_model import settings as multi_settings

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _ensure_prompts_dir() -> Path:
    _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    return _PROMPTS_DIR


def load_prompt_template(name: str, fallback: str | None = None) -> str:
    path = _ensure_prompts_dir() / f"{name}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    if fallback:
        path.write_text(fallback, encoding="utf-8")
        logger.info("Created prompt template: {}", name)
        return fallback
    return ""


def save_prompt_template(name: str, content: str) -> None:
    path = _ensure_prompts_dir() / f"{name}.txt"
    path.write_text(content, encoding="utf-8")
    logger.info("Updated prompt template: {}", name)


class MultiClientPool:
    def __init__(self):
        self._clients: dict[str, AsyncOpenAI] = {}
        self._configs: list[Any] = []
        self._refresh()

    def _refresh(self):
        self._configs = multi_settings.model_configs
        self._clients = {}
        for cfg in self._configs:
            if not cfg.is_active:
                continue
            key = cfg.provider
            kwargs = {"api_key": cfg.api_key}
            if cfg.base_url:
                kwargs["base_url"] = cfg.base_url
            self._clients[key] = AsyncOpenAI(**kwargs)
        from app.config import settings
        if settings.OPENAI_API_KEY and "default" not in self._clients:
            kwargs = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_API_BASE:
                kwargs["base_url"] = settings.OPENAI_API_BASE
            self._clients["default"] = AsyncOpenAI(**kwargs)

    def get_client(self, provider: str | None = None) -> AsyncOpenAI:
        if not self._clients:
            self._refresh()
        if not provider or provider == "default":
            return self._clients.get("default") or self._clients.get(list(self._clients.keys())[0])
        client = self._clients.get(provider)
        if client:
            return client
        for key, cl in self._clients.items():
            if provider.lower() in key.lower() or provider.lower() in str(cl.base_url).lower():
                return cl
        logger.warning("Provider '{}' not found, falling back to default", provider)
        return self._clients.get("default") or self._clients.get(list(self._clients.keys())[0])

    def get_model_name(self, provider: str | None, model_id: str | None = None) -> str:
        from app.config import settings
        if model_id:
            return model_id
        if provider and provider != "default":
            for cfg in self._configs:
                if cfg.name == provider and cfg.is_active:
                    return cfg.model_id or settings.OPENAI_MODEL
        return settings.OPENAI_MODEL

    def list_models(self) -> list[dict]:
        self._refresh()
        result = []
        for cfg in self._configs:
            if not cfg.is_active:
                continue
            result.append({
                "id": cfg.name, "provider": cfg.provider, "model_id": cfg.model_id,
                "base_url": cfg.base_url or "https://api.openai.com/v1",
                "max_tokens": cfg.max_tokens, "context_window": cfg.context_window,
                "is_default": cfg.is_default, "status": "active",
            })
        from app.config import settings
        if settings.OPENAI_API_KEY:
            result.append({
                "id": "default", "provider": "default", "model_id": settings.OPENAI_MODEL,
                "base_url": settings.OPENAI_API_BASE or "https://api.openai.com/v1",
                "max_tokens": 4096, "context_window": 128000,
                "is_default": not any(c.is_default for c in self._configs),
                "status": "active",
            })
        return result


_pool = MultiClientPool()


def get_pool() -> MultiClientPool:
    return _pool


_RETRYABLE_ERRORS = (RateLimitError, APITimeoutError, TimeoutError, ConnectionError)


async def _retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await func()
        except _RETRYABLE_ERRORS as e:
            last_exc = e
            delay = base_delay * (2 ** attempt)
            logger.warning("LLM call failed (attempt {}/{}): {}. Retrying in {:.1f}s", attempt + 1, max_retries, str(e)[:100], delay)
            await asyncio.sleep(delay)
        except APIError as e:
            if e.status_code in (401, 403):
                raise
            last_exc = e
            delay = base_delay * (2 ** attempt)
            logger.warning("LLM API error (attempt {}): {}. Retrying.", attempt + 1, str(e)[:100])
            await asyncio.sleep(delay)
        except Exception as e:
            logger.error("Unexpected LLM error: {}", str(e)[:200])
            raise
    raise last_exc or RuntimeError("LLM call failed after retries")


_token_usage_log: list[dict] = []


def record_token_usage(provider: str, model: str, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
    _token_usage_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider, "model": model,
        "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens,
    })


def get_token_usage_summary(period: str = "day", provider: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    if period == "day":
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        cutoff = now - timedelta(days=now.weekday())
        cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cutoff_iso = cutoff.isoformat()
    filtered = [u for u in _token_usage_log if u["timestamp"] >= cutoff_iso and (not provider or u["provider"] == provider)]
    total_prompt = sum(u["prompt_tokens"] for u in filtered)
    total_completion = sum(u["completion_tokens"] for u in filtered)
    total = sum(u["total_tokens"] for u in filtered)
    call_count = len(filtered)
    estimated_cost = (total_prompt / 1_000_000) * 0.015 + (total_completion / 1_000_000) * 0.06
    by_provider: dict[str, dict] = {}
    for u in filtered:
        p = u["provider"]
        if p not in by_provider:
            by_provider[p] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        by_provider[p]["calls"] += 1
        by_provider[p]["prompt_tokens"] += u["prompt_tokens"]
        by_provider[p]["completion_tokens"] += u["completion_tokens"]
        by_provider[p]["total_tokens"] += u["total_tokens"]
    return {
        "period": period, "call_count": call_count,
        "prompt_tokens": total_prompt, "completion_tokens": total_completion,
        "total_tokens": total, "estimated_cost_usd": round(estimated_cost, 6),
        "by_provider": by_provider,
    }


def compress_context(texts: list[str], max_tokens: int = 8000) -> str:
    char_limit = max_tokens * 4
    result = []
    total = 0
    for text in texts:
        if total + len(text) > char_limit:
            result.append(text[: char_limit - total])
            break
        result.append(text)
        total += len(text)
    return "\n\n".join(result)


async def chat_completion(
    messages: list[dict], model: str | None = None, provider: str | None = None,
    temperature: float = 0.7, max_tokens: int = 4096, response_format: dict | None = None,
) -> str:
    pool = get_pool()
    client = pool.get_client(provider)
    resolved_model = pool.get_model_name(provider, model)
    async def _call():
        kwargs: dict = {"model": resolved_model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if response_format:
            kwargs["response_format"] = response_format
        resp = await client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        if resp.usage:
            record_token_usage(provider or "default", resolved_model, resp.usage.prompt_tokens, resp.usage.completion_tokens, resp.usage.total_tokens)
        return content
    return await _retry_with_backoff(_call)


async def chat_completion_stream(
    messages: list[dict], model: str | None = None, provider: str | None = None,
    temperature: float = 0.7, max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    pool = get_pool()
    client = pool.get_client(provider)
    resolved_model = pool.get_model_name(provider, model)
    stream = await client.chat.completions.create(
        model=resolved_model, messages=messages, temperature=temperature, max_tokens=max_tokens, stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


_TEMPLATE_SENTIMENT = "You are a professional market intelligence analyst specializing in sentiment analysis. Return JSON with sentiment, sentiment_score, confidence, key_phrases, reasoning."
_TEMPLATE_SUMMARY = "You are an intelligence summary expert. Return JSON with summary, key_points, impact_level, affected_areas, action_items."
_TEMPLATE_REPORT = "You are a senior competitive analyst. Generate a professional competitive analysis report in Markdown with sections: Overview, Key Findings, Competitor Dynamics, SWOT, Market Trends, Recommendations, Risk Alerts."
_TEMPLATE_COMPETITOR_ANALYSIS = "You are a competitive analysis expert. Return JSON with strengths, weaknesses, market_position, threat_level, opportunity_for_us, strategic_recommendations, recent_highlights, risk_factors."

SYSTEM_PROMPT_SENTIMENT = load_prompt_template("sentiment", _TEMPLATE_SENTIMENT)
SYSTEM_PROMPT_SUMMARY = load_prompt_template("summary", _TEMPLATE_SUMMARY)
SYSTEM_PROMPT_REPORT = load_prompt_template("report", _TEMPLATE_REPORT)
SYSTEM_PROMPT_COMPETITOR_ANALYSIS = load_prompt_template("competitor_analysis", _TEMPLATE_COMPETITOR_ANALYSIS)


async def analyze_sentiment(text: str, model: str | None = None, provider: str | None = None) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT_SENTIMENT}, {"role": "user", "content": text}]
    result_text = await chat_completion(messages, model=model, provider=provider, temperature=0.3, max_tokens=1024, response_format={"type": "json_object"})
    return _parse_json_response(result_text, fallback={"sentiment": "neutral", "sentiment_score": 0.5})


async def extract_summary(text: str, model: str | None = None, provider: str | None = None) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT_SUMMARY}, {"role": "user", "content": text}]
    result_text = await chat_completion(messages, model=model, provider=provider, temperature=0.3, max_tokens=2048, response_format={"type": "json_object"})
    return _parse_json_response(result_text, fallback={"summary": result_text, "key_points": []})


async def generate_report(title: str, intelligence_data: list[dict], competitor_info: dict | None = None, report_type: str = "competitor_analysis", model: str | None = None, provider: str | None = None) -> str:
    intel_context = ""
    for idx, intel in enumerate(intelligence_data, 1):
        intel_context += f"\n### Intel {idx}: {intel.get('title', 'Unknown')}\n"
        intel_context += f"- Category: {intel.get('category', 'Uncategorized')}\n"
        intel_context += f"- Sentiment: {intel.get('sentiment', 'Unknown')}\n"
        intel_context += f"- Importance: {intel.get('importance', 'Unknown')}\n"
        if intel.get("summary"):
            intel_context += f"- Summary: {intel['summary']}\n"
    comp_context = ""
    if competitor_info:
        comp_context = f"\n## Competitor Info\n- Name: {competitor_info.get('name', 'Unknown')}\n- Tier: {competitor_info.get('tier', 'Unknown')}\n"
    user_content = f"Generate a competitive analysis report.\n\nTitle: {title}\nType: {report_type}\n{comp_context}\n\nIntelligence Data:\n{compress_context([intel_context])}"
    messages = [{"role": "system", "content": SYSTEM_PROMPT_REPORT}, {"role": "user", "content": user_content}]
    return await chat_completion(messages, model=model, provider=provider, temperature=0.5, max_tokens=4096)


async def analyze_competitor(competitor_info: dict, intelligence_data: list[dict], model: str | None = None, provider: str | None = None) -> dict:
    context = f"Competitor: {competitor_info.get('name')}\nTier: {competitor_info.get('tier')}\nDescription: {competitor_info.get('description', '')}\n\nRecent Intelligence ({len(intelligence_data)} items):\n"
    for intel in intelligence_data[:10]:
        context += f"- [{intel.get('category', '')}] {intel.get('title')}\n"
    messages = [{"role": "system", "content": SYSTEM_PROMPT_COMPETITOR_ANALYSIS}, {"role": "user", "content": context}]
    result_text = await chat_completion(messages, model=model, provider=provider, temperature=0.4, max_tokens=2048, response_format={"type": "json_object"})
    return _parse_json_response(result_text, fallback={"raw": result_text})


async def batch_sentiment_analysis(texts: list[str], model: str | None = None, provider: str | None = None) -> list[dict]:
    results = []
    for text in texts:
        try:
            results.append(await analyze_sentiment(text, model=model, provider=provider))
        except Exception as e:
            logger.error("Sentiment analysis failed: {}", str(e)[:100])
            results.append({"sentiment": "neutral", "sentiment_score": 0.5, "error": str(e)})
    return results


async def generate_streaming_report(title: str, intelligence_data: list[dict], competitor_info: dict | None = None, report_type: str = "competitor_analysis", model: str | None = None, provider: str | None = None) -> AsyncGenerator[str, None]:
    intel_context = ""
    for idx, intel in enumerate(intelligence_data, 1):
        intel_context += f"\n### Intel {idx}: {intel.get('title', 'Unknown')}\n"
        intel_context += f"- Category: {intel.get('category', 'Uncategorized')}\n"
        if intel.get("summary"):
            intel_context += f"- Summary: {intel['summary']}\n"
    comp_context = ""
    if competitor_info:
        comp_context = f"\n## Competitor: {competitor_info.get('name', 'Unknown')}\n"
    user_content = f"Generate report. Title: {title}\nType: {report_type}\n{comp_context}\nData: {compress_context([intel_context])}"
    messages = [{"role": "system", "content": SYSTEM_PROMPT_REPORT}, {"role": "user", "content": user_content}]
    async for chunk in chat_completion_stream(messages, model=model, provider=provider, temperature=0.5, max_tokens=4096):
        yield chunk


def _parse_json_response(text: str, fallback: dict | None = None) -> dict:
    if not text or not text.strip():
        return fallback or {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    json_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1).strip())
        except json.JSONDecodeError:
            pass
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass
    logger.warning("Failed to parse JSON from LLM response")
    return fallback or {"raw": text}


def list_available_models() -> list[dict]:
    return get_pool().list_models()


def get_model_config(provider: str) -> dict | None:
    for cfg in multi_settings.model_configs:
        if cfg.provider == provider:
            return cfg.model_dump()
    return None
