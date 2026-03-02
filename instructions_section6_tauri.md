# Section 6 — ビルド・配布 Tauri 統合

> 担当: Antigravity（Tauri 設定・フロントビルド）+ Claude Code（PyInstaller サイドカー）
> 前提: Section 3（バックエンド）+ Section 4（フロントエンド）が完了していること
> 完了条件: `pnpm tauri dev` でデスクトップアプリが起動し、全機能が動作すること

---

## パート A — Claude Code 担当（サイドカービルド）

### ステップ 6.1 — PyInstaller ビルドテスト

```powershell
cd zpcos/backend
pwsh scripts/build_sidecar.ps1
```

確認:
- `frontend/src-tauri/binaries/zpcos-backend-{triple}.exe` が生成されること
- サイズが妥当（おおよそ 30〜80 MB）

### ステップ 6.2 — サイドカー単体テスト

```powershell
# 生成された exe を直接起動
.\frontend\src-tauri\binaries\zpcos-backend-x86_64-pc-windows-msvc.exe

# 別ターミナル
curl http://localhost:18234/api/health
# → {"status":"ok", ...}
```

---

## パート B — Antigravity 担当（Tauri 設定）

### ステップ 6.3 — tauri.conf.json 最終調整

```
frontend/src-tauri/tauri.conf.json を以下の設定で更新:

{
  "productName": "ZPCOS",
  "version": "0.1.0",
  "identifier": "com.zpcos.app",
  "build": {
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "title": "ZPCOS — AI業務実行OS",
        "width": 1280,
        "height": 800,
        "minWidth": 960,
        "minHeight": 600,
        "resizable": true
      }
    ]
  },
  "bundle": {
    "active": true,
    "targets": ["msi", "nsis"],
    "externalBin": ["binaries/zpcos-backend"],
    "windows": {
      "wix": { "language": "ja-JP" }
    },
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.ico"
    ]
  }
}
```

### ステップ 6.4 — Rust サイドカー起動コード

```
frontend/src-tauri/src/main.rs を編集:
Tauri の sidecar API でバックエンドプロセスを起動・管理する。

- アプリ起動時に zpcos-backend サイドカーを起動
- アプリ終了時にサイドカーを kill
- サイドカーの stdout/stderr をログに出力
- ヘルスチェック（/api/health）でバックエンド起動完了を待つ
```

### ステップ 6.5 — フロントエンドの API URL 切り替え

```
src/lib/api.ts の API_BASE を環境によって切り替え:

- 開発時: http://localhost:18234
- Tauri 内: http://localhost:18234（サイドカーが同じポートで起動）

window.__TAURI__ の存在でTauri環境を判定。
```

---

## ステップ 6.6 — 統合テスト

```powershell
cd zpcos

# 1. サイドカービルド
cd backend && pwsh scripts/build_sidecar.ps1

# 2. Tauri 開発モード
cd ../frontend && pnpm tauri dev

# 確認項目:
# - デスクトップウィンドウが開く
# - バックエンドが自動起動する
# - ログイン画面が表示される
# - OpenRouter ログインが動作する
# - ダッシュボードが表示される
# - Skill 実行が動作する
# - Orchestrate が動作する
```

### ステップ 6.7 — 本番ビルド（最終）

```powershell
cd zpcos/frontend
pnpm tauri build
# → src-tauri/target/release/bundle/ に .msi と .exe が生成される
```

```powershell
git add -A
git commit -m "feat: Tauri integration and build (Section 6 v11.0)"
```

セクション 6 完了。
