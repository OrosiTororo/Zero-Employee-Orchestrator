"""ファイルアップロード API エンドポイント.

ファイルのアップロード、ダウンロード、削除、一覧取得を提供する。
ファイルサイズ制限（最大50MB）、許可拡張子チェック、
一時ディレクトリへの保存を行う。
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
UPLOAD_DIR: Path = Path(os.environ.get("UPLOAD_DIR", "/tmp/zeo_uploads"))

ALLOWED_EXTENSIONS: set[str] = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".htm",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".odt",
    ".ods",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".bmp",
    ".zip",
    ".tar",
    ".gz",
    ".py",
    ".js",
    ".ts",
    ".sh",
    ".sql",
    ".log",
    ".ini",
    ".toml",
    ".cfg",
}


# ---------------------------------------------------------------------------
# インメモリファイル管理
# ---------------------------------------------------------------------------
@dataclass
class StoredFile:
    """保存されたファイルのメタデータ."""

    id: str
    original_name: str
    stored_path: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


_file_store: dict[str, StoredFile] = {}


# ---------------------------------------------------------------------------
# Pydantic スキーマ
# ---------------------------------------------------------------------------
class FileInfoResponse(BaseModel):
    """ファイル情報レスポンス."""

    id: str
    original_name: str
    content_type: str
    size_bytes: int
    uploaded_at: str


class FileListResponse(BaseModel):
    """ファイル一覧レスポンス."""

    files: list[FileInfoResponse]
    total: int


class UploadResponse(BaseModel):
    """アップロードレスポンス."""

    id: str
    original_name: str
    size_bytes: int
    message: str


class MultiUploadResponse(BaseModel):
    """複数ファイルアップロードレスポンス."""

    uploaded: list[UploadResponse]
    failed: list[dict[str, str]]


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def _validate_extension(filename: str) -> None:
    """ファイル拡張子が許可リストに含まれるかチェックする."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"許可されていないファイル形式です: {ext}",
        )


def _to_info_response(f: StoredFile) -> FileInfoResponse:
    """StoredFile を FileInfoResponse に変換する."""
    return FileInfoResponse(
        id=f.id,
        original_name=f.original_name,
        content_type=f.content_type,
        size_bytes=f.size_bytes,
        uploaded_at=f.uploaded_at.isoformat(),
    )


async def _save_upload(upload: UploadFile) -> StoredFile:
    """UploadFile をディスクに保存し、StoredFile を返す.

    データ保護ポリシーのチェックとパスワードパターン検出を適用する。
    """
    filename = upload.filename or "unnamed"
    _validate_extension(filename)

    # データ保護ポリシーチェック
    try:
        from app.security.data_protection import data_protection_guard

        upload_check = data_protection_guard.check_upload(filename, "user")
        if not upload_check.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"データ保護ポリシーによりアップロードが拒否されました: {upload_check.reason}",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.debug("Data protection check skipped: %s", exc)

    # ファイルサイズチェック（チャンク読み込み）
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    ext = Path(filename).suffix.lower()
    stored_path = UPLOAD_DIR / f"{file_id}{ext}"

    total_size = 0
    chunk_size = 1024 * 1024  # 1MB

    try:
        with open(stored_path, "wb") as f:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    # 途中まで書いたファイルを削除
                    f.close()
                    stored_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"ファイルサイズが上限を超えています "
                            f"(最大 {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB)"
                        ),
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"ファイル保存中にエラーが発生しました: {exc}",
        ) from exc

    stored = StoredFile(
        id=file_id,
        original_name=filename,
        stored_path=str(stored_path),
        content_type=upload.content_type or "application/octet-stream",
        size_bytes=total_size,
    )
    _file_store[file_id] = stored
    logger.info(
        "ファイルアップロード: id=%s, name=%s, size=%d",
        file_id,
        filename,
        total_size,
    )
    return stored


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile, user: User = Depends(get_current_user)) -> UploadResponse:
    """単一ファイルをアップロードする.

    最大50MBまで。許可された拡張子のみ受け付ける。
    """
    stored = await _save_upload(file)
    return UploadResponse(
        id=stored.id,
        original_name=stored.original_name,
        size_bytes=stored.size_bytes,
        message="アップロード完了",
    )


@router.post("/upload-multiple", response_model=MultiUploadResponse)
async def upload_multiple_files(
    files: list[UploadFile],
    user: User = Depends(get_current_user),
) -> MultiUploadResponse:
    """複数ファイルを一括アップロードする.

    各ファイルに対して個別にバリデーションを行い、
    成功・失敗を分けて結果を返す。
    """
    uploaded: list[UploadResponse] = []
    failed: list[dict[str, str]] = []

    for file in files:
        try:
            stored = await _save_upload(file)
            uploaded.append(
                UploadResponse(
                    id=stored.id,
                    original_name=stored.original_name,
                    size_bytes=stored.size_bytes,
                    message="アップロード完了",
                )
            )
        except HTTPException as exc:
            failed.append(
                {
                    "filename": file.filename or "unnamed",
                    "error": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                }
            )

    return MultiUploadResponse(uploaded=uploaded, failed=failed)


@router.get("/{file_id}", response_model=FileInfoResponse)
async def get_file_info(file_id: str, user: User = Depends(get_current_user)) -> FileInfoResponse:
    """ファイル情報を取得する."""
    stored = _file_store.get(file_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    return _to_info_response(stored)


@router.get("/{file_id}/download")
async def download_file(file_id: str, user: User = Depends(get_current_user)) -> FileResponse:
    """ファイルをダウンロードする."""
    stored = _file_store.get(file_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    path = Path(stored.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="ファイルがストレージ上に見つかりません")

    # サンドボックスチェック — ファイルパスが許可範囲内か
    try:
        from app.security.sandbox import AccessType, filesystem_sandbox

        access = filesystem_sandbox.check_access(str(path), AccessType.READ)
        if not access.allowed:
            logger.warning(
                "Sandbox blocked file download: path=%s reason=%s",
                path,
                access.reason,
            )
            raise HTTPException(
                status_code=403,
                detail=f"サンドボックスポリシーによりアクセスが拒否されました: {access.reason}",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.debug("Sandbox check skipped: %s", exc)

    return FileResponse(
        path=str(path),
        filename=stored.original_name,
        media_type=stored.content_type,
    )


@router.delete("/{file_id}")
async def delete_file(file_id: str, user: User = Depends(get_current_user)) -> dict[str, str]:
    """ファイルを削除する."""
    stored = _file_store.get(file_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    # ディスクから削除
    path = Path(stored.stored_path)
    path.unlink(missing_ok=True)

    del _file_store[file_id]
    logger.info("ファイル削除: id=%s, name=%s", file_id, stored.original_name)
    return {"message": f"ファイル '{stored.original_name}' を削除しました"}


@router.get("", response_model=FileListResponse)
async def list_files(
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(get_current_user),
) -> FileListResponse:
    """アップロード済みファイル一覧を取得する."""
    all_files = sorted(
        _file_store.values(),
        key=lambda f: f.uploaded_at,
        reverse=True,
    )
    total = len(all_files)
    page = all_files[offset : offset + limit]
    return FileListResponse(
        files=[_to_info_response(f) for f in page],
        total=total,
    )
