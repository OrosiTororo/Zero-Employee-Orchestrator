# ZEO リポジトリ構成変更 — Claude Code 実行プロンプト

以下の指示に従い、Zero-Employee Orchestrator リポジトリをeverything-claude-code.mdのスタイルに合わせて再構成してください。

---

## 1. ディレクトリ構成の変更

### 1-1. `docs/` フォルダの作成

```bash
mkdir -p docs/ja-JP
mkdir -p docs/zh-CN
mkdir -p docs/zh-TW
mkdir -p docs/ko-KR
mkdir -p docs/pt-BR
mkdir -p docs/tr
mkdir -p docs/guides
```

### 1-2. `assets/images/` フォルダの整備

```bash
mkdir -p assets/images/guides
mkdir -p assets/images/logo
mkdir -p assets/images/screenshots
```

- `assets/logo.svg` が既存なら `assets/images/logo/` に移動
- ガイド用のヘッダー画像のプレースホルダーを3つ作成（後で実画像に差し替え）:
  - `assets/images/guides/quickstart-guide.png`
  - `assets/images/guides/architecture-guide.png`
  - `assets/images/guides/security-guide.png`

---

## 2. README.md の差し替え

ルートの `README.md` を英語メインに差し替えてください。新しい README.md の内容は、このプロンプトと同じディレクトリにある `README.md` ファイルを使用してください。

**差し替え後のチェックリスト:**

- [ ] 冒頭に言語切替リンク（English | 日本語 | 简体中文 | 繁體中文 | 한국어 | Português | Türkçe）
- [ ] GitHub バッジ群（Stars, Forks, Contributors, License, 言語バッジ）
- [ ] Guide 画像カード（テーブル形式、3列）
- [ ] What's New セクション（バージョン別変更履歴）
- [ ] Quick Start（Step 1/2/3 形式）
- [ ] What's Inside（ツリー形式ディレクトリ構成、`docs/` を含む）
- [ ] 9-Layer Architecture（ASCII図）
- [ ] Key Features（カテゴリ別テーブル）
- [ ] Security（テーブル形式）
- [ ] CLI Reference
- [ ] FAQ（`<details>` 折りたたみ）
- [ ] Star History Chart（star-history.com）
- [ ] License

---

## 3. 多言語 README の生成

以下の 6 言語の README.md を作成してください。各ファイルの冒頭に言語切替リンクを配置し、自身の言語がボールド表示になるようにしてください。

### 3-1. `docs/ja-JP/README.md`（日本語）

- 元の日本語 README の内容をベースにする
- 英語版 README の構造（バッジ、ガイドカード、What's New、FAQ 等）に合わせる
- 画像パスは相対パスで `../../assets/images/...` を使用
- リンクはルートからの相対パスで `../../USER_SETUP.md` 等

### 3-2. `docs/zh-CN/README.md`（简体中文）

- 元の中文セクションの内容をベースにする
- 英語版と同じ構造

### 3-3. `docs/zh-TW/README.md`（繁體中文）

- 簡体字版を繁體字に変換
- 台湾の用語慣習に合わせる（例: 「伺服器」「程式」等）

### 3-4. `docs/ko-KR/README.md`（한국어）

- 英語版を韓国語に翻訳
- 技術用語は韓国の開発者コミュニティで一般的な表記に合わせる

### 3-5. `docs/pt-BR/README.md`（Português do Brasil）

- 英語版をブラジルポルトガル語に翻訳
- ブラジルの表記慣習に合わせる

### 3-6. `docs/tr/README.md`（Türkçe）

- 英語版をトルコ語に翻訳

### 各言語ファイルの共通ルール

1. **冒頭の言語切替リンク**: 自分の言語をボールド、他は通常リンク

   ```
   **Language:** [English](../../README.md) | **[日本語](README.md)** | [简体中文](../zh-CN/README.md) | ...
   ```

2. **バッジ**: 英語版と同じ（バッジ自体は英語のまま）

3. **画像パス**: すべて `../../assets/images/...` に相対パスで参照

4. **内部リンク**: `../../USER_SETUP.md`, `../../SECURITY.md`, `../../LICENSE` 等

5. **コードブロック**: コマンドは翻訳しない（英語のまま）。コメントのみ各言語に翻訳

---

## 4. ガイドドキュメントの作成

### 4-1. `docs/guides/quickstart-guide.md`

英語版 README の Quick Start セクションを拡張した詳細ガイド:

- 前提条件（Python 3.12+, Node.js 20+, Docker optional）自動的に確認・インストール
- インストール方法の詳細比較（PyPI vs Source vs Docker）
- 初回起動から最初のワークフロー実行まで
- トラブルシューティング

### 4-2. `docs/guides/architecture-guide.md`

- 9 層アーキテクチャの詳細解説
- Self-Healing DAG の仕組み
- Judge Layer の Two-stage + Cross-Model 検証フロー
- Experience Memory のデータ構造と学習サイクル
- 図表を ASCII / Mermaid で記述

### 4-3. `docs/guides/security-guide.md`

- プロンプトインジェクション防御の 5 カテゴリ詳細
- 承認ゲートの 12 カテゴリ一覧
- IAM 設計（人間/AI アカウント分離）
- ファイルサンドボックスとデータ保護ポリシーの設定手順
- PII 保護の 13 カテゴリ
- 本番環境デプロイ前チェックリスト

---

## 5. ガイド画像のプレースホルダー作成

`assets/images/guides/` にプレースホルダー画像（SVG） everything-claude-code.mdのようなものを3つ作成してください。
各画像はガイドカード画像のようなスタイルで:

- 1200×630px 相当の SVG
- グラデーション背景
- タイトルテキストを中央配置
- ZEO のブランドカラーを使用

```
quickstart-guide.png  → "Quickstart Guide" + サブタイトル
architecture-guide.png → "Architecture Deep Dive" + サブタイトル
security-guide.png     → "Security Guide" + サブタイトル
```

実際には SVG で作成し、後で PNG にエクスポートすることを前提としてください。

---

## 6. 既存ファイルの更新

### 6-1. `.gitignore` に追加

```
# Guide images (generated)
# assets/images/guides/*.png は追跡対象（コミットする）
```

### 6-2. `CONTRIBUTING.md` の更新（存在する場合）

多言語 README の翻訳貢献セクションを追加:

```markdown
## Translations

We welcome translations! Current languages:
- 日本語 (`docs/ja-JP/`)
- 简体中文 (`docs/zh-CN/`)
- 繁體中文 (`docs/zh-TW/`)
- 한국어 (`docs/ko-KR/`)
- Português (`docs/pt-BR/`)
- Türkçe (`docs/tr/`)

To add a new language:
1. Create `docs/<lang-code>/README.md`
2. Translate from the English README
3. Update language links in all existing READMEs
4. Submit a PR
```

---

## 7. 実行順序

1. ディレクトリ作成（`docs/`, `assets/images/`）
2. 既存 `assets/logo.svg` の移動
3. ルート README.md の差し替え
4. ガイドドキュメント 3 本の作成
5. 多言語 README 6 本の生成
6. ガイド画像（SVG プレースホルダー）3 本の作成
7. CONTRIBUTING.md の更新
8. 最終確認: 全リンクの整合性チェック

---

## 8. 品質チェック

すべての作業完了後、以下を確認してください:

- [ ] ルート README.md の全リンクが正しいパスを指している
- [ ] 各言語 README.md の言語切替リンクが正しい相対パスになっている
- [ ] 画像パスが `assets/images/...` で統一されている
- [ ] `docs/guides/` 内のガイドからルートの他ファイルへのリンクが正しい
- [ ] コードブロック内のコマンドが翻訳されていない（コメントのみ翻訳）
- [ ] バッジの GitHub ユーザー名/リポジトリ名が `OrosiTororo/Zero-Employee-Orchestrator` になっている
- [ ] Star History の URL が正しいリポジトリを指している
