"""Design Interview — 壁打ち・すり合わせで要件を深掘り + Spec Writer。"""

import json
import uuid
from pydantic import BaseModel
from app.gateway import call_llm


class InterviewQuestion(BaseModel):
    id: str
    question: str
    why: str = ""  # なぜこの質問をするのか
    options: list[str] = []  # 選択肢
    answer: str = ""


class InterviewSession(BaseModel):
    id: str
    user_input: str
    questions: list[InterviewQuestion] = []
    answers: dict = {}
    status: str = "active"  # active | finalized


class SpecDocument(BaseModel):
    requirements: list[str] = []
    constraints: list[str] = []
    priorities: list[str] = []
    acceptance_criteria: list[str] = []
    ai_assumptions: list[str] = []


# メモリ内ストレージ
_sessions: dict[str, InterviewSession] = {}


async def start_interview(user_input: str) -> InterviewSession:
    """インタビューを開始。質問リストを生成。"""
    session_id = str(uuid.uuid4())

    prompt = f"""ユーザーが以下の要望を持っています。要件を明確にするために重要な質問を5つ生成してください。

ユーザーの要望: {user_input}

以下のJSON形式で返してください:
[
  {{
    "id": "q1",
    "question": "質問文",
    "why": "なぜこの質問が重要か",
    "options": ["選択肢1", "選択肢2", "選択肢3"]
  }}
]
JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]

    try:
        questions_data = json.loads(content.strip())
    except json.JSONDecodeError:
        questions_data = [{"id": "q1", "question": "具体的にどのような成果を期待していますか？",
                           "why": "目標を明確にするため", "options": []}]

    questions = [InterviewQuestion(**q) for q in questions_data]
    session = InterviewSession(id=session_id, user_input=user_input, questions=questions)
    _sessions[session_id] = session
    return session


async def process_response(session_id: str, answers: dict) -> InterviewSession:
    """回答を処理。追加質問があれば生成。"""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    session.answers.update(answers)

    # 回答に基づいて追加質問を検討
    if len(session.answers) < len(session.questions):
        return session  # まだ未回答がある

    return session


async def finalize(session_id: str) -> SpecDocument:
    """インタビューを完了し、Spec を生成。"""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    qa_text = "\n".join(
        f"Q: {q.question}\nA: {session.answers.get(q.id, '未回答')}"
        for q in session.questions
    )

    prompt = f"""以下のインタビュー結果から仕様書を生成してください。

元の要望: {session.user_input}

Q&A:
{qa_text}

JSON形式で返してください:
{{
  "requirements": ["要件1", "要件2"],
  "constraints": ["制約1"],
  "priorities": ["優先事項1"],
  "acceptance_criteria": ["受入基準1"],
  "ai_assumptions": ["AIが推定した前提1"]
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
        spec_data = json.loads(content.strip())
    except json.JSONDecodeError:
        spec_data = {
            "requirements": [session.user_input],
            "constraints": [], "priorities": [],
            "acceptance_criteria": [], "ai_assumptions": [],
        }

    session.status = "finalized"
    return SpecDocument(**spec_data)
