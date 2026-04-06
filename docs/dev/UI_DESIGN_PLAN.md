# ZEO UI Design Plan — VSCode準拠 + Zed参考

## ライセンス確認結果

| ソース | ライセンス | UIデザイン参照 |
|--------|-----------|--------------|
| VSCode | MIT | OK（カラートークン、レイアウト直接流用可） |
| Zed | GPL/Apache 2.0 | OK（GPUI UIフレームワークはApache 2.0） |
| Cursor | プロプライエタリ | NG（非公開、参照不可） |

---

## 1. カラートークン（VSCode Dark Default を基盤）

### ベース（VSCode公式値をそのまま使用）
```
--bg-base:          #1E1E1E   ← VSCode editor.background
--bg-surface:       #252526   ← VSCode sideBar.background / menu.background
--bg-raised:        #2D2D2D   ← VSCode tab.inactiveBackground
--bg-overlay:       #303031   ← VSCode widget.border 周辺
--bg-input:         #3C3C3C   ← VSCode input.background
--bg-hover:         #2A2D2E   ← VSCode list.hoverBackground
--bg-active:        #37373D   ← VSCode list.activeSelectionBackground
--bg-activity-bar:  #333333   ← VSCode activityBar.background
--bg-titlebar:      #323233   ← VSCode titleBar.activeBackground
--bg-statusbar:     #007ACC   ← VSCode statusBar.background
```

### テキスト（VSCode公式値）
```
--text-primary:     #D4D4D4   ← VSCode editor.foreground
--text-secondary:   #BBBBBB   ← VSCode sideBarTitle.foreground
--text-muted:       #6E7681   ← VSCode editorGutter
```

### アクセント（VSCode公式値）
```
--accent:           #007ACC   ← VSCode focusBorder / badge
--accent-fg:        #FFFFFF
```

### ステータス（Zed参考 — より視認性の高い色）
```
--success:          #56BA9F   ← Zed success (VSCode緑 #16825d より明瞭)
--error:            #E5484D   ← Zed error
--warning:          #F3D768   ← Zed warning
--info:             #0090FF   ← Zed info/blue
```

### ボーダー
```
--border:           #3E3E42   ← VSCode contrastBorder近辺
--border-focus:     #007ACC   ← VSCode focusBorder
```

---

## 2. ライトテーマ（VSCode Light Default）

```
--bg-base:          #FFFFFF
--bg-surface:       #F3F3F3
--bg-activity-bar:  #2C2C2C   ← VSCodeライトでもダーク
--text-primary:     #1E1E1E
--text-secondary:   #616161
--accent:           #007ACC   ← 共通
```

---

## 3. レイアウト寸法（VSCode準拠）

```
Activity Bar幅:     48px      ← VSCode ACTIVITY_BAR_WIDTH
Activity Barアイコン: 24px     ← VSCode ACTIVITY_BAR_ICON_SIZE
Activity Barボタン高: 48px     ← VSCode ACTIVITY_BAR_ACTION_HEIGHT
Title Bar高:        30px      ← VSCode（Electronでは22px、Tauriでは30px）
Status Bar高:       22px      ← VSCode STATUS_BAR_HEIGHT
Tab Bar高:          35px      ← VSCode TAB_HEIGHT
Sidebar最小幅:      170px     ← VSCode SIDEBAR_MIN_WIDTH
```

---

## 4. ロゴ方針

**現行**: カスタムSVGロゴ（三角ネットワーク＋ノード） → **削除**

**代替案 — Lucide `Workflow` アイコン + テキスト**:
- Lucide React にある `Workflow` アイコンをロゴマークとして使用
- アイコンの色: `#007ACC`（VSCodeアクセント）
- テキスト: "ZEO" のみ、フォント: system-ui, 太字
- フルロゴ: `[Workflow icon] Zero-Employee Orchestrator`

→ ロゴはブランドイメージに関わるので、この方向でよいか確認お願いします。
  もし専用デザインが必要なら、Figma等で別途作成を推奨。

---

## 5. シャドウ（Zed参考）

VSCodeはシャドウをほぼ使わないフラットデザイン。
Zedも最小限のシャドウ。ZEOではポップオーバーとモーダルのみに使用：

```
--shadow-sm:    なし（通常要素にはシャドウなし）
--shadow-popup: 0 4px 12px rgba(0,0,0,0.3)  ← ポップオーバー/ドロップダウンのみ
--shadow-modal: 0 8px 24px rgba(0,0,0,0.4)  ← モーダル/コマンドパレットのみ
```

---

## 6. 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `index.css` | VSCode公式値でテーマ書き換え、カスタムシャドウ・グラデーション削除 |
| `Logo.tsx` | カスタムSVG削除 → Lucide `Workflow` + テキスト |
| `Layout.tsx` | VSCode寸法に厳密準拠、タブバー復元 |
| `LoginPage.tsx` | 左パネルのカスタムブランディング削除、シンプル化 |
| `DashboardPage.tsx` | カスタムカード→VSCodeスタイルのパネル |
| `CommandPalette.tsx` | カスタムアニメーション→シンプルフェード |
| `BackendGuard.tsx` | カスタムグラデーション削除 |
| `auth.py` | OAuthコールバックHTMLをVSCodeカラーに変更 |

---

## 7. 削除するカスタム要素

- [x] `Logo` / `LogoMark` SVGコンポーネント
- [x] `--gradient-primary` (ブルー→パープルのグラデーション)
- [x] `--gradient-surface`, `--gradient-card`
- [x] `--shadow-glow` (アクセントグロウ)
- [x] `.btn-primary` のグラデーション背景
- [x] `.card-elevated` のグラデーション背景
- [x] `.text-gradient` ユーティリティ
- [x] `.glass` ユーティリティ
- [x] `@keyframes pulse-ring`, `checkmark`, `shimmer`
- [x] LoginPage左パネルのカスタムグラデーション背景
- [x] OAuthコールバックのカスタムダークテーマ

---

## 8. 残すもの

- GoogleIcon（Google公式ブランドカラーの再現、商標に忠実）
- Lucideアイコンの使用（OSSアイコンライブラリ）
- Tailwind CSSのユーティリティクラス使用
- `@keyframes loading`（プログレスバー用、標準的パターン）
- `@keyframes fadeIn`, `slideIn`（標準的UIアニメーション）
