# Section 3 — バックエンド全構築（Claude Code 用）v11.2

> 担当: Claude Code（全ステップ）
> 前提: Section 2 が完了していること（uv sync 済み、main.py スケルトン動作確認済み）
> 完了条件: 全 API エンドポイント（33個）が動作し、Judge・Orchestrator・Self-Healing が機能すること
> 実装順序は依存関係に基づく。順序を変えないこと。
> v11.2 追加: ステップ 3.15〜3.17（Self-Healing DAG, Skill Registry, v11.2エンドポイント統合）

---

## 重要: このファイルを Claude Code に渡す方法

```
cd zpcos
claude
> read instructions_section3_backend.md, execute all steps in order
```

各ステップ完了後に確認コマンドを実行し、PASS を確認してから次へ進む。

---

## ステップ 3.1 — Token Store（auth/token_store.py）

`backend/app/auth/token_store.py` を実装してください。

### 要件

1. keyring に AES-256 暗号鍵のみ保存
   - キー名: `"zpcos-{service}-key"`
   - 値: 32バイトのランダム鍵を hex エンコード（64文字）
   - keyring のサービス名は `"zpcos"` で統一
2. トークン JSON は AES-GCM 暗号化して `%APPDATA%/zpcos/tokens/{service}.enc` に保存
3. AES-GCM 構造: nonce (12 bytes) + ciphertext + tag (16 bytes)
4. 使用ライブラリ: `from cryptography.hazmat.primitives.ciphers.aead import AESGCM`

### API

```python
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


async def save_token(service: str, token_data: dict) -> None:
    """トークンを暗号化して保存。"""
    # asyncio.to_thread でブロッキング回避
    ...

async def load_token(service: str) -> Optional[dict]:
    """トークンを復号して読み込み。ファイルが無ければ None。"""
    ...

async def delete_token(service: str) -> None:
    """トークンファイルと暗号鍵を削除。"""
    ...

async def has_token(service: str) -> bool:
    """トークンが存在するか。"""
    ...

def list_connections() -> list[str]:
    """tokens/ ディレクトリを走査して接続済みサービス一覧を返す。"""
    ...
```

### 確認

```powershell
cd backend
uv run python -c "
import asyncio
from app.auth.token_store import save_token, load_token, has_token, delete_token

async def test():
    await save_token('test', {'key': 'abc123'})
    assert await has_token('test')
    data = await load_token('test')
    assert data['key'] == 'abc123'
    await delete_token('test')
    assert not await has_token('test')
    print('token_store: ALL OK')

asyncio.run(test())
"
```

---

## ステップ 3.2 — OpenRouter OAuth PKCE（auth/openrouter_oauth.py）

`backend/app/auth/openrouter_oauth.py` を実装してください。

### 要件

1. Python 標準ライブラリ + httpx のみ（requests 不使用）
2. PKCE フロー:
   - `code_verifier`: `os.urandom(64)` → base64url（パディングなし）
   - `code_challenge`: code_verifier の SHA-256 → base64url
3. 認証 URL パラメータ:
   - `callback_url`: `"http://localhost:3000/callback"` (固定、変更不可)
   - `code_challenge`, `code_challenge_method`: `"S256"`
   - `limit`: `5.0`, `usage_limit_type`: `"monthly"`
4. ポート 3000 で一時 HTTP サーバーを起動:
   - 起動前にポート空き確認 (`socket.connect_ex`)
   - 使用中ならエラーメッセージ
   - `http.server.HTTPServer` で GET /callback を待受け
   - クエリパラメータから `code` を取得
5. code 受信 → httpx で POST `https://openrouter.ai/api/v1/auth/keys`:
   - body: `{ "code": code, "code_verifier": verifier, "code_challenge_method": "S256" }`
6. API key を `token_store.save_token("openrouter", {"key": api_key})` で保存
7. ブラウザに「認証完了。このタブを閉じてください。」HTML 表示
8. タイムアウト 120 秒
9. 全体を `asyncio.to_thread()` でスレッドオフロード
10. OpenRouter Python SDK（ベータ）は使用しない

### API

```python
async def start_pkce_flow() -> dict:
    """PKCE フローを開始し、結果を返す。"""
    # 1. code_verifier, code_challenge 生成
    # 2. webbrowser.open() で認証 URL を開く
    # 3. ポート 3000 で一時サーバー起動（asyncio.to_thread 内）
    # 4. code 受信 → API key 交換
    # 5. token_store に保存
    # 返り値: {"status": "ok", "message": "認証完了"}
    ...

async def get_auth_status() -> dict:
    """OpenRouter 認証状態を返す。"""
    token = await token_store.load_token("openrouter")
    if token and "key" in token:
        return {"authenticated": True}
    return {"authenticated": False}

async def logout() -> None:
    """OpenRouter のトークンを削除。"""
    await token_store.delete_token("openrouter")
```

---

## ステップ 3.3 — LiteLLM Gateway（gateway/__init__.py）

`backend/app/gateway/__init__.py` を実装してください。

### 要件

1. `providers.json` を `resource_path("gateway/providers.json")` で読み込み
2. `litellm.Router` を初期化
3. `api_key` は `token_store.load_token("openrouter")` で取得し、各 model の `litellm_params["api_key"]` に注入
4. キー未設定時は Router を None にする（認証 API は動作可能）
5. `enable_pre_call_checks=True`

### API

```python
import json
import litellm
from typing import Optional

from app.main import resource_path
from app.auth import token_store

_router: Optional[litellm.Router] = None


async def init_gateway() -> bool:
    """Router を初期化。成功時 True、キー未設定時 False。"""
    global _router
    token = await token_store.load_token("openrouter")
    if not token or "key" not in token:
        _router = None
        return False

    api_key = token["key"]
    providers_path = resource_path("gateway/providers.json")
    with open(providers_path, encoding="utf-8") as f:
        config = json.load(f)

    model_list = []
    for m in config["models"]:
        params = dict(m["litellm_params"])
        params["api_key"] = api_key
        model_list.append({
            "model_name": m["model_name"],
            "litellm_params": params,
        })

    rs = config.get("router_settings", {})
    _router = litellm.Router(
        model_list=model_list,
        routing_strategy=rs.get("routing_strategy", "simple-shuffle"),
        num_retries=rs.get("num_retries", 3),
        allowed_fails=rs.get("allowed_fails", 3),
        cooldown_time=rs.get("cooldown_time", 30),
        enable_pre_call_checks=True,
    )
    return True


async def call_llm(
    messages: list[dict],
    model_group: str = "fast",
    **kwargs,
) -> dict:
    """LLM を呼び出す。Router 未初期化時は例外。"""
    if _router is None:
        raise RuntimeError("Gateway not initialized. OpenRouter authentication required.")
    response = await _router.acompletion(
        model=model_group,
        messages=messages,
        **kwargs,
    )
    return response


def is_ready() -> bool:
    """Router が初期化済みか。"""
    return _router is not None
```

### 確認

```powershell
# Gateway の初期化テスト（認証キーなしの場合）
uv run python -c "
import asyncio
from app.gateway import init_gateway, is_ready
async def test():
    result = await init_gateway()
    print(f'init_gateway returned: {result}')
    print(f'is_ready: {is_ready()}')
    # キーなしなので False が正常
asyncio.run(test())
"
```

---

## ステップ 3.4 — Google OAuth（auth/google_oauth.py）

`backend/app/auth/google_oauth.py` を実装してください。

### 要件

```python
import os
import json
import asyncio
from pathlib import Path
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.main import resource_path
from app.auth import token_store


def _find_client_secrets() -> Path:
    """client_secret.json を 3段階で探索。"""
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "zpcos" / "client_secret.json",
        resource_path("client_secret.json"),
        Path(__file__).parent.parent.parent / "client_secret.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(
        "client_secret.json が見つかりません。"
        "Google Cloud Console からダウンロードし、設定画面からインポートしてください。"
    )


def _load_scopes() -> list[str]:
    """connectors/google.json からスコープを読み込み。"""
    p = resource_path("auth/connectors/google.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)["scopes"]


async def connect_google() -> dict:
    """Google OAuth フローを開始。ブラウザが開く。"""
    secrets_path = _find_client_secrets()
    scopes = _load_scopes()
    flow = InstalledAppFlow.from_client_secrets_file(
        str(secrets_path), scopes, autogenerate_code_verifier=True
    )
    # ブロッキングなのでスレッドオフロード
    credentials = await asyncio.to_thread(
        flow.run_local_server, port=0, open_browser=True
    )
    # トークンを保存
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or []),
    }
    await token_store.save_token("google", token_data)
    return {"status": "ok", "scopes": token_data["scopes"]}


async def get_google_credentials() -> Optional[Credentials]:
    """有効な Google Credentials を返す。期限切れなら自動更新。"""
    token_data = await token_store.load_token("google")
    if not token_data:
        return None
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )
    if creds.expired and creds.refresh_token:
        try:
            await asyncio.to_thread(creds.refresh, Request())
            # 更新後のトークンを保存
            token_data["token"] = creds.token
            await token_store.save_token("google", token_data)
        except Exception:
            return None
    return creds


async def disconnect_google() -> None:
    """Google トークンを削除。"""
    await token_store.delete_token("google")
```

---

## ステップ 3.5 — AuthHub（auth/authhub.py）

`backend/app/auth/authhub.py` を実装してください。

### 要件

```python
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from app.main import resource_path
from app.auth import token_store
from app.auth import openrouter_oauth
from app.auth import google_oauth

router = APIRouter(prefix="/api/auth", tags=["auth"])

# コネクター定義を起動時に読み込み
_connectors: dict[str, dict] = {}


def load_connectors() -> None:
    """connectors/ ディレクトリの JSON を全読み込み。"""
    global _connectors
    connectors_dir = resource_path("auth/connectors")
    for f in Path(connectors_dir).glob("*.json"):
        if f.name.startswith("_"):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        _connectors[data["service"]] = data


@router.post("/login")
async def login():
    """OpenRouter PKCE フローを開始。"""
    return await openrouter_oauth.start_pkce_flow()


@router.get("/status")
async def auth_status():
    """OpenRouter 認証状態を返す。"""
    return await openrouter_oauth.get_auth_status()


@router.post("/logout")
async def logout():
    """OpenRouter ログアウト。"""
    await openrouter_oauth.logout()
    return {"status": "ok"}


@router.post("/connect/{service}")
async def connect_service(service: str):
    """外部サービスに接続。"""
    if service == "openrouter":
        return await openrouter_oauth.start_pkce_flow()
    elif service == "google":
        return await google_oauth.connect_google()
    else:
        raise HTTPException(404, f"Unknown service: {service}")


@router.get("/connections")
async def list_connections():
    """全コネクターの接続状態を返す。"""
    result = []
    for svc, meta in _connectors.items():
        connected = await token_store.has_token(svc)
        result.append({
            "service": svc,
            "display_name": meta["display_name"],
            "connected": connected,
        })
    return result


@router.delete("/disconnect/{service}")
async def disconnect_service(service: str):
    """サービスを切断。"""
    if service == "google":
        await google_oauth.disconnect_google()
    else:
        await token_store.delete_token(service)
    return {"status": "ok"}


@router.get("/token/{service}")
async def get_token(service: str):
    """内部 API: 有効なトークンを返す。"""
    if service == "google":
        creds = await google_oauth.get_google_credentials()
        if not creds:
            raise HTTPException(401, "Google not connected or token expired")
        return {"token": creds.token, "scopes": list(creds.scopes or [])}
    token = await token_store.load_token(service)
    if not token:
        raise HTTPException(401, f"{service} not connected")
    return token
```

### 確認

```powershell
# main.py に AuthHub ルーターを登録（ステップ 3.10 で完成するが先に部分テスト）
uv run python -c "
from app.auth.authhub import load_connectors, _connectors
load_connectors()
print(f'Loaded connectors: {list(_connectors.keys())}')
assert 'google' in _connectors
assert 'openrouter' in _connectors
print('authhub: ALL OK')
"
```

---

## ステップ 3.6 — Policy Pack（policy/policy_pack.py）★v11.1

`backend/app/policy/policy_pack.py` を作成:

```python
"""Policy Pack — コンプライアンスチェック。
禁止表現・誇大表現・差別表現などのポリシーを提案段階で検出。
"""

from pydantic import BaseModel


class PolicyRule(BaseModel):
    category: str  # forbidden_expression | exaggeration | discrimination | legal_risk
    pattern: str
    severity: str  # error | warning | info
    suggestion: str


class PolicyViolation(BaseModel):
    rule: PolicyRule
    matched_text: str
    position: int = 0


# デフォルトポリシー（ユーザーがカスタマイズ可能）
DEFAULT_POLICIES: list[dict] = [
    {"category": "exaggeration", "pattern": "絶対", "severity": "warning",
     "suggestion": "「高い確率で」等の表現に置き換えを検討"},
    {"category": "exaggeration", "pattern": "100%", "severity": "warning",
     "suggestion": "具体的な根拠がない場合は数値の修正を検討"},
    {"category": "forbidden_expression", "pattern": "必ず儲かる", "severity": "error",
     "suggestion": "投資・収益の断定的表現は法的リスクがあります"},
    {"category": "discrimination", "pattern": "〇〇人は", "severity": "error",
     "suggestion": "民族・国籍に基づく一般化は避けてください"},
]


async def check_policy(text: str, custom_rules: list[dict] | None = None) -> list[PolicyViolation]:
    """テキストに対してポリシーチェックを実行。"""
    rules = [PolicyRule(**r) for r in (custom_rules or DEFAULT_POLICIES)]
    violations = []
    for rule in rules:
        if rule.pattern in text:
            pos = text.index(rule.pattern)
            violations.append(PolicyViolation(rule=rule, matched_text=rule.pattern, position=pos))
    return violations
```

`policy/__init__.py`:
```python
"""Policy Pack — コンプライアンスチェック。"""
from app.policy.policy_pack import check_policy, PolicyViolation  # noqa: F401
```

---

## ステップ 3.6b — Two-stage Detection（judge/pre_check.py）★v11.1

`backend/app/judge/pre_check.py` を作成:

```python
"""Two-stage Detection — Stage 1: 安価なルールベースチェック。
Stage 1 が PASS した場合のみ Stage 2（Cross-Model Judge）を実行。
"""

from pydantic import BaseModel
from app.policy.policy_pack import check_policy


class PreCheckResult(BaseModel):
    passed: bool
    issues: list[str] = []
    stage: int = 1  # 1 = pre_check, 2 = full_judge


async def pre_check(text: str, context: str = "") -> PreCheckResult:
    """Stage 1: 安価なチェック。"""
    issues = []

    # 1. 空入力チェック
    if not text or len(text.strip()) < 10:
        issues.append("入力が短すぎます（最低10文字）")

    # 2. ポリシーチェック
    violations = await check_policy(text)
    for v in violations:
        if v.rule.severity == "error":
            issues.append(f"ポリシー違反: {v.rule.suggestion}")

    # 3. コスト超過チェック（トークン数概算）
    estimated_tokens = len(text) * 2  # 日本語の概算
    if estimated_tokens > 100000:
        issues.append(f"テキストが長すぎます（推定{estimated_tokens}トークン）。分割を検討してください。")

    return PreCheckResult(passed=len(issues) == 0, issues=issues, stage=1)
```

---

## ステップ 3.7 — Cross-Model Judge（judge/ 5ファイル）

### 3.6.1 — judge/models.py（Pydantic モデル定義）

`backend/app/judge/models.py` を作成:

```python
"""Judge パイプラインの Pydantic モデル定義。"""

from pydantic import BaseModel, Field


class Segment(BaseModel):
    id: str
    text: str
    category: str = Field(description="claim | number | name | logic")


class SampleResult(BaseModel):
    segment_id: str
    model_name: str
    response: str
    agrees: bool


class EvalResult(BaseModel):
    segment_id: str
    score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)


class JudgeResult(BaseModel):
    segments: list[Segment]
    samples: list[SampleResult]
    eval_results: list[EvalResult]
    improved_output: str
    overall_score: float = Field(ge=0.0, le=1.0)
```

### 3.6.2 — judge/segmenter.py

```python
"""Segmenter — テキストを評価単位に分割。"""

import json
from app.gateway import call_llm
from app.judge.models import Segment


async def segment(text: str) -> list[Segment]:
    """テキストを事実主張・数値・固有名詞・論理の単位に分割。"""
    prompt = f"""以下のテキストを評価可能な単位（セグメント）に分割してください。
各セグメントは以下のいずれかのカテゴリに分類してください:
- claim: 事実に関する主張
- number: 数値データ
- name: 固有名詞・人名・組織名
- logic: 論理的推論・因果関係

JSON 配列で返してください。各要素は {{"id": "seg_1", "text": "...", "category": "..."}} の形式です。
JSON のみを返し、他のテキストは含めないでください。

テキスト:
{text}"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="fast",
    )
    content = response.choices[0].message.content
    # JSON パース（```json ... ``` で囲まれている場合も処理）
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    segments_data = json.loads(content.strip())
    return [Segment(**s) for s in segments_data]
```

### 3.6.3 — judge/sampler.py

```python
"""Sampler — 複数モデルから回答サンプリング。"""

import asyncio
import json
from app.gateway import call_llm
from app.judge.models import Segment, SampleResult

# 検証に使う 3 モデルグループ
JUDGE_MODELS = ["fast", "quality", "value"]


async def _check_segment(segment: Segment, context: str, model_group: str) -> SampleResult:
    """1つのセグメントを1つのモデルで検証。"""
    prompt = f"""以下の主張が正しいかどうかを検証してください。

コンテキスト: {context}

主張: {segment.text}
カテゴリ: {segment.category}

JSON で返してください: {{"agrees": true/false, "reason": "..."}}
JSON のみを返し、他のテキストは含めないでください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group=model_group,
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    try:
        result = json.loads(content.strip())
    except json.JSONDecodeError:
        result = {"agrees": False, "reason": "Parse error"}

    return SampleResult(
        segment_id=segment.id,
        model_name=model_group,
        response=result.get("reason", ""),
        agrees=result.get("agrees", False),
    )


async def sample(segments: list[Segment], context: str) -> list[SampleResult]:
    """全セグメントを全モデルで並列検証。"""
    tasks = []
    for seg in segments:
        for model in JUDGE_MODELS:
            tasks.append(_check_segment(seg, context, model))
    return await asyncio.gather(*tasks)
```

### 3.6.4 — judge/evaluator.py

```python
"""Evaluator — 複数モデルの結果からスコアを算出。"""

from collections import defaultdict
from app.judge.models import SampleResult, EvalResult


async def evaluate(
    segments: list,
    samples: list[SampleResult],
) -> list[EvalResult]:
    """各セグメントのスコアを算出。3モデル一致→1.0、2/3→0.67、全不一致→0.0"""
    # segment_id ごとにグループ化
    grouped: dict[str, list[SampleResult]] = defaultdict(list)
    for s in samples:
        grouped[s.segment_id].append(s)

    results = []
    for seg_id, seg_samples in grouped.items():
        agrees_count = sum(1 for s in seg_samples if s.agrees)
        total = len(seg_samples)

        if total == 0:
            score = 0.0
        elif agrees_count == total:
            score = 1.0
        elif agrees_count >= total * 2 / 3:
            score = 0.67
        else:
            score = 0.0

        issues = [s.response for s in seg_samples if not s.agrees and s.response]
        results.append(EvalResult(segment_id=seg_id, score=score, issues=issues))

    return results
```

### 3.6.5 — judge/improver.py

```python
"""Improver — 低スコアセグメントの自動改善。"""

from app.gateway import call_llm
from app.judge.models import EvalResult


async def improve(original: str, eval_results: list[EvalResult]) -> str:
    """score < 0.67 のセグメントのみ修正した改善版を生成。"""
    low_score_issues = []
    for er in eval_results:
        if er.score < 0.67:
            low_score_issues.append({
                "segment_id": er.segment_id,
                "issues": er.issues,
            })

    if not low_score_issues:
        return original  # 修正不要

    issues_text = "\n".join(
        f"- セグメント {i['segment_id']}: {', '.join(i['issues'])}"
        for i in low_score_issues
    )

    prompt = f"""以下のテキストに問題が見つかりました。指摘された問題のみを修正してください。
修正していない部分はそのまま保持してください。

元のテキスト:
{original}

指摘された問題:
{issues_text}

修正後のテキストのみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    return response.choices[0].message.content
```

### 3.6.6 — judge/pipeline.py

```python
"""Cross-Model Judge Pipeline — メインオーケストレーター。"""

from app.judge.models import JudgeResult
from app.judge.segmenter import segment
from app.judge.sampler import sample
from app.judge.evaluator import evaluate
from app.judge.improver import improve


async def judge(original_output: str, context: str = "") -> JudgeResult:
    """Judge パイプラインを実行（Two-stage Detection 統合）。"""
    from app.judge.pre_check import pre_check

    # Stage 1: 安価なプリチェック
    pre_result = await pre_check(original_output, context)
    if not pre_result.passed:
        # Stage 1 で問題検出 → Stage 2 スキップ、問題をそのまま返す
        return JudgeResult(
            segments=[], samples=[], eval_results=[],
            improved_output=original_output,
            overall_score=0.0,
        )

    # Stage 2: Cross-Model Judge（高価）
    # 1. Segmenter: テキストを評価単位に分割
    segments = await segment(original_output)

    # 2. Sampler: 複数モデルで並列検証
    samples = await sample(segments, context)

    # 3. Evaluator: スコア算出
    eval_results = await evaluate(segments, samples)

    # 4. Improver: 低スコア修正
    improved = await improve(original_output, eval_results)

    # 全体スコア
    if eval_results:
        overall = sum(er.score for er in eval_results) / len(eval_results)
    else:
        overall = 1.0

    return JudgeResult(
        segments=segments,
        samples=samples,
        eval_results=eval_results,
        improved_output=improved,
        overall_score=round(overall, 2),
    )
```

### judge/__init__.py を更新

```python
"""Cross-Model Judge Pipeline.
pipeline.py → segmenter.py → sampler.py → evaluator.py → improver.py
"""
from app.judge.pipeline import judge  # noqa: F401
from app.judge.models import JudgeResult  # noqa: F401
```

---

## ステップ 3.7 — 状態機械（state/）

`backend/app/state/machine.py` を作成:

```python
"""State Machine — AsyncMachine + aiosqlite 永続化。"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosqlite
from transitions.extensions.asyncio import AsyncMachine
from pydantic import BaseModel


class TaskData(BaseModel):
    id: str
    skill_name: str
    state: str
    input_data: dict
    output_data: Optional[dict] = None
    judge_result: Optional[dict] = None
    created_at: str
    updated_at: str


# 状態定義
STATES = [
    "draft",
    "ai_executing",
    "ai_completed",
    "judging",
    "judge_completed",
    "human_review",
    "approved",
    "rejected",
    "committed",
    "error",
]

# 遷移定義
TRANSITIONS = [
    {"trigger": "start_execution", "source": "draft", "dest": "ai_executing"},
    {"trigger": "complete_execution", "source": "ai_executing", "dest": "ai_completed"},
    {"trigger": "start_judging", "source": "ai_completed", "dest": "judging"},
    {"trigger": "complete_judging", "source": "judging", "dest": "judge_completed"},
    {"trigger": "request_review", "source": "judge_completed", "dest": "human_review"},
    {"trigger": "approve", "source": "human_review", "dest": "approved"},
    {"trigger": "reject", "source": "human_review", "dest": "rejected"},
    {"trigger": "commit", "source": "approved", "dest": "committed"},
    {"trigger": "revise", "source": "rejected", "dest": "draft"},
    # error は任意状態から遷移可能
    {"trigger": "fail", "source": "*", "dest": "error"},
]


class TaskStateMachine:
    """タスクの状態機械。"""

    def __init__(self, task_id: str, initial_state: str = "draft"):
        self.task_id = task_id
        self.state = initial_state
        self.machine = AsyncMachine(
            model=self,
            states=STATES,
            transitions=TRANSITIONS,
            initial=initial_state,
            auto_transitions=False,
        )


# --- SQLite 永続化 ---

_db_path: Optional[str] = None


async def init_db(db_path: str = "zpcos_tasks.db") -> None:
    """DB を初期化。"""
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                skill_name TEXT NOT NULL,
                state TEXT NOT NULL,
                input_data TEXT NOT NULL,
                output_data TEXT,
                judge_result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def create_task(skill_name: str, input_data: dict) -> TaskData:
    """新規タスクを作成。"""
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    task = TaskData(
        id=task_id,
        skill_name=skill_name,
        state="draft",
        input_data=input_data,
        created_at=now,
        updated_at=now,
    )
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO tasks (id, skill_name, state, input_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (task.id, task.skill_name, task.state, json.dumps(task.input_data), task.created_at, task.updated_at),
        )
        await db.commit()
    return task


async def get_task(task_id: str) -> Optional[TaskData]:
    """タスクを取得。"""
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return TaskData(
            id=row["id"],
            skill_name=row["skill_name"],
            state=row["state"],
            input_data=json.loads(row["input_data"]),
            output_data=json.loads(row["output_data"]) if row["output_data"] else None,
            judge_result=json.loads(row["judge_result"]) if row["judge_result"] else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def transition_task(task_id: str, trigger: str) -> TaskData:
    """タスクの状態遷移。"""
    task = await get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    sm = TaskStateMachine(task_id, initial_state=task.state)
    trigger_fn = getattr(sm, trigger, None)
    if trigger_fn is None:
        raise ValueError(f"Unknown trigger: {trigger}")
    await trigger_fn()

    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "UPDATE tasks SET state = ?, updated_at = ? WHERE id = ?",
            (sm.state, now, task_id),
        )
        await db.commit()

    task.state = sm.state
    task.updated_at = now
    return task


async def update_task_data(task_id: str, output_data: dict = None, judge_result: dict = None) -> None:
    """タスクの出力データや Judge 結果を更新。"""
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path) as db:
        if output_data is not None:
            await db.execute(
                "UPDATE tasks SET output_data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(output_data), now, task_id),
            )
        if judge_result is not None:
            await db.execute(
                "UPDATE tasks SET judge_result = ?, updated_at = ? WHERE id = ?",
                (json.dumps(judge_result), now, task_id),
            )
        await db.commit()


async def list_tasks(limit: int = 50) -> list[TaskData]:
    """タスク一覧を取得。"""
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            TaskData(
                id=row["id"],
                skill_name=row["skill_name"],
                state=row["state"],
                input_data=json.loads(row["input_data"]),
                output_data=json.loads(row["output_data"]) if row["output_data"] else None,
                judge_result=json.loads(row["judge_result"]) if row["judge_result"] else None,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
```

`state/__init__.py` を更新:

```python
"""State Machine — AsyncMachine (python-transitions) + aiosqlite."""
from app.state.machine import (  # noqa: F401
    init_db, create_task, get_task, transition_task,
    update_task_data, list_tasks, TaskData, STATES, TRANSITIONS,
)
```

---

## ステップ 3.8b — Experience Memory + Failure Taxonomy + Artifact Bridge ★v11.1

### state/experience.py

```python
"""Experience Memory — 成功体験の横展開。"""

import json
from datetime import datetime, timezone
import aiosqlite
from pydantic import BaseModel


class ExperienceCard(BaseModel):
    id: str = ""
    task_type: str
    success_factors: list[str]
    model_used: str
    score: float
    context: str
    created_at: str = ""


_db_path: str | None = None


async def init_experience_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY,
                task_type TEXT, success_factors TEXT,
                model_used TEXT, score REAL, context TEXT,
                created_at TEXT
            )
        """)
        await db.commit()


async def save_experience(card: ExperienceCard) -> None:
    import uuid
    card.id = str(uuid.uuid4())
    card.created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO experiences VALUES (?,?,?,?,?,?,?)",
            (card.id, card.task_type, json.dumps(card.success_factors),
             card.model_used, card.score, card.context, card.created_at),
        )
        await db.commit()


async def get_relevant_experiences(task_type: str, limit: int = 5) -> list[ExperienceCard]:
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM experiences WHERE task_type = ? ORDER BY score DESC LIMIT ?",
            (task_type, limit),
        )
        rows = await cursor.fetchall()
        return [
            ExperienceCard(
                id=r["id"], task_type=r["task_type"],
                success_factors=json.loads(r["success_factors"]),
                model_used=r["model_used"], score=r["score"],
                context=r["context"], created_at=r["created_at"],
            )
            for r in rows
        ]
```

### state/failure.py

```python
"""Failure Taxonomy — 失敗分類と復旧策。"""

from enum import Enum
from pydantic import BaseModel
from app.gateway import call_llm


class FailureType(str, Enum):
    AUTH_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    SPEC_CHANGE = "spec_change"
    INPUT_MISSING = "input_missing"
    EVIDENCE_WEAK = "evidence_weak"
    CONTRADICTION = "contradiction"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FailureRecord(BaseModel):
    failure_type: FailureType
    message: str
    recoverable: bool
    suggested_action: str


class RecoveryStrategy(BaseModel):
    strategy: str  # retry | skip | escalate | modify_input
    description: str
    auto_applicable: bool  # 人間に聞く必要がないか


async def classify_failure(error: Exception | str) -> FailureRecord:
    """エラーを分類。"""
    msg = str(error)
    if "401" in msg or "auth" in msg.lower():
        return FailureRecord(failure_type=FailureType.AUTH_ERROR, message=msg,
                             recoverable=True, suggested_action="再認証してください")
    if "429" in msg or "rate" in msg.lower():
        return FailureRecord(failure_type=FailureType.RATE_LIMIT, message=msg,
                             recoverable=True, suggested_action="30秒待って再試行")
    if "timeout" in msg.lower():
        return FailureRecord(failure_type=FailureType.TIMEOUT, message=msg,
                             recoverable=True, suggested_action="再試行またはタイムアウト延長")
    return FailureRecord(failure_type=FailureType.UNKNOWN, message=msg,
                         recoverable=False, suggested_action="エラー詳細を確認してください")


async def suggest_recovery(failure: FailureRecord) -> RecoveryStrategy:
    """復旧策を提案。"""
    if failure.failure_type == FailureType.RATE_LIMIT:
        return RecoveryStrategy(strategy="retry", description="30秒後に自動再試行",
                                auto_applicable=True)
    if failure.failure_type == FailureType.AUTH_ERROR:
        return RecoveryStrategy(strategy="escalate", description="再認証が必要です",
                                auto_applicable=False)
    return RecoveryStrategy(strategy="escalate", description="手動確認が必要です",
                            auto_applicable=False)
```

### state/artifact_bridge.py

```python
"""Artifact Bridge — 業務間の成果物接続。"""

import json
import aiosqlite
from pydantic import BaseModel


class ArtifactSlot(BaseModel):
    id: str = ""
    slot_type: str  # insight | copy | data | analysis
    content: str
    source_task_id: str
    tags: list[str] = []


_db_path: str | None = None


async def init_artifact_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY, slot_type TEXT,
                content TEXT, source_task_id TEXT, tags TEXT
            )
        """)
        await db.commit()


async def save_artifact(slot: ArtifactSlot) -> None:
    import uuid
    slot.id = str(uuid.uuid4())
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO artifacts VALUES (?,?,?,?,?)",
            (slot.id, slot.slot_type, slot.content,
             slot.source_task_id, json.dumps(slot.tags)),
        )
        await db.commit()


async def find_relevant_artifacts(tags: list[str], limit: int = 5) -> list[ArtifactSlot]:
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM artifacts ORDER BY rowid DESC LIMIT ?", (limit * 3,)
        )
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            stored_tags = json.loads(r["tags"])
            if any(t in stored_tags for t in tags):
                results.append(ArtifactSlot(
                    id=r["id"], slot_type=r["slot_type"], content=r["content"],
                    source_task_id=r["source_task_id"], tags=stored_tags,
                ))
            if len(results) >= limit:
                break
        return results
```

---

## ステップ 3.9 — Skill フレームワーク（skills/）

`backend/app/skills/framework.py` を作成:

```python
"""Skill Framework — SkillBase + SkillRegistry。"""

import json
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel


class SkillMeta(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    input_schema: dict = {}
    output_schema: dict = {}
    requires_auth: list[dict] = []


class SkillBase(ABC):
    """全 Skill の基底クラス。"""

    def __init__(self, meta: SkillMeta, skill_dir: Path):
        self.meta = meta
        self.skill_dir = skill_dir

    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """Skill を実行。"""
        ...


class SkillRegistry:
    """Skill の登録・管理。"""

    def __init__(self):
        self._skills: dict[str, SkillBase] = {}

    def scan_builtins(self, builtins_dir: Path) -> None:
        """builtins/ ディレクトリを走査し、全 Skill を登録。"""
        if not builtins_dir.exists():
            return
        for skill_dir in builtins_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_json = skill_dir / "SKILL.json"
            executor_py = skill_dir / "executor.py"
            if not skill_json.exists() or not executor_py.exists():
                continue
            try:
                self.register_skill(skill_dir)
            except Exception as e:
                print(f"Warning: Failed to load skill {skill_dir.name}: {e}")

    def register_skill(self, skill_dir: Path) -> None:
        """1つの Skill を登録。"""
        skill_json = skill_dir / "SKILL.json"
        executor_py = skill_dir / "executor.py"

        meta = SkillMeta(**json.loads(skill_json.read_text(encoding="utf-8")))

        # executor.py を動的インポート
        spec = importlib.util.spec_from_file_location(
            f"skills.{meta.name}", executor_py
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # executor.py には Executor クラスが定義されている前提
        executor_class = getattr(module, "Executor")
        skill_instance = executor_class(meta=meta, skill_dir=skill_dir)
        self._skills[meta.name] = skill_instance

    def list_skills(self) -> list[SkillMeta]:
        """登録済み Skill のメタデータ一覧。"""
        return [s.meta for s in self._skills.values()]

    def get_skill(self, name: str) -> Optional[SkillBase]:
        """名前で Skill を取得。"""
        return self._skills.get(name)

    def has_skill(self, name: str) -> bool:
        return name in self._skills
```

`skills/__init__.py` を更新:

```python
"""Skill Framework."""
from app.skills.framework import SkillBase, SkillMeta, SkillRegistry  # noqa: F401
```

---

## ステップ 3.9b — Skill Gap Negotiation + ROI Explainer ★v11.1

### skills/gap_detector.py

```python
"""Skill Gap Negotiation — 不足Skillの検出と提案。"""

from pydantic import BaseModel
from app.skills.framework import SkillRegistry
from app.orchestrator.models import OrchestrationPlan


class SkillGap(BaseModel):
    required_skill: str
    reason: str
    options: list[str]  # ["代替: yt-script で代用", "自動生成", "スキップ"]


async def detect_gaps(plan: OrchestrationPlan, registry: SkillRegistry) -> list[SkillGap]:
    """Plan で必要な Skill のうち、未登録のものを検出。"""
    gaps = []
    for step in plan.steps:
        if not registry.has_skill(step.skill_name):
            gaps.append(SkillGap(
                required_skill=step.skill_name,
                reason=f"Plan のステップ '{step.step_id}' で必要ですが未登録です",
                options=[
                    f"代替: 既存 Skill で代用する",
                    f"自動生成: '{step.skill_name}' を AI で生成する",
                    f"スキップ: このステップを除外して実行する",
                ],
            ))
    return gaps
```

### skills/roi_explainer.py

```python
"""Skill ROI Explainer — Skill作成の価値説明。"""

from pydantic import BaseModel


class ROIReport(BaseModel):
    skill_name: str
    alternatives: list[str]
    value: dict  # reuse_potential, time_saved_minutes, accuracy_improvement
    risks: list[str]  # dependency, maintenance


async def explain_roi(skill_name: str, description: str) -> ROIReport:
    """Skill 作成の ROI を説明。"""
    return ROIReport(
        skill_name=skill_name,
        alternatives=[f"手動で {description} を実行", "既存 Skill の組み合わせで代用"],
        value={
            "reuse_potential": "高（同類タスクで再利用可能）",
            "time_saved_minutes": 30,
            "accuracy_improvement": "Judge による品質保証付き",
        },
        risks=[
            "外部 API 依存がある場合、API 仕様変更の影響を受ける",
            "定期的なメンテナンスが必要な場合がある",
        ],
    )
```

---

## ステップ 3.10 — Skill 自動生成エンジン（engine/）

`backend/app/engine/skill_generator.py` を作成:

```python
"""Skill Auto-Generation Engine.
LLM に SKILL.json + executor.py を生成させ、安全性検証後に登録。
"""

import ast
import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from app.gateway import call_llm
from app.main import resource_path


class SkillGenerationResult(BaseModel):
    skill_json: dict
    code: str
    safety_passed: bool
    safety_issues: list[str] = []
    registered: bool = False


# セキュリティ
IMPORT_WHITELIST = {"httpx", "json", "re", "datetime", "pydantic", "math", "typing", "asyncio"}
FUNCTION_BLACKLIST = {"eval", "exec", "compile", "__import__", "os.system", "subprocess"}


def _validate_ast(code: str) -> tuple[bool, list[str]]:
    """AST パースで安全性検証。"""
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]

    for node in ast.walk(tree):
        # インポート検証
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module not in IMPORT_WHITELIST:
                    issues.append(f"Forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                if module not in IMPORT_WHITELIST:
                    issues.append(f"Forbidden import: {node.module}")
        # 関数ブラックリスト
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FUNCTION_BLACKLIST:
                issues.append(f"Forbidden function: {node.func.id}")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in FUNCTION_BLACKLIST:
                issues.append(f"Forbidden function: {node.func.attr}")

    return len(issues) == 0, issues


async def generate_skill(description: str) -> SkillGenerationResult:
    """自然言語の説明から Skill を自動生成。"""
    prompt = f"""ユーザーの要望に基づいて、ZPCOS Skill を生成してください。

要望: {description}

以下の 2 つを JSON で返してください:
1. skill_json: SKILL.json の内容
2. code: executor.py の内容（文字列）

フォーマット:
```json
{{
  "skill_json": {{
    "name": "skill-name",
    "description": "...",
    "version": "1.0.0",
    "input_schema": {{}},
    "output_schema": {{}},
    "requires_auth": []
  }},
  "code": "import json\\n..."
}}
```

executor.py のルール:
- SkillBase を継承した Executor クラスを定義
- async def execute(self, input_data: dict) -> dict を実装
- インポート可能: httpx, json, re, datetime, pydantic, math, typing, asyncio
- 使用禁止: eval, exec, compile, __import__, os.system, subprocess, open（書込）
- LLM 呼び出しは from app.gateway import call_llm を使用

JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]

    try:
        result = json.loads(content.strip())
    except json.JSONDecodeError:
        return SkillGenerationResult(
            skill_json={}, code="", safety_passed=False,
            safety_issues=["Failed to parse LLM response as JSON"],
        )

    code = result.get("code", "")
    skill_json = result.get("skill_json", {})

    # AST 安全性検証
    safe, issues = _validate_ast(code)

    return SkillGenerationResult(
        skill_json=skill_json,
        code=code,
        safety_passed=safe,
        safety_issues=issues,
    )
```

---

## ステップ 3.11 — Design Interview（interview/）★v11.1

### interview/interviewer.py

```python
"""Design Interview — 実行前の壁打ち・すり合わせ。"""

import json
import uuid
from pydantic import BaseModel
from app.gateway import call_llm


class InterviewQuestion(BaseModel):
    question: str
    question_type: str = "mixed"  # choice | freetext | mixed
    choices: list[str] = []  # choice/mixed の場合の選択肢
    context: str = ""  # なぜこの質問をするかの説明


class InterviewSession(BaseModel):
    session_id: str
    user_input: str
    questions: list[InterviewQuestion]
    answers: list[dict] = []
    status: str = "active"  # active | finalized


class SpecDocument(BaseModel):
    requirements: list[str]
    constraints: list[str]
    priorities: list[str]
    acceptance_criteria: list[str]
    ai_assumptions: list[str] = []  # AIが補完した前提


# インメモリセッション管理（MVP）
_sessions: dict[str, InterviewSession] = {}


async def start_interview(user_input: str) -> InterviewSession:
    """インタビュー開始。深い質問を生成。"""
    prompt = f"""ユーザーが以下のタスクを依頼しています:
「{user_input}」

このタスクを正確に実行するために、ユーザーに確認すべき重要な質問を5-8個生成してください。
表面的・自明な質問ではなく、ユーザーも言語化していない前提を掘り起こす深い質問をしてください。

カテゴリ: 目的の詳細 / 制約条件 / 品質基準 / 優先順位 / 対象範囲 / 例外ケース / 運用想定

各質問に選択肢（2-4個）を付けてください。自由記述も可とします。

JSON配列で返してください:
[{{"question": "...", "question_type": "mixed", "choices": ["A", "B", "C"], "context": "この質問の意図"}}]
JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    questions = [InterviewQuestion(**q) for q in json.loads(content.strip())]

    session = InterviewSession(
        session_id=str(uuid.uuid4()),
        user_input=user_input,
        questions=questions,
    )
    _sessions[session.session_id] = session
    return session


async def process_response(session_id: str, answers: list[dict]) -> InterviewSession:
    """ユーザーの回答を処理し、追加質問があれば生成。"""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError("Session not found")
    session.answers.extend(answers)
    return session


async def finalize(session_id: str) -> SpecDocument:
    """インタビュー終了。AIが不足分を補完してSpec生成。"""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError("Session not found")

    qa_text = "\n".join(
        f"Q: {q.question}\nA: {a.get('answer', '未回答')}"
        for q, a in zip(session.questions, session.answers)
    )

    prompt = f"""以下のインタビュー結果から最終仕様書を生成してください。

元の依頼: {session.user_input}

ヒアリング結果:
{qa_text}

以下のJSON形式で返してください:
{{
  "requirements": ["要件1", "要件2"],
  "constraints": ["制約1"],
  "priorities": ["優先1"],
  "acceptance_criteria": ["基準1"],
  "ai_assumptions": ["AIが補完した前提1"]
}}

回答が不足している部分は、合理的に補完し ai_assumptions に記録してください。
JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    data = json.loads(content.strip())
    session.status = "finalized"
    return SpecDocument(**data)
```

---

## ステップ 3.12 — Task Orchestrator + Cost Guard + Quality SLA + Re-Propose（orchestrator/）

### 3.10.1 — orchestrator/models.py

```python
"""Orchestrator の Pydantic モデル定義。"""

from typing import Optional
from pydantic import BaseModel


class OrchestrationStep(BaseModel):
    """実行計画の 1 ステップ。"""
    step_id: str
    skill_name: str
    input_mapping: dict = {}  # 他ステップの出力をどう引用するか
    depends_on: list[str] = []  # 依存する step_id
    status: str = "pending"  # pending | running | completed | failed
    output: Optional[dict] = None


class OrchestrationPlan(BaseModel):
    """実行計画全体。"""
    intent: str  # ユーザーの意図を要約
    steps: list[OrchestrationStep]


class OrchestrationResult(BaseModel):
    """Orchestration の最終結果。"""
    plan: OrchestrationPlan
    step_results: list[dict] = []
    integrated_output: str = ""
    judge_result: Optional[dict] = None
    status: str = "pending"  # pending | running | completed | needs_review | approved
```

### 3.10.2 — orchestrator/planner.py

```python
"""Planner — ユーザーの意図を分析し、実行計画を生成。"""

import json
from app.gateway import call_llm
from app.skills.framework import SkillRegistry
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep


async def plan(user_input: str, registry: SkillRegistry) -> OrchestrationPlan:
    """ユーザー入力から実行計画を生成。"""
    available = registry.list_skills()
    skills_desc = "\n".join(
        f"- {s.name}: {s.description} (入力: {json.dumps(s.input_schema, ensure_ascii=False)})"
        for s in available
    )

    prompt = f"""あなたは ZPCOS の Task Orchestrator です。
ユーザーの指示を分析し、利用可能な Skill を使った実行計画を生成してください。

ユーザーの指示: {user_input}

利用可能な Skill:
{skills_desc}

以下の JSON 形式で返してください:
```json
{{
  "intent": "ユーザーの意図を1文で要約",
  "steps": [
    {{
      "step_id": "step_1",
      "skill_name": "skill-name",
      "input_mapping": {{"param": "value or $step_N.output.field"}},
      "depends_on": []
    }}
  ]
}}
```

ルール:
- 並列実行可能なステップは depends_on を空にする
- 前のステップの結果が必要な場合は depends_on に step_id を入れる
- input_mapping で $step_N.output.field と書くと、そのステップの出力を参照
- 利用可能な Skill だけを使う（無い機能は含めない）

JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="think",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]

    data = json.loads(content.strip())
    steps = [OrchestrationStep(**s) for s in data["steps"]]
    return OrchestrationPlan(intent=data["intent"], steps=steps)
```

### 3.10.3 — orchestrator/integrator.py

```python
"""Integrator — 複数 Skill の出力を統合して最終レポートを生成。"""

import json
from app.gateway import call_llm


async def integrate(step_results: list[dict], intent: str) -> str:
    """複数の Skill 出力を統合。"""
    results_text = "\n\n".join(
        f"## {r.get('skill_name', 'unknown')}\n{json.dumps(r.get('output', {}), ensure_ascii=False, indent=2)}"
        for r in step_results
    )

    prompt = f"""以下は複数の AI Skill が実行した分析結果です。
ユーザーの目的に対する包括的な回答を作成してください。

ユーザーの目的: {intent}

各 Skill の実行結果:
{results_text}

指示:
- 各分析結果を統合し、一貫したレポートにまとめる
- 具体的なアクションプランを含める
- 優先順位をつける
- 日本語で記述"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    return response.choices[0].message.content
```

### 3.10.4 — orchestrator/orchestrator.py

```python
"""Task Orchestrator — ZPCOS の司令塔。"""

import asyncio
from typing import Optional

from app.orchestrator.models import OrchestrationPlan, OrchestrationResult
from app.orchestrator.planner import plan
from app.orchestrator.integrator import integrate
from app.skills.framework import SkillRegistry
from app.judge.pipeline import judge
from app.state.machine import (
    create_task, transition_task, update_task_data,
)


async def orchestrate(
    user_input: str,
    registry: SkillRegistry,
) -> OrchestrationResult:
    """自然言語の指示から Skill を選択・実行・統合する。"""

    # 1. Plan 生成
    execution_plan = await plan(user_input, registry)

    result = OrchestrationResult(
        plan=execution_plan,
        status="running",
    )

    # 2. 依存関係に基づいて実行
    completed: dict[str, dict] = {}  # step_id → output

    # トポロジカルソートで実行順を決定
    remaining = list(execution_plan.steps)
    while remaining:
        # 依存が全て完了しているステップを抽出
        ready = [
            s for s in remaining
            if all(dep in completed for dep in s.depends_on)
        ]
        if not ready:
            # デッドロック検出
            break

        # 並列実行
        async def _execute_step(step):
            skill = registry.get_skill(step.skill_name)
            if not skill:
                return {"step_id": step.step_id, "skill_name": step.skill_name, "error": "Skill not found"}

            # input_mapping を解決
            resolved_input = {}
            for key, val in step.input_mapping.items():
                if isinstance(val, str) and val.startswith("$"):
                    # $step_N.output.field 形式を解決
                    parts = val[1:].split(".")
                    ref_step_id = parts[0]
                    if ref_step_id in completed:
                        ref_output = completed[ref_step_id]
                        for p in parts[1:]:
                            ref_output = ref_output.get(p, ref_output) if isinstance(ref_output, dict) else ref_output
                        resolved_input[key] = ref_output
                else:
                    resolved_input[key] = val

            try:
                output = await skill.execute(resolved_input)
                return {"step_id": step.step_id, "skill_name": step.skill_name, "output": output}
            except Exception as e:
                return {"step_id": step.step_id, "skill_name": step.skill_name, "error": str(e)}

        step_outputs = await asyncio.gather(*[_execute_step(s) for s in ready])

        for so in step_outputs:
            completed[so["step_id"]] = so.get("output", {})
            result.step_results.append(so)
            remaining = [s for s in remaining if s.step_id != so["step_id"]]

    # 3. 統合レポート生成
    result.integrated_output = await integrate(result.step_results, execution_plan.intent)

    # 4. Judge パイプライン
    judge_result = await judge(result.integrated_output, context=user_input)
    result.judge_result = judge_result.model_dump()

    # 5. 状態を human_review に
    result.status = "needs_review"

    return result
```

`orchestrator/__init__.py` を更新:

```python
"""Task Orchestrator — ZPCOS の司令塔。"""
from app.orchestrator.orchestrator import orchestrate  # noqa: F401
from app.orchestrator.models import OrchestrationResult, OrchestrationPlan  # noqa: F401
```

### 3.12.5 — orchestrator/cost_guard.py ★v11.1

```python
"""Cost Guard — 実行前のコスト見積り・最適化。"""

from pydantic import BaseModel
from app.orchestrator.models import OrchestrationPlan


class CostEstimate(BaseModel):
    total_api_calls: int
    estimated_tokens: int
    estimated_cost_usd: float
    estimated_time_seconds: int
    model_breakdown: list[dict] = []
    budget_exceeded: bool = False
    alternative_plan_suggested: bool = False


# モデル別コスト概算（1Kトークンあたり USD、2026年3月時点）
MODEL_COSTS = {
    "fast": 0.0001,
    "think": 0.002,
    "quality": 0.005,
    "free": 0.0,
    "reason": 0.001,
    "value": 0.0005,
}


async def estimate_cost(
    plan: OrchestrationPlan,
    quality_mode: str = "balanced",
    budget_limit_usd: float = 1.0,
) -> CostEstimate:
    """Plan のコストを見積り。"""
    steps = len(plan.steps)
    # 各ステップで使うモデルを推定
    if quality_mode == "fastest":
        model = "fast"
        judge_calls = 0
    elif quality_mode == "high_quality":
        model = "quality"
        judge_calls = steps * 3 * 2  # 3モデル×2回
    else:  # balanced
        model = "fast"
        judge_calls = steps * 3

    skill_calls = steps
    total_calls = skill_calls + judge_calls + 2  # +2 = plan生成 + 統合
    est_tokens = total_calls * 2000  # 1呼び出し平均2000トークン
    cost = est_tokens / 1000 * MODEL_COSTS.get(model, 0.001)

    return CostEstimate(
        total_api_calls=total_calls,
        estimated_tokens=est_tokens,
        estimated_cost_usd=round(cost, 4),
        estimated_time_seconds=total_calls * 3,
        budget_exceeded=cost > budget_limit_usd,
    )
```

### 3.12.6 — orchestrator/quality_sla.py ★v11.1

```python
"""Quality SLA Selector — 品質モード選択。"""

from enum import Enum


class QualityMode(str, Enum):
    FASTEST = "fastest"      # fast モデルのみ、Judge スキップ
    BALANCED = "balanced"    # fast + quality、Two-stage Judge
    HIGH_QUALITY = "high_quality"  # quality + reason、Full Judge ×2


def get_model_for_mode(mode: QualityMode, task_complexity: str = "normal") -> str:
    """品質モードとタスク複雑度からモデルグループを決定。"""
    if mode == QualityMode.FASTEST:
        return "fast"
    elif mode == QualityMode.HIGH_QUALITY:
        return "quality" if task_complexity == "normal" else "reason"
    else:  # BALANCED
        return "fast" if task_complexity == "simple" else "quality"


def should_run_judge(mode: QualityMode) -> bool:
    """このモードで Judge を実行するか。"""
    return mode != QualityMode.FASTEST
```

### 3.12.7 — orchestrator/repropose.py ★v11.1

```python
"""Re-Propose — 差し戻しではなく再提案。"""

import json
from enum import Enum
from pydantic import BaseModel
from app.gateway import call_llm
from app.orchestrator.models import OrchestrationPlan


class ReExecuteMode(str, Enum):
    FULL_REGENERATE = "full_regenerate"
    FROM_STEP_N = "from_step_n"
    PLAN_MODIFY = "plan_modify"


class ChangeRequest(BaseModel):
    mode: ReExecuteMode
    from_step: str | None = None  # FROM_STEP_N の場合
    feedback: str  # ユーザーのフィードバック
    modifications: dict = {}  # 具体的な変更内容


class PlanDiff(BaseModel):
    original_plan: dict
    modified_plan: dict
    changes: list[str]


async def repropose(
    original_plan: OrchestrationPlan,
    change_request: ChangeRequest,
) -> OrchestrationPlan:
    """Change Request に基づいて Plan を再提案。"""
    prompt = f"""元の実行計画を、ユーザーのフィードバックに基づいて修正してください。

元の計画:
{original_plan.model_dump_json(indent=2)}

ユーザーのフィードバック: {change_request.feedback}
修正モード: {change_request.mode.value}

修正後の計画を同じJSON形式で返してください。JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="think",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    data = json.loads(content.strip())
    from app.orchestrator.models import OrchestrationStep
    steps = [OrchestrationStep(**s) for s in data.get("steps", [])]
    return OrchestrationPlan(intent=data.get("intent", original_plan.intent), steps=steps)


def compute_diff(original: OrchestrationPlan, modified: OrchestrationPlan) -> PlanDiff:
    """Plan の差分を計算。"""
    orig_steps = {s.step_id: s.skill_name for s in original.steps}
    mod_steps = {s.step_id: s.skill_name for s in modified.steps}
    changes = []
    for sid, skill in mod_steps.items():
        if sid not in orig_steps:
            changes.append(f"追加: {sid} ({skill})")
        elif orig_steps[sid] != skill:
            changes.append(f"変更: {sid} {orig_steps[sid]} → {skill}")
    for sid in orig_steps:
        if sid not in mod_steps:
            changes.append(f"削除: {sid}")
    return PlanDiff(
        original_plan=original.model_dump(),
        modified_plan=modified.model_dump(),
        changes=changes,
    )
```

---

## ステップ 3.13 — Knowledge Refresh + Model Catalog Auto-Update ★v11.1

### state/knowledge.py

```python
"""Knowledge Refresh — 最新情報の継続更新。MVP では手動トリガー。"""

from pydantic import BaseModel


class KnowledgeSource(BaseModel):
    id: str
    name: str
    url: str = ""
    refresh_interval_hours: int = 24


class KnowledgeDiff(BaseModel):
    source_id: str
    summary: str
    importance: str  # high | medium | low
    adopted: bool = False


# MVP: ソースリストのインメモリ管理
_sources: list[KnowledgeSource] = []


async def register_source(source: KnowledgeSource) -> None:
    _sources.append(source)


async def list_sources() -> list[KnowledgeSource]:
    return _sources
```

### gateway/model_catalog.py

```python
"""Model Catalog Auto-Update — 最新モデル追従。"""

import json
from pathlib import Path
from pydantic import BaseModel
from app.main import resource_path


class ModelEntry(BaseModel):
    model_name: str
    model_id: str
    status: str = "active"  # active | deprecated | failed


async def load_current_catalog() -> list[ModelEntry]:
    """providers.json から現在のカタログを読み込み。"""
    p = resource_path("gateway/providers.json")
    with open(p, encoding="utf-8") as f:
        config = json.load(f)
    return [
        ModelEntry(
            model_name=m["model_name"],
            model_id=m["litellm_params"]["model"],
        )
        for m in config["models"]
    ]


async def check_model_health(entry: ModelEntry) -> bool:
    """モデルが正常に応答するかチェック（スモークテスト）。"""
    try:
        from app.gateway import call_llm
        response = await call_llm(
            messages=[{"role": "user", "content": "Hello"}],
            model_group=entry.model_name,
            max_tokens=10,
        )
        return True
    except Exception:
        return False
```

---

## ステップ 3.14 — main.py 全エンドポイント統合

`backend/app/main.py` を完成させてください。

以下のエンドポイントを追加:

```python
"""ZPCOS Backend — FastAPI entry point（完成版）。"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


def resource_path(relative_path: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時の初期化。"""
    from app.auth.authhub import load_connectors
    from app.gateway import init_gateway
    from app.state import init_db
    from app.skills import SkillRegistry

    load_connectors()
    await init_db()
    await init_gateway()  # キー無しなら False だが問題なし

    # Skill Registry をアプリ state に保存
    registry = SkillRegistry()
    registry.scan_builtins(resource_path("skills/builtins"))
    app.state.skill_registry = registry

    yield


app = FastAPI(
    title="ZPCOS Backend",
    version="0.1.0",
    description="Zero-Prompt Cross-model Orchestration System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 認証ガード ---
async def require_auth(request: Request):
    """OpenRouter 未認証時は 401。"""
    from app.auth import openrouter_oauth
    status = await openrouter_oauth.get_auth_status()
    if not status.get("authenticated"):
        raise HTTPException(401, "OpenRouter authentication required")


# --- Auth ルーター登録 ---
from app.auth.authhub import router as auth_router  # noqa: E402
app.include_router(auth_router)


# --- Health ---
@app.get("/api/health")
async def health_check():
    from app.gateway import is_ready
    from app.auth import openrouter_oauth
    status = await openrouter_oauth.get_auth_status()
    return {
        "status": "ok",
        "version": "0.1.0",
        "authenticated": status.get("authenticated", False),
        "gateway_ready": is_ready(),
    }


# --- Chat（直接 LLM 対話）---
class ChatRequest(BaseModel):
    messages: list[dict]
    model_group: str = "fast"

@app.post("/api/chat", dependencies=[Depends(require_auth)])
async def chat(req: ChatRequest):
    from app.gateway import call_llm
    response = await call_llm(req.messages, req.model_group)
    return {"content": response.choices[0].message.content}


# --- Orchestrate（★v11: 司令塔）---
class OrchestrateRequest(BaseModel):
    input: str

@app.post("/api/orchestrate", dependencies=[Depends(require_auth)])
async def orchestrate_endpoint(req: OrchestrateRequest, request: Request):
    from app.orchestrator import orchestrate
    registry = request.app.state.skill_registry
    result = await orchestrate(req.input, registry)
    return result.model_dump()


# --- Judge ---
class JudgeRequest(BaseModel):
    text: str
    context: str = ""

@app.post("/api/judge", dependencies=[Depends(require_auth)])
async def judge_endpoint(req: JudgeRequest):
    from app.judge import judge
    result = await judge(req.text, req.context)
    return result.model_dump()


# --- Tasks ---
class CreateTaskRequest(BaseModel):
    skill_name: str
    input_data: dict

@app.post("/api/tasks", dependencies=[Depends(require_auth)])
async def create_task_endpoint(req: CreateTaskRequest):
    from app.state import create_task
    task = await create_task(req.skill_name, req.input_data)
    return task.model_dump()

@app.get("/api/tasks/{task_id}", dependencies=[Depends(require_auth)])
async def get_task_endpoint(task_id: str):
    from app.state import get_task
    task = await get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.model_dump()

class TransitionRequest(BaseModel):
    trigger: str

@app.post("/api/tasks/{task_id}/transition", dependencies=[Depends(require_auth)])
async def transition_task_endpoint(task_id: str, req: TransitionRequest):
    from app.state import transition_task
    task = await transition_task(task_id, req.trigger)
    return task.model_dump()


# --- Skills ---
@app.get("/api/skills", dependencies=[Depends(require_auth)])
async def list_skills(request: Request):
    registry = request.app.state.skill_registry
    return [s.model_dump() for s in registry.list_skills()]

class ExecuteSkillRequest(BaseModel):
    skill_name: str
    input: dict

@app.post("/api/skills/execute", dependencies=[Depends(require_auth)])
async def execute_skill(req: ExecuteSkillRequest, request: Request):
    registry = request.app.state.skill_registry
    skill = registry.get_skill(req.skill_name)
    if not skill:
        raise HTTPException(404, f"Skill '{req.skill_name}' not found")
    result = await skill.execute(req.input)
    return result

class GenerateSkillRequest(BaseModel):
    description: str

@app.post("/api/skills/generate", dependencies=[Depends(require_auth)])
async def generate_skill_endpoint(req: GenerateSkillRequest):
    from app.engine.skill_generator import generate_skill
    result = await generate_skill(req.description)
    return result.model_dump()


# --- Settings ---
@app.get("/api/settings", dependencies=[Depends(require_auth)])
async def get_settings():
    return {"credit_limit": 5.0, "usage_limit_type": "monthly"}

@app.put("/api/settings", dependencies=[Depends(require_auth)])
async def update_settings():
    return {"status": "ok"}


# --- Entry point ---
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18234, reload=False, workers=1)
```

### v11.1 追加エンドポイント（main.py に追記）

以下のエンドポイントも main.py に追加してください:

```python
# --- Design Interview（★v11.1）---
class InterviewStartRequest(BaseModel):
    input: str

@app.post("/api/interview/start", dependencies=[Depends(require_auth)])
async def interview_start(req: InterviewStartRequest):
    from app.interview.interviewer import start_interview
    session = await start_interview(req.input)
    return session.model_dump()

class InterviewRespondRequest(BaseModel):
    session_id: str
    answers: list[dict]

@app.post("/api/interview/respond", dependencies=[Depends(require_auth)])
async def interview_respond(req: InterviewRespondRequest):
    from app.interview.interviewer import process_response
    session = await process_response(req.session_id, req.answers)
    return session.model_dump()

@app.post("/api/interview/finalize", dependencies=[Depends(require_auth)])
async def interview_finalize(req: dict):
    from app.interview.interviewer import finalize
    spec = await finalize(req["session_id"])
    return spec.model_dump()


# --- Orchestrate 拡張（★v11.1）---
@app.post("/api/orchestrate/{oid}/approve-plan", dependencies=[Depends(require_auth)])
async def approve_plan(oid: str):
    """Plan 承認 → 実行開始。"""
    # TODO: Plan承認→実行トリガー
    return {"status": "approved", "orchestration_id": oid}

class ReproposeRequest(BaseModel):
    feedback: str
    mode: str = "plan_modify"

@app.post("/api/orchestrate/{oid}/repropose", dependencies=[Depends(require_auth)])
async def repropose_endpoint(oid: str, req: ReproposeRequest):
    from app.orchestrator.repropose import ChangeRequest, ReExecuteMode, repropose
    # TODO: 元のPlanを取得して再提案
    return {"status": "reproposed", "orchestration_id": oid}

@app.get("/api/orchestrate/{oid}/cost", dependencies=[Depends(require_auth)])
async def get_cost(oid: str):
    from app.orchestrator.cost_guard import CostEstimate
    # TODO: 該当OrchestratorのPlanからコスト見積り
    return {"orchestration_id": oid, "estimate": None}

@app.get("/api/orchestrate/{oid}/diff", dependencies=[Depends(require_auth)])
async def get_diff(oid: str):
    return {"orchestration_id": oid, "diff": None}


# --- Skill Gaps（★v11.1）---
@app.get("/api/skills/gaps", dependencies=[Depends(require_auth)])
async def get_skill_gaps(request: Request):
    return {"gaps": []}
```

---

## ステップ 3.15 — Self-Healing DAG（orchestrator/self_healing.py）★v11.2

`backend/app/orchestrator/self_healing.py` を作成:

```python
"""Self-Healing DAG — 失敗からの自律的回復エンジン。
Judge差し戻しやSkill実行エラー時に、AI組織が自律的にDAGを再構築してリトライする。
「AIが失敗から学び、リアルタイムに実行計画を組み替えて目的を達成する」自己修復機能。
"""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel

from app.state.failure import FailureRecord, FailureType, suggest_recovery
from app.state.experience import get_relevant_experiences


class HealStrategy(str, Enum):
    RETRY_SAME = "retry_same"       # 同じSkillを別モデルで再実行
    SWAP_SKILL = "swap_skill"       # 代替Skillに切り替え
    REPLAN = "replan"               # DAG全体を再生成
    DECOMPOSE = "decompose"         # 失敗ステップをサブステップに分割


class HealAttempt(BaseModel):
    attempt_number: int
    strategy: HealStrategy
    original_error: str
    new_plan_id: str | None = None
    result: str  # success | failed | escalated
    reasoning: str = ""  # なぜこの戦略を選んだか
    timestamp: datetime = datetime.now()


MAX_HEAL_ATTEMPTS = 3

# 試行履歴（MVP: インメモリ。将来的にはaiosqlite永続化）
_heal_history: dict[str, list[HealAttempt]] = {}


async def choose_strategy(failure: FailureRecord, attempt_number: int) -> HealStrategy:
    """失敗の種類と過去の経験から最適な回復戦略を選択。"""
    # 過去の成功体験を参照
    experiences = await get_relevant_experiences(f"heal_{failure.failure_type.value}")

    # 失敗タイプに基づく基本戦略
    strategy_map = {
        FailureType.AUTH_ERROR: HealStrategy.RETRY_SAME,
        FailureType.RATE_LIMIT: HealStrategy.SWAP_SKILL,
        FailureType.TIMEOUT: HealStrategy.RETRY_SAME,
        FailureType.EVIDENCE_WEAK: HealStrategy.REPLAN,
        FailureType.CONTRADICTION: HealStrategy.REPLAN,
        FailureType.INPUT_MISSING: HealStrategy.DECOMPOSE,
        FailureType.SPEC_CHANGE: HealStrategy.REPLAN,
    }

    base_strategy = strategy_map.get(failure.failure_type, HealStrategy.REPLAN)

    # 2回目以降はエスカレーション（より大きな変更を試みる）
    if attempt_number >= 2:
        escalation = {
            HealStrategy.RETRY_SAME: HealStrategy.SWAP_SKILL,
            HealStrategy.SWAP_SKILL: HealStrategy.REPLAN,
            HealStrategy.REPLAN: HealStrategy.DECOMPOSE,
            HealStrategy.DECOMPOSE: HealStrategy.DECOMPOSE,
        }
        base_strategy = escalation.get(base_strategy, HealStrategy.DECOMPOSE)

    return base_strategy


async def self_heal(orchestration_id: str, failure: FailureRecord) -> HealAttempt:
    """失敗からの自律回復を試みる。"""
    history = _heal_history.get(orchestration_id, [])
    attempt_number = len(history) + 1

    if attempt_number > MAX_HEAL_ATTEMPTS:
        attempt = HealAttempt(
            attempt_number=attempt_number,
            strategy=HealStrategy.REPLAN,
            original_error=str(failure),
            result="escalated",
            reasoning=f"最大試行回数（{MAX_HEAL_ATTEMPTS}回）超過。人間にエスカレーション。",
        )
        history.append(attempt)
        _heal_history[orchestration_id] = history
        return attempt

    strategy = await choose_strategy(failure, attempt_number)
    recovery = await suggest_recovery(failure)

    attempt = HealAttempt(
        attempt_number=attempt_number,
        strategy=strategy,
        original_error=str(failure),
        result="failed",  # 実際の実行後に更新
        reasoning=f"失敗タイプ: {failure.failure_type.value}, "
                  f"回復可能: {failure.recoverable}, "
                  f"選択戦略: {strategy.value}",
    )

    # TODO: 実際のDAG再構築・再実行ロジック
    # strategy に基づいて orchestrator.repropose を呼び出す

    history.append(attempt)
    _heal_history[orchestration_id] = history
    return attempt


async def get_heal_history(orchestration_id: str) -> list[HealAttempt]:
    """自己修復の試行履歴を返す。"""
    return _heal_history.get(orchestration_id, [])
```

---

## ステップ 3.16 — Skill Registry 基盤（skills/registry.py）★v11.2

`backend/app/skills/registry.py` を作成:

```python
"""Skill Registry — コミュニティ Skill エコシステム基盤。
開発した Skill をパッケージマネージャのように共有・インストールできる仕組み。
MVP では GitHub リポジトリベース。将来的に専用レジストリサーバーを構築。
"""

import json
import shutil
import zipfile
from pathlib import Path
from pydantic import BaseModel

from app.main import resource_path


class SkillPackage(BaseModel):
    name: str
    version: str
    author: str
    description: str
    downloads: int = 0
    rating: float = 0.0
    tags: list[str] = []
    source_url: str = ""


# MVP: ローカルレジストリ（JSONファイルベース）
_registry_path = Path.home() / ".zpcos" / "skill_registry.json"
_installed_dir = Path.home() / ".zpcos" / "community_skills"


def _load_registry() -> list[SkillPackage]:
    """レジストリインデックスを読み込み。"""
    if not _registry_path.exists():
        return []
    data = json.loads(_registry_path.read_text(encoding="utf-8"))
    return [SkillPackage(**p) for p in data]


def _save_registry(packages: list[SkillPackage]) -> None:
    """レジストリインデックスを保存。"""
    _registry_path.parent.mkdir(parents=True, exist_ok=True)
    _registry_path.write_text(
        json.dumps([p.model_dump() for p in packages], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def search_registry(query: str) -> list[SkillPackage]:
    """レジストリからSkillを検索。"""
    packages = _load_registry()
    query_lower = query.lower()
    return [
        p for p in packages
        if query_lower in p.name.lower()
        or query_lower in p.description.lower()
        or any(query_lower in tag.lower() for tag in p.tags)
    ]


async def publish_skill(skill_dir: str, author: str) -> SkillPackage:
    """Skillをパッケージ化して公開。"""
    skill_path = Path(skill_dir)
    skill_json = json.loads((skill_path / "SKILL.json").read_text(encoding="utf-8"))

    package = SkillPackage(
        name=skill_json["name"],
        version=skill_json["version"],
        author=author,
        description=skill_json["description"],
        tags=skill_json.get("tags", []),
    )

    # レジストリに追加
    packages = _load_registry()
    packages = [p for p in packages if p.name != package.name]  # 重複除去
    packages.append(package)
    _save_registry(packages)

    return package


async def install_skill(skill_name: str) -> bool:
    """コミュニティSkillをローカルにインストール。"""
    packages = _load_registry()
    target = next((p for p in packages if p.name == skill_name), None)
    if not target:
        return False

    # TODO: 実際のダウンロード・セキュリティバリデーション・インストール
    _installed_dir.mkdir(parents=True, exist_ok=True)
    return True


async def get_popular() -> list[SkillPackage]:
    """人気Skill一覧をダウンロード数・評価順で返す。"""
    packages = _load_registry()
    return sorted(packages, key=lambda p: (p.downloads, p.rating), reverse=True)[:20]
```

---

## ステップ 3.17 — main.py に v11.2 エンドポイント追加

以下のエンドポイントも main.py に追加してください:

```python
# --- Self-Healing DAG（★v11.2）---
@app.post("/api/orchestrate/{oid}/self-heal", dependencies=[Depends(require_auth)])
async def self_heal_endpoint(oid: str):
    from app.orchestrator.self_healing import self_heal
    from app.state.failure import classify_failure
    # 直近のエラーを取得してSelf-Healingを試行
    failure = await classify_failure("Last execution error")
    attempt = await self_heal(oid, failure)
    return attempt.model_dump()

@app.get("/api/orchestrate/{oid}/heal-history", dependencies=[Depends(require_auth)])
async def heal_history_endpoint(oid: str):
    from app.orchestrator.self_healing import get_heal_history
    history = await get_heal_history(oid)
    return [h.model_dump() for h in history]


# --- Skill Registry（★v11.2）---
@app.get("/api/registry/search", dependencies=[Depends(require_auth)])
async def registry_search(q: str = ""):
    from app.skills.registry import search_registry
    results = await search_registry(q)
    return [r.model_dump() for r in results]

@app.post("/api/registry/publish", dependencies=[Depends(require_auth)])
async def registry_publish(req: dict):
    from app.skills.registry import publish_skill
    result = await publish_skill(req["skill_dir"], req.get("author", "anonymous"))
    return result.model_dump()

@app.post("/api/registry/install", dependencies=[Depends(require_auth)])
async def registry_install(req: dict):
    from app.skills.registry import install_skill
    success = await install_skill(req["skill_name"])
    return {"success": success}

@app.get("/api/registry/popular", dependencies=[Depends(require_auth)])
async def registry_popular():
    from app.skills.registry import get_popular
    results = await get_popular()
    return [r.model_dump() for r in results]
```

---

## ステップ 3.18 — 最終確認

```powershell
cd zpcos/backend

# 1. サーバー起動
uv run python -m app.main

# 2. 別ターミナルで確認
curl http://localhost:18234/api/health
# → {"status":"ok","version":"0.1.0","authenticated":false,"gateway_ready":false}

curl http://localhost:18234/api/skills
# → 401 Unauthorized（認証ガードが動作）

curl -X POST http://localhost:18234/api/auth/status
# → {"authenticated":false}

# 3. コミット
cd ..
git add -A
git commit -m "feat: implement complete backend (Section 3 v11.2)"
```

全確認 PASS でセクション 3 完了。
