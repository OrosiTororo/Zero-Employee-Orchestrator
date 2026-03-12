"""Local Context Skill — ローカルファイルの安全な読み込みと分析.

このスキルは以下を行う:
- 許可されたディレクトリ内のファイル読み込み
- テキスト・Markdown・CSV・JSON・YAML の解析
- 画像ファイルの読み込み（Base64 エンコード + メタデータ抽出）
- ファイル要約の生成
- ローカル文脈情報の提供

安全制約:
- 許可されたディレクトリのみアクセス可能
- 機密ファイル（.env, credentials 等）は除外
- 読み取り専用（書き込み不可）
- 画像ファイルは 10 MB 以下に制限
"""

import base64
import json
import os
from pathlib import Path

# テキスト系ファイル
ALLOWED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".toml",
    ".py", ".ts", ".js", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".c", ".cpp", ".h",
    ".html", ".xml", ".css", ".sql", ".sh",
}

# 画像ファイル
ALLOWED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
}

# ドキュメントファイル
ALLOWED_DOC_EXTENSIONS = {
    ".pdf",
}

ALLOWED_EXTENSIONS = ALLOWED_TEXT_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOC_EXTENSIONS

BLOCKED_PATTERNS = {".env", "credentials", "secret", ".key", ".pem", "token"}

# 画像ファイルの最大サイズ (10 MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# MIME タイプマッピング
_MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
}


def is_safe_path(path: str, allowed_dirs: list[str]) -> bool:
    """パスが許可されたディレクトリ内かチェック."""
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(os.path.abspath(d)) for d in allowed_dirs)


def is_safe_file(path: str) -> bool:
    """ファイル名が安全かチェック."""
    name = os.path.basename(path).lower()
    return not any(pattern in name for pattern in BLOCKED_PATTERNS)


def read_local_file(path: str, allowed_dirs: list[str]) -> dict:
    """ローカルファイルを安全に読み込む.

    テキストファイルと画像ファイルの両方に対応。
    画像ファイルは Base64 エンコードしてメタデータとともに返す。
    """
    if not is_safe_path(path, allowed_dirs):
        return {"error": "Access denied: path not in allowed directories"}
    if not is_safe_file(path):
        return {"error": "Access denied: file matches blocked pattern"}
    if not os.path.exists(path):
        return {"error": "File not found"}

    ext = Path(path).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"error": f"File type {ext} not supported"}

    file_size = os.path.getsize(path)

    # 画像ファイルの処理
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return _read_image_file(path, ext, file_size)

    # ドキュメントファイルの処理
    if ext in ALLOWED_DOC_EXTENSIONS:
        return _read_document_file(path, ext, file_size)

    # テキストファイルの処理
    return _read_text_file(path, ext, file_size)


def _read_text_file(path: str, ext: str, file_size: int) -> dict:
    """テキストファイルを読み込む."""
    # 複数エンコーディングを試行
    content = None
    used_encoding = "utf-8"
    for encoding in ("utf-8", "shift_jis", "euc-jp", "cp932", "latin-1"):
        try:
            with open(path, encoding=encoding) as f:
                content = f.read()
            used_encoding = encoding
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if content is None:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()

    result: dict = {
        "path": path,
        "size": file_size,
        "extension": ext,
        "type": "text",
        "encoding": used_encoding,
        "content": content[:50000],
    }

    if ext == ".json":
        try:
            result["parsed"] = json.loads(content)
        except json.JSONDecodeError:
            result["parse_error"] = "Invalid JSON"

    if ext in (".yaml", ".yml"):
        result["format"] = "yaml"

    if ext == ".csv":
        lines = content.split("\n")
        result["line_count"] = len(lines)
        if lines:
            result["header"] = lines[0]

    return result


def _read_image_file(path: str, ext: str, file_size: int) -> dict:
    """画像ファイルを読み込み、Base64 エンコードして返す."""
    if file_size > MAX_IMAGE_SIZE:
        return {
            "error": f"Image file too large ({file_size / (1024*1024):.1f} MB > {MAX_IMAGE_SIZE / (1024*1024)} MB)",
            "path": path,
            "size": file_size,
        }

    with open(path, "rb") as f:
        raw = f.read()

    mime_type = _MIME_MAP.get(ext, "application/octet-stream")

    # SVG はテキストとしても返す
    if ext == ".svg":
        try:
            svg_text = raw.decode("utf-8")
            return {
                "path": path,
                "size": file_size,
                "extension": ext,
                "type": "image",
                "mime_type": mime_type,
                "content": svg_text[:50000],
                "base64": base64.b64encode(raw).decode("ascii"),
                "data_uri": f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}",
            }
        except UnicodeDecodeError:
            pass

    b64 = base64.b64encode(raw).decode("ascii")
    return {
        "path": path,
        "size": file_size,
        "extension": ext,
        "type": "image",
        "mime_type": mime_type,
        "base64": b64,
        "data_uri": f"data:{mime_type};base64,{b64}",
        "dimensions": _get_image_dimensions(raw, ext),
    }


def _get_image_dimensions(raw: bytes, ext: str) -> dict | None:
    """画像のサイズ (width x height) を取得する (PNG/JPEG のみ)."""
    try:
        if ext == ".png" and len(raw) >= 24:
            # PNG IHDR chunk
            if raw[:8] == b"\x89PNG\r\n\x1a\n":
                width = int.from_bytes(raw[16:20], "big")
                height = int.from_bytes(raw[20:24], "big")
                return {"width": width, "height": height}

        if ext in (".jpg", ".jpeg") and len(raw) >= 2:
            # JPEG SOF marker search
            i = 2
            while i < len(raw) - 8:
                if raw[i] == 0xFF:
                    marker = raw[i + 1]
                    if marker in (0xC0, 0xC1, 0xC2):
                        height = int.from_bytes(raw[i + 5 : i + 7], "big")
                        width = int.from_bytes(raw[i + 7 : i + 9], "big")
                        return {"width": width, "height": height}
                    seg_len = int.from_bytes(raw[i + 2 : i + 4], "big")
                    i += 2 + seg_len
                else:
                    i += 1
    except Exception:
        pass
    return None


def _read_document_file(path: str, ext: str, file_size: int) -> dict:
    """ドキュメントファイル (PDF 等) のメタ情報を返す."""
    return {
        "path": path,
        "size": file_size,
        "extension": ext,
        "type": "document",
        "mime_type": _MIME_MAP.get(ext, "application/octet-stream"),
        "content": f"[PDF document: {os.path.basename(path)}, {file_size / 1024:.1f} KB]",
    }


def list_local_files(directory: str, allowed_dirs: list[str]) -> list[dict]:
    """許可されたディレクトリ内のファイル一覧."""
    if not is_safe_path(directory, allowed_dirs):
        return []

    files = []
    for entry in Path(directory).iterdir():
        if entry.is_file() and is_safe_file(str(entry)):
            ext = entry.suffix.lower()
            file_type = "text"
            if ext in ALLOWED_IMAGE_EXTENSIONS:
                file_type = "image"
            elif ext in ALLOWED_DOC_EXTENSIONS:
                file_type = "document"

            files.append({
                "name": entry.name,
                "path": str(entry),
                "size": entry.stat().st_size,
                "extension": ext,
                "type": file_type,
                "supported": ext in ALLOWED_EXTENSIONS,
            })
    return files
