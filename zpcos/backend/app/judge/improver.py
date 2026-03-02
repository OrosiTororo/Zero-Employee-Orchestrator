"""Improver — 低スコアセグメントの自動改善。"""

from app.gateway import call_llm
from app.judge.models import EvalResult


async def improve(original: str, eval_results: list[EvalResult]) -> str:
    """score < 0.67 のセグメントのみ修正した改善版を生成。"""
    low_score_issues = []
    for er in eval_results:
        if er.score < 0.67:
            low_score_issues.append({
                "segment_id": er.segment_id,
                "issues": er.issues,
            })

    if not low_score_issues:
        return original

    issues_text = "\n".join(
        f"- セグメント {i['segment_id']}: {', '.join(i['issues'])}"
        for i in low_score_issues
    )

    prompt = f"""以下のテキストに問題が見つかりました。指摘された問題のみを修正してください。
修正していない部分はそのまま保持してください。

元のテキスト:
{original}

指摘された問題:
{issues_text}

修正後のテキストのみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    return response.choices[0].message.content
