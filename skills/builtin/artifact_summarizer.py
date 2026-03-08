"""Artifact Summarizer Skill — タスク成果物の要約を生成する.

タスク実行結果 (Artifact) を受け取り、
人間が確認しやすい要約を生成する。
レビュー・承認フローの効率化を目的とする。
"""

from dataclasses import dataclass, field


@dataclass
class ArtifactSummary:
    """成果物要約."""

    artifact_id: str
    task_id: str
    title: str
    summary: str
    key_changes: list[str]
    metrics: dict[str, str | int | float] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def summarize_artifact(
    artifact_id: str,
    task_id: str,
    artifact_type: str,
    content: str,
    metadata: dict | None = None,
) -> ArtifactSummary:
    """成果物を要約する.

    実際の運用では LLM を使って内容を解析・要約するが、
    このスキルは基本的なメタデータ抽出と構造化を提供する。
    """
    meta = metadata or {}

    # Extract basic metrics
    metrics: dict[str, str | int | float] = {
        "content_length": len(content),
        "artifact_type": artifact_type,
    }

    if artifact_type == "code":
        lines = content.split("\n")
        metrics["line_count"] = len(lines)
        metrics["non_empty_lines"] = sum(1 for l in lines if l.strip())
    elif artifact_type == "document":
        words = content.split()
        metrics["word_count"] = len(words)

    # Generate summary skeleton
    title = meta.get("title", f"成果物 {artifact_id}")
    summary_text = content[:500] + "..." if len(content) > 500 else content

    key_changes = meta.get("changes", [])
    if not key_changes and content:
        # Extract first few lines as key points
        lines = [l.strip() for l in content.split("\n") if l.strip()][:5]
        key_changes = lines

    return ArtifactSummary(
        artifact_id=artifact_id,
        task_id=task_id,
        title=title,
        summary=summary_text,
        key_changes=key_changes,
        metrics=metrics,
    )


def summary_to_markdown(summary: ArtifactSummary) -> str:
    """成果物要約を Markdown 形式に変換する."""
    lines = [
        f"# 成果物要約: {summary.title}",
        "",
        f"**Artifact ID:** {summary.artifact_id}",
        f"**Task ID:** {summary.task_id}",
        "",
        "## 要約",
        summary.summary,
        "",
    ]

    if summary.key_changes:
        lines.append("## 主要な変更点")
        for change in summary.key_changes:
            lines.append(f"- {change}")
        lines.append("")

    if summary.metrics:
        lines.append("## メトリクス")
        for key, value in summary.metrics.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    if summary.risks:
        lines.append("## リスク")
        for risk in summary.risks:
            lines.append(f"- ⚠️ {risk}")
        lines.append("")

    if summary.recommendations:
        lines.append("## 推奨事項")
        for rec in summary.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    return "\n".join(lines)
