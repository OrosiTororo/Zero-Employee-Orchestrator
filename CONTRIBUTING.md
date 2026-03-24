# Contributing to Zero-Employee Orchestrator

> 日本語 | [English](docs/en/CONTRIBUTING.md) | [中文](docs/zh/CONTRIBUTING.md)

Zero-Employee Orchestrator へのコントリビューションを歓迎します。
バグ報告、機能リクエスト、コードの改善など、どのような形でも貢献をお待ちしています。

## はじめに

1. リポジトリを Fork する
2. ブランチを作成する: `git checkout -b feature/your-feature`
3. 変更をコミットする: `git commit -m "Add your feature"`
4. プッシュする: `git push origin feature/your-feature`
5. Pull Request を作成する

## 開発環境のセットアップ

```bash
git clone https://github.com/<your-username>/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh
```

### バックエンド

```bash
cd apps/api
source .venv/bin/activate
pip install -e ".[dev]"
```

### フロントエンド

```bash
cd apps/desktop/ui
pnpm install
pnpm dev
```

## コーディング規約

### Python

- **フォーマッター / リンター**: ruff
- 型ヒント必須
- FastAPI エンドポイントは `async def`
- テスト: pytest + pytest-asyncio

### TypeScript

- strict モード
- 関数コンポーネントのみ
- Tailwind CSS でスタイリング

## Pull Request のガイドライン

- PR は小さく保つ（1 つの PR で 1 つの変更）
- 既存のテストが通ることを確認する
- 新機能にはテストを追加する
- コミットメッセージは英語で、変更内容を簡潔に記述する
- `CLAUDE.md` のコーディング規約に従う

## バグ報告

[Issues](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/issues) から報告してください。

以下の情報を含めてください:
- OS とバージョン
- 再現手順
- 期待する動作と実際の動作
- エラーログ（ある場合）

## Skill / Plugin の貢献

コミュニティ Skill や Plugin の作成・共有も大歓迎です。

- Skill: `skills/templates/` のテンプレートを参考にしてください
- Plugin: `plugins/` の既存 Plugin を参考にしてください
- 安全性チェック（16 種類の危険パターン検出）を通過する必要があります
- 個人情報・機密情報を含めないでください

## ライセンス

コントリビューションは [MIT License](LICENSE) の下で公開されます。
