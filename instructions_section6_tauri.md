# Section 6 — Tauri 統合・デスクトップ化

> 担当: Antigravity + Claude Code
> 基準文書: `Zero-Employee Orchestrator.md`
> 前提: Section 3 と Section 4 が完了していること
> 目的: ローカルファーストの実行基盤として desktop app 化する
> 完了条件: `pnpm tauri dev` でアプリ起動し、backend / frontend / local capabilities が連携すること

---

## 0. この Section の意味

Zero-Employee Orchestrator はローカル特権アクセスを価値の一部としている。  
そのため、Tauri 統合は単なる配布手段ではなく、**ローカル実行・安全な接続・ファイルアクセス補助**を成立させるための中核である。

---

## 1. Claude Code 側

- backend を sidecar として起動できるようにする
- 起動ポートを固定または検出可能にする
- ログ出力先を定義する
- 開発時と配布時で設定を分ける

最低確認:

- health endpoint が sidecar 起動後に応答する
- backend の終了で zombie process を残さない

---

## 2. Antigravity 側

- Tauri 設定を整える
- frontend から backend 健康状態を確認できるようにする
- ローカルファイル選択 UI を追加できるようにする
- 接続失敗時の再試行 UI を出す

---

## 3. 必須機能

- アプリ起動時の backend 起動
- backend readiness check
- ローカルファイル選択
- ログ参照導線
- settings から provider / connector 状態を確認可能

---

## 4. 完了確認

1. `pnpm tauri dev` で起動する
2. Login -> Dashboard -> Tickets の流れが通る
3. Local Context 用のファイル選択ができる
4. backend 未起動時のエラー表示が適切
5. 配布に向けた設定分離が済んでいる
