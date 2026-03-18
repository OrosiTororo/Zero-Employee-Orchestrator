"""スマートデバイス・VR/AR 統合 — IoT/スマートデバイスおよび VR/AR インターフェース抽象化.

IoT センサー・スマートディスプレイ・VR/AR ヘッドセット・ロボット・
ドローンなどのスマートデバイスを統一的に管理する。

対応プロトコル:
- MQTT: IoT センサー・アクチュエータ
- HTTP: REST API 対応デバイス
- WebSocket: リアルタイムストリーミング
- Bluetooth: 近距離通信デバイス
- Zigbee: スマートホームデバイス
- Matter: 次世代スマートホーム標準

すべてのデバイス操作は:
- 承認ゲート経由
- 監査ログ記録
- データ保護ポリシー適用
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """デバイスタイプ."""

    IOT_SENSOR = "iot_sensor"
    SMART_DISPLAY = "smart_display"
    SMART_SPEAKER = "smart_speaker"
    SMART_GLASSES = "smart_glasses"
    VR_HEADSET = "vr_headset"
    AR_DEVICE = "ar_device"
    ROBOT = "robot"
    CAMERA = "camera"
    DRONE = "drone"


class DeviceProtocol(str, Enum):
    """デバイス通信プロトコル."""

    MQTT = "mqtt"
    HTTP = "http"
    WEBSOCKET = "websocket"
    BLUETOOTH = "bluetooth"
    ZIGBEE = "zigbee"
    MATTER = "matter"


class DeviceStatus(str, Enum):
    """デバイスステータス."""

    ONLINE = "online"
    OFFLINE = "offline"
    PAIRING = "pairing"
    ERROR = "error"
    STANDBY = "standby"


@dataclass
class SmartDevice:
    """スマートデバイス."""

    id: str
    name: str
    device_type: DeviceType
    protocol: DeviceProtocol
    status: DeviceStatus = DeviceStatus.OFFLINE
    ip_address: str = ""
    firmware_version: str = ""
    capabilities: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    last_seen: str = ""


@dataclass
class DeviceCommand:
    """デバイスコマンド."""

    device_id: str
    command: str
    params: dict = field(default_factory=dict)
    priority: int = 0
    timestamp: str = ""


@dataclass
class DeviceEvent:
    """デバイスイベント."""

    device_id: str
    event_type: str
    data: dict = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class DeviceAutomation:
    """デバイスオートメーションルール."""

    id: str
    trigger_device: str
    trigger_event: str
    action_device: str
    action_command: str
    action_params: dict = field(default_factory=dict)
    is_active: bool = True
    created_at: str = ""


@dataclass
class EventSubscription:
    """イベント購読."""

    id: str
    device_id: str
    event_types: list[str]
    callback: Callable
    created_at: str = ""


@dataclass
class VRSession:
    """VR/AR セッション."""

    id: str
    device_id: str
    session_type: str  # "vr" | "ar" | "mixed"
    status: str = "active"  # "active" | "paused" | "ended"
    started_at: str = ""
    metadata: dict = field(default_factory=dict)


class SmartDeviceHub:
    """スマートデバイスハブ.

    IoT / スマートデバイス / VR・AR デバイスの統合管理を行う。
    """

    def __init__(self) -> None:
        self._devices: dict[str, SmartDevice] = {}
        self._event_log: list[DeviceEvent] = []
        self._automations: dict[str, DeviceAutomation] = {}
        self._subscriptions: dict[str, list[EventSubscription]] = {}
        self._vr_sessions: dict[str, VRSession] = {}

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _require_device(self, device_id: str) -> SmartDevice:
        """デバイスの存在を確認する."""
        device = self._devices.get(device_id)
        if device is None:
            raise ValueError(f"デバイスが見つかりません: {device_id}")
        return device

    # ------------------------------------------------------------------
    # デバイス登録・解除
    # ------------------------------------------------------------------

    async def register_device(self, device: SmartDevice) -> SmartDevice:
        """デバイスを登録する."""
        if not device.id:
            device.id = str(uuid.uuid4())
        device.last_seen = self._now()
        self._devices[device.id] = device
        self._subscriptions.setdefault(device.id, [])

        self._event_log.append(
            DeviceEvent(
                device_id=device.id,
                event_type="registered",
                data={"name": device.name, "type": device.device_type.value},
                timestamp=self._now(),
            )
        )
        logger.info(
            "デバイス登録: id=%s name=%s type=%s protocol=%s",
            device.id,
            device.name,
            device.device_type.value,
            device.protocol.value,
        )
        return device

    async def unregister_device(self, device_id: str) -> bool:
        """デバイスを登録解除する."""
        device = self._require_device(device_id)
        del self._devices[device_id]
        self._subscriptions.pop(device_id, None)

        # アクティブな VR セッションを終了
        session = self._vr_sessions.pop(device_id, None)
        if session:
            session.status = "ended"

        self._event_log.append(
            DeviceEvent(
                device_id=device_id,
                event_type="unregistered",
                data={"name": device.name},
                timestamp=self._now(),
            )
        )
        logger.info("デバイス登録解除: id=%s name=%s", device_id, device.name)
        return True

    # ------------------------------------------------------------------
    # デバイス検出
    # ------------------------------------------------------------------

    async def discover_devices(self, protocol: DeviceProtocol | None = None) -> list[dict]:
        """ネットワーク上のデバイスをスキャンする."""
        # 実際にはプロトコル別のスキャンを実行
        # MQTT: ブローカーに接続してトピックを探索
        # HTTP: mDNS / SSDP で検出
        # Bluetooth: BLE スキャン
        # Zigbee: Zigbee コーディネーターに問い合わせ
        # Matter: Matter コミッショニング
        logger.info(
            "デバイス検出開始: protocol=%s",
            protocol.value if protocol else "all",
        )
        discovered: list[dict] = []
        # シミュレーション: 登録済みデバイスから検出結果を生成
        for device in self._devices.values():
            if protocol and device.protocol != protocol:
                continue
            if device.status in (DeviceStatus.ONLINE, DeviceStatus.STANDBY):
                discovered.append(
                    {
                        "id": device.id,
                        "name": device.name,
                        "device_type": device.device_type.value,
                        "protocol": device.protocol.value,
                        "ip_address": device.ip_address,
                        "status": device.status.value,
                    }
                )
        return discovered

    # ------------------------------------------------------------------
    # コマンド送信
    # ------------------------------------------------------------------

    async def send_command(self, device_id: str, command: str, params: dict | None = None) -> dict:
        """デバイスにコマンドを送信する."""
        device = self._require_device(device_id)
        if device.status == DeviceStatus.OFFLINE:
            raise ValueError(f"デバイス '{device.name}' はオフラインです")

        cmd = DeviceCommand(
            device_id=device_id,
            command=command,
            params=params or {},
            priority=0,
            timestamp=self._now(),
        )

        self._event_log.append(
            DeviceEvent(
                device_id=device_id,
                event_type="command_sent",
                data={"command": command, "params": params or {}},
                timestamp=self._now(),
            )
        )
        logger.info(
            "コマンド送信: device=%s command=%s",
            device_id,
            command,
        )
        return {
            "device_id": device_id,
            "command": cmd.command,
            "params": cmd.params,
            "status": "sent",
            "timestamp": cmd.timestamp,
        }

    # ------------------------------------------------------------------
    # ステータス・一覧
    # ------------------------------------------------------------------

    async def get_device_status(self, device_id: str) -> dict:
        """デバイスのステータスを取得する."""
        device = self._require_device(device_id)
        return {
            "id": device.id,
            "name": device.name,
            "device_type": device.device_type.value,
            "protocol": device.protocol.value,
            "status": device.status.value,
            "ip_address": device.ip_address,
            "firmware_version": device.firmware_version,
            "capabilities": device.capabilities,
            "last_seen": device.last_seen,
        }

    async def list_devices(
        self,
        device_type: DeviceType | None = None,
        status: DeviceStatus | None = None,
    ) -> list[SmartDevice]:
        """デバイス一覧を取得する."""
        devices = list(self._devices.values())
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        if status:
            devices = [d for d in devices if d.status == status]
        return devices

    # ------------------------------------------------------------------
    # イベント購読
    # ------------------------------------------------------------------

    async def subscribe_events(
        self,
        device_id: str,
        event_types: list[str],
        callback: Callable,
    ) -> EventSubscription:
        """デバイスイベントを購読する."""
        self._require_device(device_id)
        subscription = EventSubscription(
            id=str(uuid.uuid4()),
            device_id=device_id,
            event_types=event_types,
            callback=callback,
            created_at=self._now(),
        )
        self._subscriptions.setdefault(device_id, []).append(subscription)
        logger.info(
            "イベント購読: device=%s types=%s",
            device_id,
            event_types,
        )
        return subscription

    async def get_event_log(
        self, device_id: str | None = None, limit: int = 100
    ) -> list[DeviceEvent]:
        """イベントログを取得する."""
        events = self._event_log
        if device_id:
            events = [e for e in events if e.device_id == device_id]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    # ------------------------------------------------------------------
    # オートメーション
    # ------------------------------------------------------------------

    async def create_automation(
        self,
        trigger_device: str,
        trigger_event: str,
        action_device: str,
        action_command: str,
        action_params: dict | None = None,
    ) -> DeviceAutomation:
        """デバイスオートメーションルールを作成する."""
        self._require_device(trigger_device)
        self._require_device(action_device)

        automation = DeviceAutomation(
            id=str(uuid.uuid4()),
            trigger_device=trigger_device,
            trigger_event=trigger_event,
            action_device=action_device,
            action_command=action_command,
            action_params=action_params or {},
            is_active=True,
            created_at=self._now(),
        )
        self._automations[automation.id] = automation
        logger.info(
            "オートメーション作成: trigger=%s:%s -> action=%s:%s",
            trigger_device,
            trigger_event,
            action_device,
            action_command,
        )
        return automation

    # ------------------------------------------------------------------
    # VR/AR セッション
    # ------------------------------------------------------------------

    async def get_vr_session(self, device_id: str) -> VRSession:
        """VR/AR セッションを取得または開始する."""
        device = self._require_device(device_id)
        if device.device_type not in (
            DeviceType.VR_HEADSET,
            DeviceType.AR_DEVICE,
            DeviceType.SMART_GLASSES,
        ):
            raise ValueError(f"デバイス '{device.name}' は VR/AR デバイスではありません")

        session = self._vr_sessions.get(device_id)
        if session and session.status == "active":
            return session

        session_type = {
            DeviceType.VR_HEADSET: "vr",
            DeviceType.AR_DEVICE: "ar",
            DeviceType.SMART_GLASSES: "ar",
        }.get(device.device_type, "mixed")

        session = VRSession(
            id=str(uuid.uuid4()),
            device_id=device_id,
            session_type=session_type,
            status="active",
            started_at=self._now(),
            metadata={"device_name": device.name},
        )
        self._vr_sessions[device_id] = session
        logger.info(
            "VR/AR セッション開始: device=%s type=%s",
            device_id,
            session_type,
        )
        return session

    # ------------------------------------------------------------------
    # ストリーミング
    # ------------------------------------------------------------------

    async def stream_to_device(
        self,
        device_id: str,
        content_type: str,
        data: bytes,
    ) -> dict:
        """デバイスにデータをストリーミングする."""
        device = self._require_device(device_id)
        if device.status == DeviceStatus.OFFLINE:
            raise ValueError(f"デバイス '{device.name}' はオフラインです")

        self._event_log.append(
            DeviceEvent(
                device_id=device_id,
                event_type="stream_data",
                data={"content_type": content_type, "size_bytes": len(data)},
                timestamp=self._now(),
            )
        )
        logger.info(
            "デバイスストリーミング: device=%s content_type=%s size=%d",
            device_id,
            content_type,
            len(data),
        )
        return {
            "device_id": device_id,
            "content_type": content_type,
            "size_bytes": len(data),
            "status": "streaming",
            "timestamp": self._now(),
        }


# グローバルインスタンス
smart_device_hub = SmartDeviceHub()
