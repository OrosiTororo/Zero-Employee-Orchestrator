"""Skill ROI Explainer — Skill作成の価値説明。"""

from pydantic import BaseModel


class ROIReport(BaseModel):
    skill_name: str
    alternatives: list[str]
    value: dict
    risks: list[str]


async def explain_roi(skill_name: str, description: str) -> ROIReport:
    """Skill 作成の ROI を説明。"""
    return ROIReport(
        skill_name=skill_name,
        alternatives=[f"手動で {description} を実行", "既存 Skill の組み合わせで代用"],
        value={
            "reuse_potential": "高（同類タスクで再利用可能）",
            "time_saved_minutes": 30,
            "accuracy_improvement": "Judge による品質保証付き",
        },
        risks=[
            "外部 API 依存がある場合、API 仕様変更の影響を受ける",
            "定期的なメンテナンスが必要な場合がある",
        ],
    )
