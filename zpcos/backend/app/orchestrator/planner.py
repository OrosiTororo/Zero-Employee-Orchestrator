"""Planner — 自然言語の指示からDAG（実行計画）を生成。"""

import json
from app.gateway import call_llm
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep


async def generate_plan(
    user_input: str,
    available_skills: list[str],
    quality_mode: str = "balanced",
) -> OrchestrationPlan:
    """ユーザー入力と利用可能Skillから実行計画を生成。"""
    prompt = f"""あなたはタスクプランナーです。ユーザーの指示を実行するための計画（DAG）を作成してください。

利用可能なSkill: {json.dumps(available_skills, ensure_ascii=False)}

ユーザーの指示: {user_input}

以下のJSON形式で返してください:
{{
  "intent": "ユーザーの意図の要約",
  "steps": [
    {{
      "step_id": "step_1",
      "skill_name": "skill名",
      "input_mapping": {{"key": "value"}},
      "depends_on": []
    }}
  ]
}}

JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]

    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError:
        data = {"intent": user_input, "steps": []}

    steps = [OrchestrationStep(**s) for s in data.get("steps", [])]
    return OrchestrationPlan(
        intent=data.get("intent", user_input),
        steps=steps,
        quality_mode=quality_mode,
    )
