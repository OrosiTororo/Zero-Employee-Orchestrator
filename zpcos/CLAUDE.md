# ZPCOS — Claude Code 開発ガイド

## プロジェクト概要
ZPCOS（Zero-Prompt Cross-model Orchestration System）は、複数の LLM を自動的に
使い分け、ユーザーが AI のモデル名やパラメータを意識することなく最適な回答を得られる
Windows デスクトップアプリケーションである。

## 9層アーキテクチャ（v11.2）
1. User Layer — 自然言語で目的を伝える
2. Design Interview — 壁打ち・すり合わせで要件を深掘り
3. Task Orchestrator — タスク分解・Skill割当・進行管理 + Self-Healing DAG
4. Skill Layer — 単一目的の専門Skill + Local Context Skill（ローカルファイル分析）
5. Judge Layer — Two-stage Detection + Cross-Model Verificationで品質保証
6. Re-Propose Layer — 差し戻し時の再提案 + 動的DAG再構築
7. State & Memory — 永続的な実行環境・履歴・Experience Memory
8. Provider Interface — OpenRouter経由のLLMゲートウェイ
9. Skill Registry — コミュニティSkillの公開・検索・インストール

## 技術スタック
- バックエンド: Python 3.12 / FastAPI / uvicorn
- LLM ゲートウェイ: LiteLLM Router SDK（openrouter/ プレフィックスで全モデルアクセス）
- LLM プロバイダー: OpenRouter（OAuth PKCE 認証、ユーザー課金）
- 認証: AuthHub（OpenRouter OAuth PKCE + Google OAuth InstalledAppFlow）
- トークン保存: keyring（暗号鍵のみ）+ AES-GCM 暗号化ファイル（トークン本体）
- 状態機械: python-transitions AsyncMachine / aiosqlite 永続化
- フロントエンド: React 19 + TypeScript + Vite + shadcn/ui
- デスクトップ: Tauri v2（Rust）、Python バックエンドはサイドカー（PyInstaller .exe）
- パッケージ管理: uv（Python）、pnpm（Node.js）

## コーディング規約
- Python: ruff でフォーマット・リント、型ヒント必須、docstring は日本語可
- TypeScript: strict モード、関数コンポーネントのみ
- テスト: pytest + pytest-asyncio、テストファイルは tests/test_*.py
- エラーハンドリング: 例外は具体的にキャッチ、ログ出力必須
- 非同期: FastAPI エンドポイントは全て async def

## ポート
- FastAPI: 18234
- OpenRouter OAuth: 3000
- Google OAuth: 0（自動）

## LiteLLM モデル名規則
OpenRouter 経由モデルは openrouter/ プレフィックス必須。
エイリアス: fast, think, quality, free, reason, value
