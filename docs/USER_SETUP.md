# ユーザーセットアップガイド

> 利用ユーザーが設定・構成する項目の一覧
>
> 最終更新: 2026-03-18

---

## 1. ワークスペース環境（初期設定）

ZEO は**セキュリティファースト**で設計されています。初期状態では、AI エージェントは**完全に隔離されたワークスペース**で動作し、ローカルファイルやクラウドストレージには一切アクセスできません。

### 初期状態（デフォルト）

```
ワークスペース:           隔離環境（内部ストレージのみ）
ローカルファイルアクセス:  無効
クラウドストレージ接続:    無効
ナレッジソース:            ユーザーがアップロードしたファイルのみ
```

AI エージェントが使用するナレッジ・ファイルは、ユーザーがこの隔離環境にアップロードしたものだけです。ローカルのフォルダやクラウド（Google ドライブ等）のデータには触れません。

### ワークスペースの仕組み

```
┌─────────────────────────────────────────┐
│  隔離ワークスペース（内部ストレージ）       │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  │
│  │ ナレッジ  │  │ 成果物   │  │ 一時   │  │
│  │ (参照用)  │  │ (出力)   │  │ ファイル│  │
│  └─────────┘  └─────────┘  └────────┘  │
│                                         │
│  ※ ユーザーがアップロードしたファイルのみ    │
│  ※ AI はここからのみ読み書き可能           │
└─────────────────────────────────────────┘
          ↑ アップロード    ↓ エクスポート
      ────────────────────────────────
          ↕ ユーザーが許可した場合のみ
┌─────────────────┐  ┌─────────────────┐
│ ローカルフォルダ   │  │ クラウドストレージ  │
│ (デフォルト: 無効) │  │ (デフォルト: 無効)  │
└─────────────────┘  └─────────────────┘
```

---

## 2. ローカルフォルダ・クラウドストレージへのアクセス許可

ユーザーが必要に応じてアクセス範囲を拡張できます。

### GUI で設定

設定画面 > セキュリティ > ワークスペース環境 で以下を設定:

- **ローカルフォルダの追加**: ファイルピッカーで許可フォルダを選択
- **クラウドストレージの接続**: Google ドライブ / OneDrive / Dropbox 等を接続
- **保存先の指定**: 成果物の保存先を「内部ストレージ」「ローカル」「クラウド」から選択

### CLI / TUI で設定

```bash
# ローカルフォルダへのアクセスを許可
zero-employee config set WORKSPACE_LOCAL_ACCESS_ENABLED true
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/documents,/home/user/projects"

# クラウドストレージへのアクセスを許可
zero-employee config set WORKSPACE_CLOUD_ACCESS_ENABLED true
zero-employee config set WORKSPACE_CLOUD_PROVIDERS '["google_drive"]'

# 成果物の保存先を設定
zero-employee config set WORKSPACE_STORAGE_LOCATION internal  # internal / local / cloud

# データ転送ポリシーを変更（ローカル・クラウドアクセスを許可する場合）
zero-employee config set SECURITY_TRANSFER_POLICY restricted
```

### API 経由

```bash
# ワークスペース設定の確認
GET /api/v1/security/workspace

# ワークスペース設定の更新
PUT /api/v1/security/workspace
{
  "local_access_enabled": true,
  "cloud_access_enabled": false,
  "allowed_local_paths": ["/home/user/documents"],
  "cloud_providers": [],
  "storage_location": "internal"
}

# サンドボックスの許可パスを追加
POST /api/v1/security/sandbox/allowed-paths
{ "path": "/home/user/documents" }
```

---

## 3. 業務ごとの環境・権限カスタマイズ

システム全体の設定とは別に、**業務（チケット）ごとに環境・権限・ナレッジの使用範囲を個別に指定**できます。

### チャットで指示する場合

AI にチャットで業務ごとの環境を指示できます:

```
「このタスクではローカルの /home/user/project-x フォルダも参照して」
「Google ドライブの共有フォルダにある資料も使ってほしい」
「この業務の成果物はローカルの /home/user/output に保存して」
```

**重要**: チャットでの指示がシステム設定と異なる場合、AI は計画段階でユーザーに許可を求めます。

例:
```
AI: 「この業務では /home/user/project-x へのアクセスが必要ですが、
     現在のワークスペース設定ではローカルアクセスが無効です。
     このタスクに限り、以下のアクセスを許可しますか？
     - 読み取り: /home/user/project-x
     - 書き込み: /home/user/output
     [許可] [拒否] [設定を恒久変更]」
```

### API 経由でタスク単位の権限を設定

```bash
POST /api/v1/tasks/{task_id}/workspace-override
{
  "additional_local_paths": ["/home/user/project-x"],
  "additional_cloud_sources": ["google_drive://shared/project-x"],
  "storage_location": "local",
  "output_path": "/home/user/output"
}
```

---

## 4. ファイルサンドボックス

AI がアクセスできるフォルダを制限する追加設定です。

### レベル

| レベル | 説明 | 初期設定 |
|--------|------|---------|
| **STRICT** | 許可リストのフォルダのみアクセス可能 | **初期設定** |
| MODERATE | 許可リスト + 一般的なファイル拡張子の読み取り | - |
| PERMISSIVE | 禁止リスト以外すべて（非推奨） | - |

```bash
# サンドボックスレベルを設定
zero-employee config set SANDBOX_LEVEL strict

# 許可フォルダを追加
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/projects,/tmp/work"
```

---

## 5. データ保護（アップロード・ダウンロード制御）

| ポリシー | 説明 | 初期設定 |
|---------|------|---------|
| **LOCKDOWN** | 外部転送を全面禁止 | **初期設定** |
| RESTRICTED | ユーザーが許可した宛先のみ | - |
| PERMISSIVE | 禁止リスト以外すべて（非推奨） | - |

```bash
# 転送ポリシーを設定
zero-employee config set SECURITY_TRANSFER_POLICY lockdown

# アップロードを有効化（承認必須のまま）
zero-employee config set SECURITY_UPLOAD_ENABLED true
zero-employee config set SECURITY_UPLOAD_REQUIRE_APPROVAL true
```

---

## 6. Ollama ローカル LLM セットアップ

API キー不要で完全ローカル動作させる場合:

```bash
# 1. Ollama をインストール
curl -fsSL https://ollama.com/install.sh | sh

# 2. 推奨モデルをダウンロード
zero-employee pull qwen3:8b        # 軽量 (推奨)
zero-employee pull qwen3:32b       # 高品質
zero-employee pull deepseek-coder-v2  # コーディング特化

# 3. 実行モードを free に設定
zero-employee config set DEFAULT_EXECUTION_MODE free
```

---

## 7. Chrome 拡張機能のインストール

```
1. Chrome で chrome://extensions を開く
2. 右上の「デベロッパーモード」を ON
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. extensions/browser-assist/chrome-extension/ フォルダを選択
5. ZEO サーバーが起動していることを確認（http://localhost:18234）
```

---

## 8. Obsidian 連携

```bash
# Vault パスの登録（API 経由）
POST /api/v1/knowledge/remember
{
  "category": "obsidian",
  "key": "vault_path",
  "value": "/path/to/your/obsidian/vault"
}
```

Obsidian プラグイン「Local REST API」のインストールも推奨します。

---

## 設定不要で動作する機能

以下の機能は追加設定なしで利用可能です:

- Design Interview（壁打ち・要件深掘り）
- Task Orchestrator（DAG 分解・進行管理）
- Judge Layer（品質検証）
- Self-Healing DAG（自動再計画）
- Experience Memory（経験記憶）
- Skill Registry（スキル管理）
- 承認フロー・監査ログ
- PII 自動検出・マスキング
- プロンプトインジェクション防御
- ファイルサンドボックス
- メタスキル（AI の学習能力）
- A2A 双方向通信
- マーケットプレイス基盤
- チーム管理基盤
- ガバナンス・コンプライアンス基盤
- リパーパスエンジン
- ユーザー入力要求
- 成果物エクスポート（ローカル）
- E2E テストフレームワーク
- LLM レスポンスモック（テスト用）

---

## セキュリティ初期設定一覧

```
ワークスペース:           隔離環境（内部ストレージのみ）
ローカルアクセス:         無効
クラウドアクセス:         無効
サンドボックス:           STRICT（許可リストのみ）
データ転送ポリシー:       LOCKDOWN（外部転送禁止）
AI アップロード:          無効
AI ダウンロード:          無効
外部 API 呼び出し:        無効
PII 自動検出:             有効（全カテゴリ）
PII アップロードブロック: 有効
パスワード類の転送:       常にブロック
アップロード承認:         必須
ダウンロード承認:         必須
```

---

*Zero-Employee Orchestrator — ユーザーセットアップガイド*
