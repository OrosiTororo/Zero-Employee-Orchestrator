# ZEO UI Design Plan v2 — Cowork-style + MIT palette + Neovim CLI

## ライセンス確認結果

| ソース | ライセンス | 参照可否 |
|--------|-----------|---------|
| VSCode | MIT | OK — カラー、レイアウト、CSS直接流用可 |
| Zed | GPUI: Apache 2.0, Editor: GPL v3 | OK — デザイントークン参照可 |
| Neovim | Apache 2.0 + Vim License | OK — TUIパターン参照可 |
| Cursor | プロプライエタリ | NG — 参照不可 |

---

## GUI版デザイン計画

### 方針
「Cowork-styleのタスクファーストUI — チャット入力・承認ゲート・自律ダイアルを中心とした軽量レイアウト」
→ MIT公開カラーパレットを基盤に、Coworkパターン（Dispatch, Autonomy Dial, Operator Profile）を実装

### カラートークン（MIT公開パレットベース）

```css
/* ── Surface ── */
--bg-base:          #1E1E1E;   /* editor.background */
--bg-surface:       #252526;   /* sideBar.background, menu.background */
--bg-raised:        #2D2D2D;   /* tab.inactiveBackground */
--bg-input:         #3C3C3C;   /* input.background */
--bg-hover:         #2A2D2E;   /* list.hoverBackground */
--bg-active:        #37373D;   /* list.activeSelectionBackground */
--bg-nav-bar:  #333333;   /* nav bar background */
--bg-titlebar:      #323233;   /* titleBar.activeBackground */
--bg-statusbar:     #007ACC;   /* statusBar.background */
--bg-tab-bar:       #252526;   /* editorGroupHeader.tabsBackground */

/* ── Text ── */
--text-primary:     #D4D4D4;   /* editor.foreground */
--text-secondary:   #BBBBBB;   /* sideBarTitle.foreground */
--text-muted:       #6E7681;   /* editorLineNumber.foreground 系 */

/* ── Accent（単色） ── */
--accent:           #007ACC;   /* focusBorder, badge, statusBar */
--accent-fg:        #FFFFFF;

/* ── Border ── */
--border:           #3E3E42;   /* contrastBorder 近辺 */
--border-focus:     #007ACC;   /* focusBorder */

/* ── Status（Zed Apache 2.0 — 拡張機能で変更可能） ── */
--success:          #56BA9F;   /* Zed success */
--error:            #E5484D;   /* Zed error */
--warning:          #F3D768;   /* Zed warning */
--info:             #0090FF;   /* Zed info */
```

### ライトテーマ
```css
--bg-base:          #FFFFFF;
--bg-surface:       #F3F3F3;
--bg-raised:        #ECECEC;
--bg-nav-bar:  #2C2C2C;   /* ライトテーマでもダーク */
--bg-statusbar:     #007ACC;
--text-primary:     #1E1E1E;
--text-secondary:   #616161;
--text-muted:       #9E9E9E;
--accent:           #007ACC;
--border:           #E5E5E5;
```

### レイアウト寸法
```
Nav Bar:            48px幅, アイコン24px, ボタン高48px
Title Bar:          30px高（Tauri）
Status Bar:         22px高, font-size 12px, line-height 22px (Autonomy Dial + Dispatch feed)
Sidebar最小幅:      170px
本文font-size:      13px
グローバルfont:     11px
```

### シャドウ（最小限）
```css
/* 通常要素: シャドウなし */
--shadow-popup:  0 4px 12px rgba(0,0,0,0.3);   /* ポップオーバーのみ */
--shadow-modal:  0 8px 24px rgba(0,0,0,0.4);   /* モーダル/パレットのみ */
```

### ロゴ
- **カスタムSVG → 削除**
- Lucide `Workflow` アイコン + "ZEO" テキスト（font-weight: 700, color: #007ACC）
- アプリケーション全体のアイコンが必要な場合は Figma で別途デザイン

### 削除するカスタム要素
- Logo.tsx のカスタムSVG全体
- --gradient-primary, --gradient-surface, --gradient-card
- --shadow-glow, --shadow-inset
- .btn-primary のグラデーション背景 → 単色 #007ACC に
- .card-elevated のグラデーション → 単純な --bg-surface + border
- .text-gradient, .glass ユーティリティ
- @keyframes pulse-ring, checkmark, shimmer
- LoginPage 左パネルのカスタムブランディング
- OAuthコールバック HTML のカスタムカラー → MITパレットカラーに

### 残すもの
- GoogleIcon（Google公式ブランドカラー再現）
- Lucideアイコン（OSSライブラリ）
- @keyframes loading, fadeIn, slideIn（標準UIパターン）
- Tailwind CSSユーティリティ

### 拡張機能で変更可能にするもの
- ステータスカラー（success, error, warning, info）
- テーマ全体（dark/light/high-contrast + カスタムテーマ）
- Nav Barのアイコンセット
- フォントファミリー・サイズ

---

## CLI版デザイン計画（Neovim inspired）

### 方針
「Neovimのような、Vimをベースにメンテナンス性、拡張性、モダンなUI（TUI）と高速な操作の両立」
→ 現在の純粋ANSI出力から、Neovimのレイアウトパターンを取り入れた構造化TUIへ

### 現状分析
- ファイル: `apps/api/app/cli.py`（1,197行）
- TUIライブラリ: なし（raw ANSI escape codes + input()）
- 機能: チャット、スラッシュコマンド、NLコマンド処理、マルチプロバイダー対応

### Neovim TUI レイアウトパターン（実ソースから）
```
┌─────────────────────────────────┐
│ Tab Line (タブ/セッション)       │ ← Neovim tabline
├─────────────────────────────────┤
│                                 │
│ Buffer Area (メイン会話表示)     │ ← Neovim buffer
│                                 │
├─────────────────────────────────┤
│ Status Line (状態表示)           │ ← Neovim statusline (lualine風)
│ A | B | C            X | Y | Z  │
├─────────────────────────────────┤
│ Command Line (入力)             │ ← Neovim cmdline
└─────────────────────────────────┘
```

### ZEO CLI への適用
```
┌─────────────────────────────────────┐
│ ZEO v0.1.2 │ Session: default      │  ← セッション表示
├─────────────────────────────────────┤
│                                     │
│ User: 新規顧客向けフローを設計して   │  ← 会話バッファ
│                                     │
│ ZEO: 以下の手順で進めます...         │
│   1. ヒアリング                      │
│   2. DAG分解                         │
│   3. 承認ゲート設定                  │
│                                     │
├─────────────────────────────────────┤
│ NORMAL │ ollama │ ctx:23% │ ja │ Q  │  ← ステータスライン
├─────────────────────────────────────┤
│ > _                                 │  ← コマンドライン入力
└─────────────────────────────────────┘
```

### ステータスライン セクション（lualine風）

| セクション | 内容 | 例 |
|-----------|------|-----|
| A (左端) | モード | NORMAL / INSERT / COMMAND |
| B | プロバイダー | ollama / openrouter / anthropic |
| C | コンテキスト使用率 | ctx:23% |
| X (右端) | 言語 | ja / en |
| Y | 実行モード | Quality / Speed / Cost |
| Z | 接続状態 | ● Connected / ○ Offline |

### モードシステム（Neovim風）
- **NORMAL**: デフォルト。/コマンド入力可。矢印キーで履歴スクロール
- **INSERT**: 長文入力モード（三重引用符で入る）
- **COMMAND**: /helpなどのスラッシュコマンド実行中

### カラー（Neovim default colorscheme ベース）
```
ステータスライン背景:  #004C63 (Neovim dark blue)
モード NORMAL:         #56BA9F (green/cyan)
モード INSERT:         #007ACC (blue)
モード COMMAND:        #F3D768 (yellow)
プロンプト:            #D4D4D4 (foreground)
AIレスポンス:          #BBBBBB (secondary)
エラー:                #E5484D (Zed error)
```

### TUIライブラリ選択
**推奨: `textual`（Python TUIフレームワーク）**
- Rich/Textual エコシステム（活発なメンテナンス）
- CSS-likeスタイリング
- ウィジェットベース
- マウス対応

**代替: 現行のANSI出力を維持しつつ段階的にリッチ化**
- Phase 1: ステータスラインをlualine風に構造化（ANSI）
- Phase 2: バッファ表示のスクロール対応
- Phase 3: textual移行（オプション）

→ 軽量という方針から、Phase 1-2 をまず実装し、textualはオプション拡張として提供

---

## 変更対象ファイル一覧

### GUI (Desktop)
| ファイル | 変更 |
|---------|------|
| `index.css` | MITパレットカラーに書き換え、カスタム要素全削除 |
| `Logo.tsx` | カスタムSVG削除 → Lucide Workflow + テキスト |
| `Layout.tsx` | Cowork-style nav bar + status bar (Autonomy Dial, Dispatch feed) |
| `LoginPage.tsx` | 左パネル削除、フォームのみのシンプルデザイン |
| `DashboardPage.tsx` | カスタムカード→ Coworkタスクファーストスタイル |
| `CommandPalette.tsx` | カスタムアニメーション削除 |
| `BackendGuard.tsx` | カスタムグラデーション削除 |

### Backend
| ファイル | 変更 |
|---------|------|
| `auth.py` | OAuthコールバックHTML → MITパレットカラー |

### CLI
| ファイル | 変更 |
|---------|------|
| `cli.py` | ステータスライン構造化、モード表示、Neovimレイアウト |
| `banner.py` | カスタムカラー → MITパレット/Neovimカラー |
