from __future__ import annotations
import json
from typing import AsyncIterator
from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

WRITING_MODEL = "deepseek-v4-pro"
LIGHT_MODEL = "deepseek-v4-flash"


async def chat_stream(
    messages: list[dict],
    model: str = WRITING_MODEL,
    temperature: float = 0.75,
    max_tokens: int = 4096,
    enable_thinking: bool = True,
) -> AsyncIterator[dict]:
    extra = {}
    if enable_thinking:
        extra["thinking"] = {"type": "enabled"}
    extra["reasoning_effort"] = "high" if model == WRITING_MODEL else "minimal"

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
        extra_body=extra,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta is None:
            continue
        out = {}
        if getattr(delta, "reasoning_content", None):
            out["reasoning"] = delta.reasoning_content
        if delta.content:
            out["content"] = delta.content
        if out:
            yield out


async def chat_simple(
    prompt: str,
    system: str = "",
    model: str = LIGHT_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )
    return resp.choices[0].message.content or ""
