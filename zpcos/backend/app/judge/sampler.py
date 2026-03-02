"""Sampler — 複数モデルから回答サンプリング。"""

import asyncio
import json
from app.gateway import call_llm
from app.judge.models import Segment, SampleResult

JUDGE_MODELS = ["fast", "quality", "value"]


async def _check_segment(segment: Segment, context: str, model_group: str) -> SampleResult:
    """1つのセグメントを1つのモデルで検証。"""
    prompt = f"""以下の主張が正しいかどうかを検証してください。

コンテキスト: {context}

主張: {segment.text}
カテゴリ: {segment.category}

JSON で返してください: {{"agrees": true/false, "reason": "..."}}
JSON のみを返し、他のテキストは含めないでください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group=model_group,
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    try:
        result = json.loads(content.strip())
    except json.JSONDecodeError:
        result = {"agrees": False, "reason": "Parse error"}

    return SampleResult(
        segment_id=segment.id,
        model_name=model_group,
        response=result.get("reason", ""),
        agrees=result.get("agrees", False),
    )


async def sample(segments: list[Segment], context: str) -> list[SampleResult]:
    """全セグメントを全モデルで並列検証。"""
    tasks = []
    for seg in segments:
        for model in JUDGE_MODELS:
            tasks.append(_check_segment(seg, context, model))
    return await asyncio.gather(*tasks)
