"""ローカルファイル分析 Skill。
ローカルに常駐するOSだからこそ可能な、機密データを含むファイルのセキュアな読み込み・分析。
クラウドAIにはできない「ローカルの文脈理解」を実現する。
"""

import os
import json
from pathlib import Path

from app.skills.framework import SkillBase
from app.gateway import call_llm


def _load_allowed_dirs() -> list[str]:
    """許可ディレクトリ一覧を読み込み。"""
    config_path = (
        Path(os.environ.get("APPDATA", Path.home() / ".config"))
        / "zpcos"
        / "allowed_dirs.json"
    )
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return []


def _is_path_allowed(target: str, allowed_dirs: list[str]) -> bool:
    """パスが許可ディレクトリ配下かチェック。"""
    target_path = Path(target).resolve()
    return any(
        str(target_path).startswith(str(Path(d).resolve()))
        for d in allowed_dirs
    )


def _read_file_content(file_path: Path) -> str | None:
    """ファイルを読み込み。テキスト系のみ対応。"""
    text_exts = {
        ".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".toml",
        ".py", ".js", ".ts", ".html", ".css", ".xml", ".log",
    }
    if file_path.suffix.lower() not in text_exts:
        return None
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")[:50000]
    except Exception:
        return None


class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        target_path = input_data.get("path", "")
        instruction = input_data.get("instruction", "内容を要約してください")
        file_types = input_data.get("file_types", [".txt", ".md", ".csv"])

        if not target_path:
            return {"error": "パスを指定してください。"}

        allowed_dirs = _load_allowed_dirs()
        if not allowed_dirs:
            return {
                "error": "許可ディレクトリが設定されていません。"
                "設定画面からアクセスを許可するディレクトリを追加してください。"
            }

        if not _is_path_allowed(target_path, allowed_dirs):
            return {
                "error": f"指定されたパスはアクセスが許可されていません: {target_path}\n"
                f"許可ディレクトリ: {allowed_dirs}"
            }

        target = Path(target_path)
        files_read = []

        if target.is_file():
            content = _read_file_content(target)
            if content:
                files_read.append({"path": str(target), "content": content, "size": len(content)})
        elif target.is_dir():
            for ext in file_types:
                for f in target.rglob(f"*{ext}"):
                    if len(files_read) >= 20:
                        break
                    content = _read_file_content(f)
                    if content:
                        files_read.append({
                            "path": str(f), "content": content[:10000], "size": len(content),
                        })

        if not files_read:
            return {"error": "読み込み可能なファイルが見つかりませんでした。"}

        file_summaries = "\n\n".join(
            f"--- {f['path']} ({f['size']}文字) ---\n{f['content'][:5000]}"
            for f in files_read
        )

        prompt = f"""以下のローカルファイルを分析してください。

指示: {instruction}

ファイル内容:
{file_summaries}

日本語で分析結果を返してください。"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_group="quality",
        )

        return {
            "files_read": [{"path": f["path"], "size": f["size"]} for f in files_read],
            "analysis": response.choices[0].message.content,
            "file_count": len(files_read),
        }
