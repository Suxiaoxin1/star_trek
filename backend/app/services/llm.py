"""LLM 集成服务 — OpenAI API 封装

支持：
  - 文本生成 / 补全
  - 情感分析
  - 摘要提取
  - 结构化分析报告生成

兼容 OpenAI 及符合 OpenAI API 格式的其他提供商（如 DeepSeek、通义千问等），
通过 OPENAI_API_BASE 自定义 base_url。
"""
import json
from typing import AsyncGenerator

from openai import AsyncOpenAI
from loguru import logger

from app.config import settings


# ────────────── 全局客户端 ──────────────
def _build_client() -> AsyncOpenAI:
    """根据配置构建 OpenAI 异步客户端"""
    kwargs: dict = {
        "api_key": settings.OPENAI_API_KEY,
    }
    # 自定义 base_url（DeepSeek / 通义等兼容接口）
    if settings.OPENAI_API_BASE:
        kwargs["base_url"] = settings.OPENAI_API_BASE
    return AsyncOpenAI(**kwargs)


_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    """获取 LLM 客户端（懒初始化）"""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，请在 .env 或环境变量中设置")
        _client = _build_client()
        logger.info("LLM client initialized | base_url={}", settings.OPENAI_API_BASE or "https://api.openai.com/v1")
    return _client


# ────────────── 基础能力 ──────────────
async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: dict | None = None,
) -> str:
    """通用 chat completion 调用，返回文本内容"""
    client = get_llm_client()
    model = model or settings.OPENAI_MODEL

    logger.debug("LLM chat | model={} tokens={} msgs={}", model, max_tokens, len(messages))

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    resp = await client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or ""

    # 记录 token 使用量
    if resp.usage:
        logger.info(
            "LLM usage | prompt={} completion={} total={}",
            resp.usage.prompt_tokens,
            resp.usage.completion_tokens,
            resp.usage.total_tokens,
        )
    return content


async def chat_completion_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """流式 chat completion，逐块返回文本"""
    client = get_llm_client()
    model = model or settings.OPENAI_MODEL

    logger.debug("LLM stream | model={} tokens={}", model, max_tokens)

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ────────────── 预置 Prompt 工厂 ──────────────
SYSTEM_PROMPT_SENTIMENT = """\
你是一位专业的市场情报分析师，擅长对商业新闻和行业动态进行情感分析。

请对给定的文本进行情感分析，返回 JSON 格式结果：
{
  "sentiment": "positive" | "neutral" | "negative",
  "sentiment_score": 0.0-1.0 的浮点数（正面倾向越高数值越大）,
  "confidence": 0.0-1.0 的置信度,
  "key_phrases": ["影响情感判断的关键短语列表"],
  "reasoning": "简短的情感判断理由（1-2句话）"
}

分析维度：
1. 对目标公司/产品的影响（正面/负面/中性）
2. 市场信号强度
3. 行业趋势关联性
"""

SYSTEM_PROMPT_SUMMARY = """\
你是一位情报摘要专家。请对给定的市场情报文本生成结构化摘要。

返回 JSON 格式：
{
  "summary": "100-200字的中文摘要",
  "key_points": ["3-5个关键要点"],
  "impact_level": "high" | "medium" | "low",
  "affected_areas": ["受影响的业务领域"],
  "action_items": ["建议的跟进行动（如有）"]
}

要求：
- 摘要简洁准确，突出商业影响
- 关键要点用一句话概括
- 优先关注对竞品格局的影响
"""

SYSTEM_PROMPT_REPORT = """\
你是一位资深竞品分析师，需要基于提供的市场情报数据生成专业的竞品分析报告。

报告应包含以下结构（Markdown 格式）：

# {报告标题}

## 概述
对当前竞品态势的总体判断（2-3段）

## 关键发现
- 逐条列出最重要的 3-5 个发现

## 竞品动态分析
按竞品分组，分析近期的关键动向

## SWOT 分析
| 维度 | 内容 |
|------|------|
| 优势 | ... |
| 劣势 | ... |
| 机会 | ... |
| 威胁 | ... |

## 市场趋势判断
短期和中期的市场趋势预测

## 建议与行动项
针对我方的策略建议

## 风险提示
需要关注的风险点

---
要求：
- 基于事实分析，避免主观臆断
- 数据驱动，引用具体情报内容
- 结论明确，建议可执行
- 中文输出，专业术语可保留英文
"""

SYSTEM_PROMPT_COMPETITOR_ANALYSIS = """\
你是一位竞品分析专家，请根据提供的竞品信息和市场情报，对该竞品进行深度分析。

返回 JSON 格式：
{
  "strengths": ["该竞品的核心优势"],
  "weaknesses": ["该竞品的主要劣势"],
  "market_position": "市场定位描述",
  "threat_level": "high" | "medium" | "low",
  "opportunity_for_us": ["我方可利用的机会"],
  "strategic_recommendations": ["针对该竞品的策略建议"],
  "recent_highlights": ["近期重要动向"],
  "risk_factors": ["风险因素"]
}

要求客观分析，基于提供的事实数据。
"""


# ────────────── JSON 解析工具 ──────────────
def _parse_json_response(text: str, fallback: dict | None = None) -> dict:
    """从 LLM 响应中提取 JSON，支持 markdown 代码块包裹的情况"""
    if not text or not text.strip():
        return fallback or {}

    # 1. 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 尝试提取 ```json ... ``` 代码块
    import re
    json_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. 尝试提取第一个 { ... } 块
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    # 4. 所有解析都失败，返回 fallback
    logger.warning("Failed to parse JSON from LLM response, returning fallback")
    return fallback or {"raw": text}


# ────────────── 预置分析函数 ──────────────
async def analyze_sentiment(text: str, model: str | None = None) -> dict:
    """情感分析：返回结构化情感结果"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_SENTIMENT},
        {"role": "user", "content": f"请分析以下文本的情感倾向：\n\n{text}"},
    ]
    result_text = await chat_completion(
        messages,
        model=model,
        temperature=0.3,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    return _parse_json_response(result_text, fallback={"sentiment": "neutral", "sentiment_score": 0.5})


async def extract_summary(text: str, model: str | None = None) -> dict:
    """摘要提取：返回结构化摘要"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_SUMMARY},
        {"role": "user", "content": f"请生成以下情报的结构化摘要：\n\n{text}"},
    ]
    result_text = await chat_completion(
        messages,
        model=model,
        temperature=0.3,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return _parse_json_response(result_text, fallback={"summary": result_text, "key_points": []})


async def generate_report(
    title: str,
    intelligence_data: list[dict],
    competitor_info: dict | None = None,
    report_type: str = "competitor_analysis",
    model: str | None = None,
) -> str:
    """生成 Markdown 格式的分析报告"""

    # 构建情报上下文
    intel_context = ""
    for idx, intel in enumerate(intelligence_data, 1):
        intel_context += f"\n### 情报 {idx}: {intel.get('title', '未知')}\n"
        intel_context += f"- 分类: {intel.get('category', '未分类')}\n"
        intel_context += f"- 情感: {intel.get('sentiment', '未知')}\n"
        intel_context += f"- 重要度: {intel.get('importance', '未知')}\n"
        intel_context += f"- 来源: {intel.get('source_name', '未知')}\n"
        if intel.get("summary"):
            intel_context += f"- 摘要: {intel['summary']}\n"
        intel_context += f"- 发布时间: {intel.get('published_at', '未知')}\n"

    # 竞品信息
    comp_context = ""
    if competitor_info:
        comp_context = f"\n## 竞品基础信息\n"
        comp_context += f"- 名称: {competitor_info.get('name', '未知')}\n"
        comp_context += f"- 层级: {competitor_info.get('tier', '未知')}\n"
        comp_context += f"- 网站: {competitor_info.get('website', '未知')}\n"
        if competitor_info.get("description"):
            comp_context += f"- 描述: {competitor_info['description']}\n"

    user_content = f"""请根据以下数据生成竞品分析报告：

报告标题：{title}
报告类型：{report_type}

{comp_context}

## 相关市场情报
{intel_context}

请生成完整的专业分析报告。"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_REPORT},
        {"role": "user", "content": user_content},
    ]
    return await chat_completion(
        messages,
        model=model,
        temperature=0.5,
        max_tokens=4096,
    )


async def analyze_competitor(
    competitor_info: dict,
    intelligence_data: list[dict],
    model: str | None = None,
) -> dict:
    """竞品深度分析：返回结构化分析结果"""

    context = f"""竞品信息：
名称: {competitor_info.get('name')}
层级: {competitor_info.get('tier')}
描述: {competitor_info.get('description', '无')}

相关情报（最近 {len(intelligence_data)} 条）：
"""
    for intel in intelligence_data[:10]:
        context += f"- [{intel.get('category', '')}] {intel.get('title')} (情感: {intel.get('sentiment', '未知')})\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_COMPETITOR_ANALYSIS},
        {"role": "user", "content": context},
    ]
    result_text = await chat_completion(
        messages,
        model=model,
        temperature=0.4,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return _parse_json_response(result_text, fallback={"raw": result_text})


async def batch_sentiment_analysis(texts: list[str], model: str | None = None) -> list[dict]:
    """批量情感分析"""
    results = []
    for text in texts:
        try:
            result = await analyze_sentiment(text, model=model)
            results.append(result)
        except Exception as e:
            logger.error("Sentiment analysis failed for text: {}", str(e)[:100])
            results.append({"sentiment": "neutral", "sentiment_score": 0.5, "error": str(e)})
    return results


async def generate_streaming_report(
    title: str,
    intelligence_data: list[dict],
    competitor_info: dict | None = None,
    report_type: str = "competitor_analysis",
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """流式生成分析报告（用于前端实时展示）"""

    intel_context = ""
    for idx, intel in enumerate(intelligence_data, 1):
        intel_context += f"\n### 情报 {idx}: {intel.get('title', '未知')}\n"
        intel_context += f"- 分类: {intel.get('category', '未分类')}\n"
        intel_context += f"- 情感: {intel.get('sentiment', '未知')}\n"
        intel_context += f"- 重要度: {intel.get('importance', '未知')}\n"
        if intel.get("summary"):
            intel_context += f"- 摘要: {intel['summary']}\n"

    comp_context = ""
    if competitor_info:
        comp_context = f"\n## 竞品基础信息\n"
        comp_context += f"- 名称: {competitor_info.get('name', '未知')}\n"
        comp_context += f"- 层级: {competitor_info.get('tier', '未知')}\n"

    user_content = f"""请根据以下数据生成竞品分析报告：

报告标题：{title}
报告类型：{report_type}

{comp_context}

## 相关市场情报
{intel_context}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_REPORT},
        {"role": "user", "content": user_content},
    ]

    async for chunk in chat_completion_stream(messages, model=model, temperature=0.5, max_tokens=4096):
        yield chunk