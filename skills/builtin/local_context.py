"""Local Context Skill — ローカルファイルの安全な読み込みと分析.

このスキルは以下を行う:
- 許可されたディレクトリ内のファイル読み込み
- テキスト・Markdown・CSV・JSON の解析
- ファイル要約の生成
- ローカル文脈情報の提供

安全制約:
- 許可されたディレクトリのみアクセス可能
- 機密ファイル（.env, credentials 等）は除外
- 読み取り専用（書き込み不可）
"""

import json
import os
from pathlib import Path

ALLOWED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".toml", ".py", ".ts", ".js"}
BLOCKED_PATTERNS = {".env", "credentials", "secret", ".key", ".pem", "token"}


def is_safe_path(path: str, allowed_dirs: list[str]) -> bool:
    """パスが許可されたディレクトリ内かチェック."""
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(os.path.abspath(d)) for d in allowed_dirs)


def is_safe_file(path: str) -> bool:
    """ファイル名が安全かチェック."""
    name = os.path.basename(path).lower()
    return not any(pattern in name for pattern in BLOCKED_PATTERNS)


def read_local_file(path: str, allowed_dirs: list[str]) -> dict:
    """ローカルファイルを安全に読み込む."""
    if not is_safe_path(path, allowed_dirs):
        return {"error": "Access denied: path not in allowed directories"}
    if not is_safe_file(path):
        return {"error": "Access denied: file matches blocked pattern"}
    if not os.path.exists(path):
        return {"error": "File not found"}

    ext = Path(path).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"error": f"File type {ext} not supported"}

    with open(path, encoding="utf-8") as f:
        content = f.read()

    result = {
        "path": path,
        "size": os.path.getsize(path),
        "extension": ext,
        "content": content[:50000],
    }

    if ext == ".json":
        try:
            result["parsed"] = json.loads(content)
        except json.JSONDecodeError:
            result["parse_error"] = "Invalid JSON"

    return result


def list_local_files(directory: str, allowed_dirs: list[str]) -> list[dict]:
    """許可されたディレクトリ内のファイル一覧."""
    if not is_safe_path(directory, allowed_dirs):
        return []

    files = []
    for entry in Path(directory).iterdir():
        if entry.is_file() and is_safe_file(str(entry)):
            files.append({
                "name": entry.name,
                "path": str(entry),
                "size": entry.stat().st_size,
                "extension": entry.suffix,
            })
    return files
