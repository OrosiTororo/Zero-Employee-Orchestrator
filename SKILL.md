# SKILL.md 作成ガイド

> Claude Code に特定の業務手順を教える「業務マニュアル」の作成方法。
> 自然言語で記述でき、実行可能なスクリプトと組み合わせて構成される。

## 概要

`SKILL.md` は Claude Code のスキルファイルであり、以下の 2 部構成で成り立つ:

1. **フロントマター（設定部分）** — 常に Claude のコンテキストに含まれる
2. **本文（指示書部分）** — スキル起動時にのみ読み込まれる

配置場所: `.claude/skills/` ディレクトリ配下

## 1. フロントマター（設定部分）

ファイル先頭に YAML フロントマターで記述する。Claude がスキルを認識・選択するための設定。

```yaml
---
name: download-sharepoint
description: SharePointからファイルをダウンロードし、ローカルに保存する
disable-model-invocation: true
---
```

| フィールド | 説明 |
|-----------|------|
| `name` | `/download-sharepoint` のようなスラッシュコマンド名 |
| `description` | Claude が会話文脈からスキルを自動選択する際の参照テキスト |
| `disable-model-invocation` | `true`: ユーザーの明示的コマンドのみで起動。副作用を伴う処理に推奨 |

## 2. 本文（指示書部分）

スキル起動時に読み込まれる具体的な指示書。対話設計（UX デザイン）を含められる。

### 記述要素

**具体的なコマンドとオプション:**
```markdown
以下のコマンドを実行してください:
`pwsh -ExecutionPolicy Bypass -File ./scripts/download-sp.ps1 --site-id $SITE_ID`
```

**STEP 形式の対話フロー:**
```markdown
## 手順

STEP 1: ユーザーにサイト ID を質問する
STEP 2: 取得するフィールドを確認する（日本語名のみ / 基本情報 / 全項目）
STEP 3: ユーザーの選択に応じてコマンドを組み立てて実行する
```

**条件分岐:**
```markdown
ユーザーの選択に応じて引数を切り替える:
- 「日本語名のみ」→ `--id` のみ
- 「基本情報」→ `--id --fields basic`
- 「全項目」→ `--id --fields all`
```

**結果のハンドリング:**
```markdown
スクリプトの JSON 出力を確認する:
- `status: "ok"` → 結果をユーザーに表示
- `status: "not_found"` → ID の確認を促す
- `status: "error"` → `hint` フィールドの内容をユーザーに案内
```

**初回セットアップ（フォールバック）:**
```markdown
## セットアップ
Playwright が未インストールの場合:
`npm install -g playwright && npx playwright install chromium`
```

## 3. スクリプトとの連携

SKILL.md はオーケストレーション（指揮）に徹し、複雑なロジックはスクリプトに委譲する。

### インターフェース設計

スクリプトからの出力は構造化 JSON を推奨:

```json
{
  "status": "ok",
  "data": { ... },
  "hint": null
}
```

```json
{
  "status": "error",
  "data": null,
  "hint": "pip install playwright を実行してください"
}
```

- `status` フィールドで Claude が結果を正確に分岐して解釈
- `hint` フィールドでエラー時の対処法を提案

## 4. ディレクトリ配置

### パターン A: スキル内に配置（自己完結・移植向き）

```
.claude/skills/
└── download-sharepoint/
    ├── SKILL.md
    └── scripts/
        └── download-sp.ps1
```

### パターン B: プロジェクトルートに配置（パイプライン・共有向き）

```
.claude/skills/
└── download-sharepoint.md
scripts/
└── download-sp.ps1
```

スクリプト間に依存関係やパイプライン的な処理フローがある場合に適している。

## 5. サンプル: 完全な SKILL.md

```markdown
---
name: fetch-user-data
description: 社内システムからユーザーデータを取得して整形する
disable-model-invocation: true
---

# ユーザーデータ取得スキル

## 手順

STEP 1: ユーザーに対象の社員 ID を質問する
STEP 2: 取得範囲を確認する
  - 「基本情報のみ」
  - 「部署・役職を含む」
  - 「全項目」
STEP 3: 以下のコマンドを実行する

`python scripts/fetch_user.py --employee-id $ID --scope $SCOPE`

## 結果の解釈

JSON 出力の `status` フィールドを確認:
- `ok` → データをユーザーに表示
- `not_found` → 社員 ID の確認を促す
- `auth_error` → 認証トークンの再設定を案内

## セットアップ

初回実行時にエラーが出た場合:
`pip install requests && python scripts/setup_auth.py`
```

## 6. Zero-Employee Orchestrator との関連

本プロジェクトのビルトイン Skill (`skills/builtin/`) は Python モジュールとして実装されているが、
Claude Code のスキルファイル (`.claude/skills/`) とは別の仕組みである。

| 種別 | 配置場所 | 形式 | 用途 |
|------|---------|------|------|
| Claude Code スキル | `.claude/skills/*.md` | SKILL.md (自然言語) | 開発者の業務自動化 |
| ZEO ビルトイン Skill | `skills/builtin/*.py` | Python モジュール | AI エージェントの専門能力 |

両方を活用することで、開発者の作業効率化と AI エージェントの能力拡張を同時に実現できる。
