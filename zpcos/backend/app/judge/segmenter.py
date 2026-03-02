"""Segmenter — テキストを評価単位に分割。"""

import json
from app.gateway import call_llm
from app.judge.models import Segment


async def segment(text: str) -> list[Segment]:
    """テキストを事実主張・数値・固有名詞・論理の単位に分割。"""
    prompt = f"""以下のテキストを評価可能な単位（セグメント）に分割してください。
各セグメントは以下のいずれかのカテゴリに分類してください:
- claim: 事実に関する主張
- number: 数値データ
- name: 固有名詞・人名・組織名
- logic: 論理的推論・因果関係

JSON 配列で返してください。各要素は {{"id": "seg_1", "text": "...", "category": "..."}} の形式です。
JSON のみを返し、他のテキストは含めないでください。

テキスト:
{text}"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="fast",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    segments_data = json.loads(content.strip())
    return [Segment(**s) for s in segments_data]
