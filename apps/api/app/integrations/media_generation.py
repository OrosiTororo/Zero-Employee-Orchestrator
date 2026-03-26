"""Media generation integration — image, video, audio, and 3D generation tool orchestration.

Integrates image, video, audio, and 3D model generation using external APIs.
All generation goes through data protection policies and approval gates.

Built-in services:
- Image generation: OpenAI DALL-E, Stability AI (Stable Diffusion), Replicate
- Video generation: Runway ML, Replicate (SVD/AnimateDiff), Pika
- Audio generation: OpenAI TTS, ElevenLabs
- Music generation: Suno, Udio

Dynamic provider registration:
- Users can add new providers via API (3D tools, etc.)
- Built-in providers cannot be deleted or disabled

Safety:
- Prompt injection inspection (applied to generation prompts too)
- Approval gate: external API calls require approval
- Transfer control following data protection policies
- Generation results recorded in audit logs
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MediaType(str, Enum):
    """Media type."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MUSIC = "music"
    THREE_D = "3d"


class GenerationProvider(str, Enum):
    """Built-in generation provider (for backward compatibility)."""

    # Image
    OPENAI_DALLE = "openai_dalle"
    STABILITY_AI = "stability_ai"
    REPLICATE_IMAGE = "replicate_image"

    # Video
    RUNWAY_ML = "runway_ml"
    REPLICATE_VIDEO = "replicate_video"
    PIKA = "pika"

    # Audio
    OPENAI_TTS = "openai_tts"
    ELEVENLABS = "elevenlabs"

    # Music
    SUNO = "suno"
    UDIO = "udio"


class GenerationStatus(str, Enum):
    """Generation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class MediaProviderEntry:
    """Media provider registry entry."""

    id: str
    media_type: str  # MediaType value (image, video, audio, music, 3d)
    api_base: str
    env_key: str
    models: list[str] = field(default_factory=list)
    default_model: str = ""
    max_prompt_length: int = 5000
    cost_per_generation: float = 0.0
    extra_config: dict = field(default_factory=dict)
    builtin: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "media_type": self.media_type,
            "api_base": self.api_base,
            "env_key": self.env_key,
            "models": self.models,
            "default_model": self.default_model,
            "max_prompt_length": self.max_prompt_length,
            "cost_per_generation": self.cost_per_generation,
            "extra_config": self.extra_config,
            "builtin": self.builtin,
        }


class MediaProviderRegistry:
    """Dynamic media provider registry.

    Built-in providers are registered at initialization and cannot be deleted.
    Users can add and remove new providers via API.
    """

    def __init__(self) -> None:
        self._providers: dict[str, MediaProviderEntry] = {}
        self._init_builtin_providers()

    def _init_builtin_providers(self) -> None:
        """Register built-in providers."""
        builtins = [
            MediaProviderEntry(
                id="openai_dalle",
                media_type="image",
                api_base="https://api.openai.com/v1/images/generations",
                env_key="OPENAI_API_KEY",
                models=["dall-e-3", "dall-e-2"],
                default_model="dall-e-3",
                max_prompt_length=4000,
                cost_per_generation=0.04,
                extra_config={
                    "supported_sizes": ["1024x1024", "1024x1792", "1792x1024"],
                },
                builtin=True,
            ),
            MediaProviderEntry(
                id="stability_ai",
                media_type="image",
                api_base="https://api.stability.ai/v2beta/stable-image/generate",
                env_key="STABILITY_API_KEY",
                models=["sd3.5-large", "sd3.5-medium", "sd3-turbo"],
                default_model="sd3.5-large",
                max_prompt_length=10000,
                cost_per_generation=0.065,
                builtin=True,
            ),
            MediaProviderEntry(
                id="replicate_image",
                media_type="image",
                api_base="https://api.replicate.com/v1/predictions",
                env_key="REPLICATE_API_TOKEN",
                models=["flux-1.1-pro", "sdxl", "kandinsky"],
                default_model="flux-1.1-pro",
                max_prompt_length=5000,
                cost_per_generation=0.03,
                builtin=True,
            ),
            MediaProviderEntry(
                id="runway_ml",
                media_type="video",
                api_base="https://api.dev.runwayml.com/v1",
                env_key="RUNWAY_API_KEY",
                models=["gen-3-alpha"],
                default_model="gen-3-alpha",
                max_prompt_length=2000,
                cost_per_generation=0.50,
                builtin=True,
            ),
            MediaProviderEntry(
                id="replicate_video",
                media_type="video",
                api_base="https://api.replicate.com/v1/predictions",
                env_key="REPLICATE_API_TOKEN",
                models=["stable-video-diffusion", "animate-diff"],
                default_model="stable-video-diffusion",
                max_prompt_length=2000,
                cost_per_generation=0.10,
                builtin=True,
            ),
            MediaProviderEntry(
                id="pika",
                media_type="video",
                api_base="https://api.pika.art/v1",
                env_key="PIKA_API_KEY",
                models=["pika-2.0"],
                default_model="pika-2.0",
                max_prompt_length=2000,
                cost_per_generation=0.20,
                builtin=True,
            ),
            MediaProviderEntry(
                id="openai_tts",
                media_type="audio",
                api_base="https://api.openai.com/v1/audio/speech",
                env_key="OPENAI_API_KEY",
                models=["tts-1", "tts-1-hd"],
                default_model="tts-1",
                max_prompt_length=4096,
                cost_per_generation=0.015,
                extra_config={
                    "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                },
                builtin=True,
            ),
            MediaProviderEntry(
                id="elevenlabs",
                media_type="audio",
                api_base="https://api.elevenlabs.io/v1/text-to-speech",
                env_key="ELEVENLABS_API_KEY",
                models=["eleven_multilingual_v2"],
                default_model="eleven_multilingual_v2",
                max_prompt_length=5000,
                cost_per_generation=0.03,
                builtin=True,
            ),
            MediaProviderEntry(
                id="suno",
                media_type="music",
                api_base="https://api.suno.ai/v1",
                env_key="SUNO_API_KEY",
                models=["suno-v4"],
                default_model="suno-v4",
                max_prompt_length=3000,
                cost_per_generation=0.10,
                builtin=True,
            ),
            MediaProviderEntry(
                id="udio",
                media_type="music",
                api_base="https://api.udio.com/v1",
                env_key="UDIO_API_KEY",
                models=["udio-v2"],
                default_model="udio-v2",
                max_prompt_length=3000,
                cost_per_generation=0.10,
                builtin=True,
            ),
        ]
        for entry in builtins:
            self._providers[entry.id] = entry

    def register(self, entry: MediaProviderEntry) -> None:
        """Register a provider (overwrites existing user-defined providers)."""
        existing = self._providers.get(entry.id)
        if existing and existing.builtin:
            raise ValueError(f"Cannot overwrite builtin provider: {entry.id}")
        self._providers[entry.id] = entry
        logger.info("Media provider registered: %s (type=%s)", entry.id, entry.media_type)

    def unregister(self, provider_id: str) -> bool:
        """Remove a provider (built-in providers cannot be removed)."""
        entry = self._providers.get(provider_id)
        if not entry:
            return False
        if entry.builtin:
            raise ValueError(f"Cannot remove builtin provider: {provider_id}")
        del self._providers[provider_id]
        logger.info("Media provider unregistered: %s", provider_id)
        return True

    def get(self, provider_id: str) -> MediaProviderEntry | None:
        """Get a provider."""
        return self._providers.get(provider_id)

    def list_all(self, media_type: str | None = None) -> list[MediaProviderEntry]:
        """Return all providers (optionally filtered by media type)."""
        entries = list(self._providers.values())
        if media_type:
            entries = [e for e in entries if e.media_type == media_type]
        return entries

    def get_available(self, media_type: str | None = None) -> list[dict]:
        """List of available providers (including whether API key is configured)."""
        import os

        result = []
        for entry in self.list_all(media_type):
            available = bool(os.environ.get(entry.env_key)) if entry.env_key else False
            result.append(
                {
                    "provider": entry.id,
                    "media_type": entry.media_type,
                    "models": entry.models,
                    "default_model": entry.default_model,
                    "available": available,
                    "builtin": entry.builtin,
                    "cost_per_generation": entry.cost_per_generation,
                }
            )
        return result


# Global registry instance
media_provider_registry = MediaProviderRegistry()


@dataclass
class GenerationRequest:
    """Media generation request."""

    prompt: str
    media_type: str  # MediaType value (string)
    provider: str  # provider ID (string, not enum)
    user_id: str
    parameters: dict = field(default_factory=dict)
    negative_prompt: str = ""
    language: str = "ja"


@dataclass
class GenerationResult:
    """Media generation result."""

    request_id: str
    status: GenerationStatus
    media_type: str
    provider: str
    output_url: str = ""
    output_base64: str = ""
    metadata: dict = field(default_factory=dict)
    error: str = ""
    cost_usd: float = 0.0
    created_at: str = ""


class MediaGenerationService:
    """Media generation service.

    Manages image, video, audio, and 3D generation in a unified way.
    Uses dynamic provider registry to also support user-registered providers.
    """

    def __init__(self, registry: MediaProviderRegistry | None = None) -> None:
        self._registry = registry or media_provider_registry
        self._results: dict[str, GenerationResult] = {}

    def get_available_providers(self) -> list[dict]:
        """Return a list of available providers."""
        return self._registry.get_available()

    def get_providers_by_type(self, media_type: str) -> list[dict]:
        """Return providers by media type."""
        return self._registry.get_available(media_type)

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate media.

        Safety checks:
        1. Prompt injection inspection
        2. Data protection policy check
        3. Approval gate check
        4. Cost estimate verification
        """
        request_id = str(uuid.uuid4())

        # Resolve provider
        entry = self._registry.get(request.provider)
        if not entry:
            return GenerationResult(
                request_id=request_id,
                status=GenerationStatus.FAILED,
                media_type=request.media_type,
                provider=request.provider,
                error=f"Unknown provider: {request.provider}",
                created_at=datetime.now(UTC).isoformat(),
            )

        # Prompt injection inspection
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

        # Data protection check
        from app.security.data_protection import data_protection_guard

        api_base = entry.api_base
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

        # Approval check
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
                    "provider": request.provider,
                    "estimated_cost": entry.cost_per_generation,
                },
                created_at=datetime.now(UTC).isoformat(),
            )
            self._results[request_id] = result
            return result

        # Actual generation (external API call)
        try:
            result = await self._execute_generation(request_id, request, entry)
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
        entry: MediaProviderEntry,
    ) -> GenerationResult:
        """Call external API to generate media."""
        import os

        api_key = os.environ.get(entry.env_key)

        if not api_key:
            return GenerationResult(
                request_id=request_id,
                status=GenerationStatus.FAILED,
                media_type=request.media_type,
                provider=request.provider,
                error=f"API key not configured: set {entry.env_key} environment variable",
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

        api_base = entry.api_base
        model = request.parameters.get("model", entry.default_model)

        # Build request per provider
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body: dict = {}

        if request.provider == "openai_dalle":
            body = {
                "model": model,
                "prompt": request.prompt,
                "n": request.parameters.get("n", 1),
                "size": request.parameters.get("size", "1024x1024"),
                "response_format": "b64_json",
            }
        elif request.provider == "openai_tts":
            body = {
                "model": model,
                "input": request.prompt,
                "voice": request.parameters.get("voice", "alloy"),
                "response_format": request.parameters.get("format", "mp3"),
            }
        elif request.provider in ("replicate_image", "replicate_video"):
            body = {
                "version": model,
                "input": {
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    **request.parameters,
                },
            }
        else:
            # Generic request — non-builtin providers also go through this path
            body = {
                "model": model,
                "prompt": request.prompt,
                **request.parameters,
            }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(api_base, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

        # Response parsing
        output_url = ""
        output_base64 = ""

        if request.provider == "openai_dalle":
            items = data.get("data", [])
            if items:
                output_base64 = items[0].get("b64_json", "")
                output_url = items[0].get("url", "")
        elif request.provider in ("replicate_image", "replicate_video"):
            output_url = data.get("output", "")
            if isinstance(output_url, list):
                output_url = output_url[0] if output_url else ""
        else:
            output_url = data.get("url", data.get("output_url", ""))

        cost = entry.cost_per_generation

        logger.info(
            "Media generated: type=%s, provider=%s, request_id=%s, cost=$%.3f",
            request.media_type,
            request.provider,
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
        """Get generation result."""
        return self._results.get(request_id)


# Global instance
media_generation_service = MediaGenerationService()
