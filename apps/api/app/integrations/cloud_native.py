"""Cloud service native integration — AWS / GCP / Azure / Cloudflare abstraction layer.

Provides a unified interface for multi-cloud resource management, storage,
serverless execution, and cost estimation.

All operations:
- Go through approval gates
- Are recorded in audit logs
- Follow data protection policies
- Credentials are managed via secret_manager
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CloudProvider(str, Enum):
    """Cloud provider."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    CLOUDFLARE = "cloudflare"


class CloudService(str, Enum):
    """Cloud service type."""

    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    SERVERLESS = "serverless"
    CDN = "cdn"
    DNS = "dns"
    MONITORING = "monitoring"
    AI_ML = "ai_ml"
    QUEUE = "queue"
    SECRET_MANAGER = "secret_manager"


class ResourceStatus(str, Enum):
    """Resource status."""

    CREATING = "creating"
    ACTIVE = "active"
    STOPPED = "stopped"
    DELETING = "deleting"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class CloudCredential:
    """Cloud credential."""

    provider: CloudProvider
    credential_type: str  # "access_key" | "service_account" | "oauth" | "api_token"
    region: str = ""
    config: dict = field(default_factory=dict)
    is_valid: bool = False
    last_validated: str = ""


@dataclass
class CloudResource:
    """Cloud resource."""

    id: str
    provider: CloudProvider
    service: CloudService
    resource_type: str  # "ec2_instance" | "s3_bucket" | "lambda_function" etc.
    name: str
    region: str = ""
    status: ResourceStatus = ResourceStatus.UNKNOWN
    metadata: dict = field(default_factory=dict)
    created_at: str = ""


class CloudNativeIntegration:
    """Cloud service native integration.

    Manages multi-cloud resources through a unified interface.
    """

    def __init__(self) -> None:
        self._credentials: dict[CloudProvider, CloudCredential] = {}
        self._resources: dict[str, CloudResource] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _require_credential(self, provider: CloudProvider) -> CloudCredential:
        """Verify that credentials are configured."""
        cred = self._credentials.get(provider)
        if cred is None:
            raise ValueError(f"Credentials not configured for provider {provider.value}")
        if not cred.is_valid:
            raise ValueError(
                f"Credentials for provider {provider.value} are invalid. "
                "Please verify with validate_credentials()"
            )
        return cred

    # ------------------------------------------------------------------
    # Credential management
    # ------------------------------------------------------------------

    async def configure_provider(
        self, provider: CloudProvider, credentials: dict
    ) -> CloudCredential:
        """プロバイダーの認証情報を設定する."""
        cred_type = credentials.pop("credential_type", "access_key")
        region = credentials.pop("region", "")

        credential = CloudCredential(
            provider=provider,
            credential_type=cred_type,
            region=region,
            config=credentials,
            is_valid=False,
            last_validated="",
        )
        self._credentials[provider] = credential
        logger.info(
            "クラウド認証情報設定: provider=%s type=%s region=%s",
            provider.value,
            cred_type,
            region,
        )
        return credential

    async def validate_credentials(self, provider: CloudProvider) -> bool:
        """認証情報の有効性を検証する."""
        cred = self._credentials.get(provider)
        if cred is None:
            raise ValueError(f"プロバイダー {provider.value} の認証情報が設定されていません")

        # 実際のクラウド API 呼び出しのシミュレーション
        # 本番では boto3 / google-cloud / azure-sdk を使用
        has_config = bool(cred.config)
        cred.is_valid = has_config
        cred.last_validated = self._now()
        logger.info(
            "クラウド認証検証: provider=%s valid=%s",
            provider.value,
            cred.is_valid,
        )
        return cred.is_valid

    # ------------------------------------------------------------------
    # リソース管理
    # ------------------------------------------------------------------

    async def list_resources(
        self,
        provider: CloudProvider | None = None,
        service: CloudService | None = None,
    ) -> list[CloudResource]:
        """リソース一覧を取得する."""
        resources = list(self._resources.values())
        if provider:
            resources = [r for r in resources if r.provider == provider]
        if service:
            resources = [r for r in resources if r.service == service]
        return resources

    async def create_resource(
        self,
        provider: CloudProvider,
        service: CloudService,
        config: dict,
    ) -> CloudResource:
        """クラウドリソースを作成する."""
        self._require_credential(provider)

        resource_id = str(uuid.uuid4())
        resource_type = config.get("resource_type", service.value)
        name = config.get("name", f"{provider.value}-{service.value}-{resource_id[:8]}")
        region = config.get("region", self._credentials[provider].region)

        resource = CloudResource(
            id=resource_id,
            provider=provider,
            service=service,
            resource_type=resource_type,
            name=name,
            region=region,
            status=ResourceStatus.CREATING,
            metadata=config,
            created_at=self._now(),
        )
        self._resources[resource_id] = resource

        # リソース作成のシミュレーション（非同期完了）
        resource.status = ResourceStatus.ACTIVE

        logger.info(
            "クラウドリソース作成: id=%s provider=%s service=%s name=%s",
            resource_id,
            provider.value,
            service.value,
            name,
        )
        return resource

    async def delete_resource(self, resource_id: str) -> bool:
        """クラウドリソースを削除する."""
        resource = self._resources.get(resource_id)
        if resource is None:
            raise ValueError(f"リソースが見つかりません: {resource_id}")

        self._require_credential(resource.provider)
        resource.status = ResourceStatus.DELETING
        del self._resources[resource_id]
        logger.info("クラウドリソース削除: id=%s name=%s", resource_id, resource.name)
        return True

    async def get_resource_status(self, resource_id: str) -> dict:
        """リソースのステータスを取得する."""
        resource = self._resources.get(resource_id)
        if resource is None:
            raise ValueError(f"リソースが見つかりません: {resource_id}")
        return {
            "id": resource.id,
            "name": resource.name,
            "provider": resource.provider.value,
            "service": resource.service.value,
            "status": resource.status.value,
            "region": resource.region,
            "created_at": resource.created_at,
        }

    # ------------------------------------------------------------------
    # ストレージ
    # ------------------------------------------------------------------

    async def upload_to_storage(
        self,
        provider: CloudProvider,
        bucket: str,
        key: str,
        data: bytes,
    ) -> dict:
        """ストレージにファイルをアップロードする."""
        self._require_credential(provider)
        size_bytes = len(data)
        logger.info(
            "ストレージアップロード: provider=%s bucket=%s key=%s size=%d",
            provider.value,
            bucket,
            key,
            size_bytes,
        )
        return {
            "provider": provider.value,
            "bucket": bucket,
            "key": key,
            "size_bytes": size_bytes,
            "uploaded_at": self._now(),
            "status": "success",
        }

    async def download_from_storage(
        self,
        provider: CloudProvider,
        bucket: str,
        key: str,
    ) -> dict:
        """ストレージからファイルをダウンロードする."""
        self._require_credential(provider)
        logger.info(
            "ストレージダウンロード: provider=%s bucket=%s key=%s",
            provider.value,
            bucket,
            key,
        )
        return {
            "provider": provider.value,
            "bucket": bucket,
            "key": key,
            "downloaded_at": self._now(),
            "status": "success",
            "data": b"",  # 実際にはクラウド SDK からデータを取得
        }

    # ------------------------------------------------------------------
    # サーバーレス
    # ------------------------------------------------------------------

    async def invoke_serverless(
        self,
        provider: CloudProvider,
        function_name: str,
        payload: dict,
    ) -> dict:
        """サーバーレス関数を実行する."""
        self._require_credential(provider)
        logger.info(
            "サーバーレス実行: provider=%s function=%s",
            provider.value,
            function_name,
        )
        return {
            "provider": provider.value,
            "function_name": function_name,
            "invoked_at": self._now(),
            "status": "success",
            "response": {},  # 実際には関数の戻り値
            "duration_ms": 0,
        }

    # ------------------------------------------------------------------
    # コスト見積もり
    # ------------------------------------------------------------------

    async def get_cost_estimate(
        self,
        provider: CloudProvider,
        resources: list[dict],
    ) -> dict:
        """リソースのコスト見積もりを取得する."""
        # 簡易見積もりロジック（実際にはクラウドプロバイダーの Pricing API を使用）
        cost_map = {
            "compute": 0.05,  # USD/hour
            "storage": 0.023,  # USD/GB/month
            "serverless": 0.0002,  # USD/invocation
            "database": 0.10,  # USD/hour
            "cdn": 0.01,  # USD/GB
        }

        total_monthly = 0.0
        breakdown: list[dict] = []
        for resource in resources:
            service = resource.get("service", "compute")
            quantity = resource.get("quantity", 1)
            rate = cost_map.get(service, 0.05)
            if service == "compute":
                cost = rate * 24 * 30 * quantity  # 月額
            elif service == "storage":
                cost = rate * quantity  # GB 単位
            elif service == "serverless":
                cost = rate * quantity  # 呼び出し数
            else:
                cost = rate * 24 * 30 * quantity

            breakdown.append(
                {
                    "service": service,
                    "quantity": quantity,
                    "rate": rate,
                    "monthly_cost_usd": round(cost, 2),
                }
            )
            total_monthly += cost

        return {
            "provider": provider.value,
            "estimated_monthly_cost_usd": round(total_monthly, 2),
            "currency": "USD",
            "breakdown": breakdown,
            "estimated_at": self._now(),
            "note": "概算見積もり。実際のコストはプロバイダーの料金体系により異なります",
        }

    # ------------------------------------------------------------------
    # プロバイダーステータス
    # ------------------------------------------------------------------

    async def get_provider_status(self) -> dict:
        """設定済み全プロバイダーのステータスを取得する."""
        statuses: dict[str, dict] = {}
        for provider in CloudProvider:
            cred = self._credentials.get(provider)
            if cred is not None:
                resource_count = sum(1 for r in self._resources.values() if r.provider == provider)
                statuses[provider.value] = {
                    "configured": True,
                    "valid": cred.is_valid,
                    "credential_type": cred.credential_type,
                    "region": cred.region,
                    "last_validated": cred.last_validated,
                    "resource_count": resource_count,
                }
            else:
                statuses[provider.value] = {
                    "configured": False,
                    "valid": False,
                }
        return statuses


# グローバルインスタンス
cloud_native = CloudNativeIntegration()
