"""メディア生成統合 — 画像・動画・音声の生成ツール連携.

外部 API を利用した画像生成、動画生成、音声生成を統合する。
すべての生成はデータ保護ポリシーと承認ゲートを経由する。

対応サービス:
- 画像生成: OpenAI DALL-E, Stability AI (Stable Diffusion), Replicate
- 動画生成: Runway ML, Replicate (SVD/AnimateDiff), Pika
- 音声生成: OpenAI TTS, ElevenLabs
- 音楽生成: Suno, Udio

安全性:
- プロンプトインジェクション検査（生成プロンプトにも適用）
- 承認ゲート: 外部 API 呼び出しは承認必須
- データ保護ポリシーに従った転送制御
- 生成結果の監査ログ記録
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MediaType(str, Enum):
    """メディアタイプ."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MUSIC = "music"


class GenerationProvider(str, Enum):
    """生成プロバイダー."""

    # 画像
    OPENAI_DALLE = "openai_dalle"
    STABILITY_AI = "stability_ai"
    REPLICATE_IMAGE = "replicate_image"

    # 動画
    RUNWAY_ML = "runway_ml"
    REPLICATE_VIDEO = "replicate_video"
    PIKA = "pika"

    # 音声
    OPENAI_TTS = "openai_tts"
    ELEVENLABS = "elevenlabs"

    # 音楽
    SUNO = "suno"
    UDIO = "udio"


class GenerationStatus(str, Enum):
    """生成ステータス."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class GenerationRequest:
    """メディア生成リクエスト."""

    prompt: str
    media_type: MediaType
    provider: GenerationProvider
    user_id: str
    parameters: dict = field(default_factory=dict)
    negative_prompt: str = ""
    language: str = "ja"


@dataclass
class GenerationResult:
    """メディア生成結果."""

    request_id: str
    status: GenerationStatus
    media_type: MediaType
    provider: GenerationProvider
    output_url: str = ""
    output_base64: str = ""
    metadata: dict = field(default_factory=dict)
    error: str = ""
    cost_usd: float = 0.0
    created_at: str = ""


# プロバイダー設定
_PROVIDER_CONFIG: dict[GenerationProvider, dict] = {
    GenerationProvider.OPENAI_DALLE: {
        "media_type": MediaType.IMAGE,
        "api_base": "https://api.openai.com/v1/images/generations",
        "env_key": "OPENAI_API_KEY",
        "models": ["dall-e-3", "dall-e-2"],
        "default_model": "dall-e-3",
        "max_prompt_length": 4000,
        "supported_sizes": ["1024x1024", "1024x1792", "1792x1024"],
        "cost_per_generation": 0.04,  # DALL-E 3 standard
    },
    GenerationProvider.STABILITY_AI: {
        "media_type": MediaType.IMAGE,
        "api_base": "https://api.stability.ai/v2beta/stable-image/generate",
        "env_key": "STABILITY_API_KEY",
        "models": ["sd3.5-large", "sd3.5-medium", "sd3-turbo"],
        "default_model": "sd3.5-large",
        "max_prompt_length": 10000,
        "cost_per_generation": 0.065,
    },
    GenerationProvider.REPLICATE_IMAGE: {
        "media_type": MediaType.IMAGE,
        "api_base": "https://api.replicate.com/v1/predictions",
        "env_key": "REPLICATE_API_TOKEN",
        "models": ["flux-1.1-pro", "sdxl", "kandinsky"],
        "default_model": "flux-1.1-pro",
        "max_prompt_length": 5000,
        "cost_per_generation": 0.03,
    },
    GenerationProvider.RUNWAY_ML: {
        "media_type": MediaType.VIDEO,
        "api_base": "https://api.dev.runwayml.com/v1",
        "env_key": "RUNWAY_API_KEY",
        "models": ["gen-3-alpha"],
        "default_model": "gen-3-alpha",
        "max_prompt_length": 2000,
        "cost_per_generation": 0.50,
    },
    GenerationProvider.REPLICATE_VIDEO: {
        "media_type": MediaType.VIDEO,
        "api_base": "https://api.replicate.com/v1/predictions",
        "env_key": "REPLICATE_API_TOKEN",
        "models": ["stable-video-diffusion", "animate-diff"],
        "default_model": "stable-video-diffusion",
        "max_prompt_length": 2000,
        "cost_per_generation": 0.10,
    },
    GenerationProvider.PIKA: {
        "media_type": MediaType.VIDEO,
        "api_base": "https://api.pika.art/v1",
        "env_key": "PIKA_API_KEY",
        "models": ["pika-2.0"],
        "default_model": "pika-2.0",
        "max_prompt_length": 2000,
        "cost_per_generation": 0.20,
    },
    GenerationProvider.OPENAI_TTS: {
        "media_type": MediaType.AUDIO,
        "api_base": "https://api.openai.com/v1/audio/speech",
        "env_key": "OPENAI_API_KEY",
        "models": ["tts-1", "tts-1-hd"],
        "default_model": "tts-1",
        "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        "max_prompt_length": 4096,
        "cost_per_generation": 0.015,
    },
    GenerationProvider.ELEVENLABS: {
        "media_type": MediaType.AUDIO,
        "api_base": "https://api.elevenlabs.io/v1/text-to-speech",
        "env_key": "ELEVENLABS_API_KEY",
        "models": ["eleven_multilingual_v2"],
        "default_model": "eleven_multilingual_v2",
        "max_prompt_length": 5000,
        "cost_per_generation": 0.03,
    },
    GenerationProvider.SUNO: {
        "media_type": MediaType.MUSIC,
        "api_base": "https://api.suno.ai/v1",
        "env_key": "SUNO_API_KEY",
        "models": ["suno-v4"],
        "default_model": "suno-v4",
        "max_prompt_length": 3000,
        "cost_per_generation": 0.10,
    },
    GenerationProvider.UDIO: {
        "media_type": MediaType.MUSIC,
        "api_base": "https://api.udio.com/v1",
        "env_key": "UDIO_API_KEY",
        "models": ["udio-v2"],
        "default_model": "udio-v2",
        "max_prompt_length": 3000,
        "cost_per_generation": 0.10,
    },
}


class MediaGenerationService:
    """メディア生成サービス.

    画像・動画・音声の生成を統合管理する。
    """

    def __init__(self) -> None:
        self._results: dict[str, GenerationResult] = {}

    def get_available_providers(self) -> list[dict]:
        """利用可能なプロバイダー一覧を返す."""
        import os

        providers = []
        for provider, config in _PROVIDER_CONFIG.items():
            env_key = config.get("env_key", "")
            available = bool(os.environ.get(env_key)) if env_key else False
            providers.append(
                {
                    "provider": provider.value,
                    "media_type": config["media_type"].value,
                    "models": config.get("models", []),
                    "default_model": config.get("default_model", ""),
                    "available": available,
                    "cost_per_generation": config.get("cost_per_generation", 0),
                }
            )
        return providers

    def get_providers_by_type(self, media_type: MediaType) -> list[dict]:
        """メディアタイプ別のプロバイダーを返す."""
        return [p for p in self.get_available_providers() if p["media_type"] == media_type.value]

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """メディアを生成する.

        安全性チェック:
        1. プロンプトインジェクション検査
        2. データ保護ポリシーチェック
        3. 承認ゲートチェック
        4. コスト見積もり確認
        """
        request_id = str(uuid.uuid4())

        # プロンプトインジェクション検査
        from app.security.prompt_guard import scan_prompt_injection

        guard_result = scan_prompt_injection(request.prompt)
        if not guard_result.is_safe:
            return GenerationResult(
                request_id=request_id,
                status=GenerationStatus.FAILED,
                media_type=request.media_type,
                provider=request.provider,
                error="Prompt blocked: potentially unsafe content detected",
                created_at=datetime.now(UTC).isoformat(),
            )

        # データ保護チェック
        from app.security.data_protection import data_protection_guard

        api_config = _PROVIDER_CONFIG.get(request.provider, {})
        api_base = api_config.get("api_base", "")
        if api_base:
            from urllib.parse import urlparse

            host = urlparse(api_base).hostname or ""
            transfer_check = data_protection_guard.check_external_api(host)
            if not transfer_check.allowed:
                return GenerationResult(
                    request_id=request_id,
                    status=GenerationStatus.FAILED,
                    media_type=request.media_type,
                    provider=request.provider,
                    error=f"Data protection: {transfer_check.reason}",
                    created_at=datetime.now(UTC).isoformat(),
                )

        # 承認チェック
        from app.policies.approval_gate import check_approval_required

        approval = check_approval_required("external_api_write")
        if approval.requires_approval:
            result = GenerationResult(
                request_id=request_id,
                status=GenerationStatus.AWAITING_APPROVAL,
                media_type=request.media_type,
                provider=request.provider,
                metadata={
                    "prompt": request.prompt,
                    "provider": request.provider.value,
                    "estimated_cost": api_config.get("cost_per_generation", 0),
                },
                created_at=datetime.now(UTC).isoformat(),
            )
            self._results[request_id] = result
            return result

        # 実際の生成（外部 API 呼び出し）
        try:
            result = await self._execute_generation(request_id, request)
            self._results[request_id] = result
            return result
        except Exception as exc:
            logger.error("Media generation failed: %s", exc)
            result = GenerationResult(
                request_id=request_id,
                status=GenerationStatus.FAILED,
                media_type=request.media_type,
                provider=request.provider,
                error=str(exc),
                created_at=datetime.now(UTC).isoformat(),
            )
            self._results[request_id] = result
            return result

    async def _execute_generation(
        self,
        request_id: str,
        request: GenerationRequest,
    ) -> GenerationResult:
        """外部 API を呼び出してメディアを生成する.

        各プロバイダーの API 仕様に合わせたリクエストを構築・実行する。
        実際の HTTP 呼び出しは httpx / aiohttp を使用。
        """
        import os

        config = _PROVIDER_CONFIG.get(request.provider, {})
        api_key = os.environ.get(config.get("env_key", ""))

        if not api_key:
            return GenerationResult(
                request_id=request_id,
                status=GenerationStatus.FAILED,
                media_type=request.media_type,
                provider=request.provider,
                error=f"API key not configured: set {config.get('env_key', 'UNKNOWN')} "
                f"environment variable",
                created_at=datetime.now(UTC).isoformat(),
            )

        try:
            import httpx
        except ImportError:
            return GenerationResult(
                request_id=request_id,
                status=GenerationStatus.FAILED,
                media_type=request.media_type,
                provider=request.provider,
                error="httpx is required for media generation. Install with: pip install httpx",
                created_at=datetime.now(UTC).isoformat(),
            )

        api_base = config["api_base"]
        model = request.parameters.get("model", config.get("default_model", ""))

        # プロバイダー別のリクエスト構築
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body: dict = {}

        if request.provider == GenerationProvider.OPENAI_DALLE:
            body = {
                "model": model,
                "prompt": request.prompt,
                "n": request.parameters.get("n", 1),
                "size": request.parameters.get("size", "1024x1024"),
                "response_format": "b64_json",
            }
        elif request.provider == GenerationProvider.OPENAI_TTS:
            body = {
                "model": model,
                "input": request.prompt,
                "voice": request.parameters.get("voice", "alloy"),
                "response_format": request.parameters.get("format", "mp3"),
            }
        elif request.provider in (
            GenerationProvider.REPLICATE_IMAGE,
            GenerationProvider.REPLICATE_VIDEO,
        ):
            body = {
                "version": model,
                "input": {
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    **request.parameters,
                },
            }
        else:
            # Generic request
            body = {
                "model": model,
                "prompt": request.prompt,
                **request.parameters,
            }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(api_base, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

        # レスポンス解析
        output_url = ""
        output_base64 = ""

        if request.provider == GenerationProvider.OPENAI_DALLE:
            items = data.get("data", [])
            if items:
                output_base64 = items[0].get("b64_json", "")
                output_url = items[0].get("url", "")
        elif request.provider in (
            GenerationProvider.REPLICATE_IMAGE,
            GenerationProvider.REPLICATE_VIDEO,
        ):
            output_url = data.get("output", "")
            if isinstance(output_url, list):
                output_url = output_url[0] if output_url else ""
        else:
            output_url = data.get("url", data.get("output_url", ""))

        cost = config.get("cost_per_generation", 0)

        logger.info(
            "Media generated: type=%s, provider=%s, request_id=%s, cost=$%.3f",
            request.media_type.value,
            request.provider.value,
            request_id,
            cost,
        )

        return GenerationResult(
            request_id=request_id,
            status=GenerationStatus.COMPLETED,
            media_type=request.media_type,
            provider=request.provider,
            output_url=output_url,
            output_base64=output_base64,
            cost_usd=cost,
            metadata={"model": model},
            created_at=datetime.now(UTC).isoformat(),
        )

    def get_result(self, request_id: str) -> GenerationResult | None:
        """生成結果を取得する."""
        return self._results.get(request_id)


# グローバルインスタンス
media_generation_service = MediaGenerationService()
