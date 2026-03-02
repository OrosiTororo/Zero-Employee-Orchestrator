"""Token Store — ハイブリッド暗号化保存.
keyring → AES-256 鍵のみ
ファイル → %APPDATA%/zpcos/tokens/{service}.enc に AES-GCM 暗号化 JSON
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional

import keyring
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _tokens_dir() -> Path:
    """トークン保存ディレクトリ。"""
    base = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "zpcos" / "tokens"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _get_or_create_key(service: str) -> bytes:
    """keyring から暗号鍵を取得。無ければ生成して保存。"""
    key_name = f"zpcos-{service}-key"
    stored = keyring.get_password("zpcos", key_name)
    if stored:
        return bytes.fromhex(stored)
    key = os.urandom(32)
    keyring.set_password("zpcos", key_name, key.hex())
    return key


def _save_sync(service: str, token_data: dict) -> None:
    key = _get_or_create_key(service)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(token_data).encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    enc_path = _tokens_dir() / f"{service}.enc"
    enc_path.write_bytes(nonce + ciphertext)


def _load_sync(service: str) -> Optional[dict]:
    enc_path = _tokens_dir() / f"{service}.enc"
    if not enc_path.exists():
        return None
    key = _get_or_create_key(service)
    aesgcm = AESGCM(key)
    data = enc_path.read_bytes()
    nonce = data[:12]
    ciphertext = data[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode("utf-8"))


def _delete_sync(service: str) -> None:
    enc_path = _tokens_dir() / f"{service}.enc"
    if enc_path.exists():
        enc_path.unlink()
    key_name = f"zpcos-{service}-key"
    try:
        keyring.delete_password("zpcos", key_name)
    except keyring.errors.PasswordDeleteError:
        pass


async def save_token(service: str, token_data: dict) -> None:
    """トークンを暗号化して保存。"""
    await asyncio.to_thread(_save_sync, service, token_data)


async def load_token(service: str) -> Optional[dict]:
    """トークンを復号して読み込み。ファイルが無ければ None。"""
    return await asyncio.to_thread(_load_sync, service)


async def delete_token(service: str) -> None:
    """トークンファイルと暗号鍵を削除。"""
    await asyncio.to_thread(_delete_sync, service)


async def has_token(service: str) -> bool:
    """トークンが存在するか。"""
    enc_path = _tokens_dir() / f"{service}.enc"
    return enc_path.exists()


def list_connections() -> list[str]:
    """tokens/ ディレクトリを走査して接続済みサービス一覧を返す。"""
    tokens_dir = _tokens_dir()
    return [f.stem for f in tokens_dir.glob("*.enc")]
