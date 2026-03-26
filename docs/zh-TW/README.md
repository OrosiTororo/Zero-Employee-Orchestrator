**Language:** [English](../../README.md) | [日本語](../ja-JP/README.md) | [简体中文](../zh-CN/README.md) | **繁體中文** | [한국어](../ko-KR/README.md) | [Português (Brasil)](../pt-BR/README.md) | [Türkçe](../tr/README.md)

# Zero-Employee Orchestrator

[![Stars](https://img.shields.io/github/stars/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/stargazers)
[![Forks](https://img.shields.io/github/forks/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/network/members)
[![Contributors](https://img.shields.io/github/contributors/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Rust](https://img.shields.io/badge/-Rust-000000?logo=rust&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)

> **AI 編排平台 — 設計 · 執行 · 驗證 · 改進**

---

<div align="center">

**🌐 Language / 言語 / 语言**

[English](../../README.md) | [日本語](../ja-JP/README.md) | [简体中文](../zh-CN/README.md) | [**繁體中文**](README.md) | [한국어](../ko-KR/README.md) | [Português (Brasil)](../pt-BR/README.md) | [Türkçe](../tr/README.md)

</div>

---

**將 AI 作為組織來營運的平台 — 不僅僅是聊天機器人。**

用自然語言定義業務流程，讓多個 AI 代理按角色分工協作，在人類審批閘門和完整稽核能力的支援下執行任務。基於 Self-Healing DAG、Judge Layer 和 Experience Memory 的 9 層架構建構。

ZEO 本身是免費的開源專案。LLM API 費用由使用者直接向各供應商支付。

---

## 指南

本儲存庫是平台本體。指南文件說明了架構和設計理念。

<table>
<tr>
<td width="33%">
<a href="../../docs/guides/quickstart-guide.md">
<img src="../../assets/images/guides/quickstart-guide.svg" alt="快速入門指南" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/architecture-guide.md">
<img src="../../assets/images/guides/architecture-guide.svg" alt="架構深度解析" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/security-guide.md">
<img src="../../assets/images/guides/security-guide.svg" alt="安全指南" />
</a>
</td>
</tr>
<tr>
<td align="center"><b>快速入門指南</b><br/>安裝、首次工作流程、CLI 基礎。<b>請先閱讀此文件。</b></td>
<td align="center"><b>架構深度解析</b><br/>9 層架構、DAG 編排、Judge Layer、Experience Memory。</td>
<td align="center"><b>安全指南</b><br/>提示注入防禦、審批閘門、IAM、沙箱、PII 保護。</td>
</tr>
</table>

| 主題 | 學習內容 |
|------|---------|
| 9 層架構 | User → Design Interview → Task Orchestrator → Skill → Judge → Re-Propose → Memory → Provider → Registry |
| Self-Healing DAG | 任務失敗時自動重新規劃和重新提案 |
| Judge Layer | 基於規則的初判 + 跨模型高精度驗證 |
| Skill / Plugin / Extension | 支援自然語言生成技能的三層可擴充體系 |
| Human-in-the-Loop | 12 類危險操作需要人類審批 |
| 安全優先設計 | 提示注入防禦（40+ 模式）、PII 遮罩、檔案沙箱 |

---

## 最新動態

### v0.1.0 — 首次發布（2026年3月）

- **9 層架構** — User Layer → Design Interview → Task Orchestrator → Skill Layer → Judge Layer → Re-Propose → State & Memory → Provider → Skill Registry
- **Self-Healing DAG** — 任務失敗時透過動態 DAG 重構自動重新規劃
- **Judge Layer** — 基於規則的初判 + 跨模型高精度驗證
- **Experience Memory** — 從歷史執行中學習，提升未來效能
- **Skill / Plugin / Extension** — 三層可擴充體系：8 個內建技能、10 個外掛、5 個擴充
- **自然語言技能生成** — 用自然語言描述技能，AI 自動生成（含安全性檢查）
- **瀏覽器輔助** — Chrome 擴充功能疊加聊天，即時螢幕分享和錯誤診斷
- **媒體生成** — 圖片（DALL-E, SD）、影片（Runway ML, Pika）、音訊（TTS, ElevenLabs）、音樂（Suno）、3D（動態供應商註冊）
- **AI 工具整合** — 25+ 外部工具（GitHub、Slack、Jira、Figma 等）可由 AI 操作
- **安全優先** — 提示注入防禦（5 個類別、40+ 模式）、審批閘門、IAM、PII 保護、檔案沙箱
- **多模型支援** — 透過 `model_catalog.json` 實現動態模型目錄，已棄用模型自動回退
- **多語言（i18n）** — 日本語 / English / 中文 — 介面、AI 回覆和 CLI 無縫切換
- **自主運行** — Docker / Cloudflare Workers 實現 24/365 背景執行
- **自我改進** — AI 分析和改進自身技能（需審批）
- **A2A 通訊** — 代理間點對點訊息、頻道和協商

---

## 🖥️ 下載桌面應用程式

預先建置的桌面安裝程式可在 [Releases](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) 頁面取得。

| 作業系統 | 檔案 | 說明 |
|---|---|---|
| **Windows** | `.msi` / `-setup.exe` | Windows 安裝程式 |
| **macOS** | `.dmg` | macOS (Intel / Apple Silicon) |
| **Linux** | `.AppImage` | 可攜式（無需安裝） |
| **Linux** | `.deb` / `.rpm` | Debian/Ubuntu / Fedora/RHEL |

所有安裝程式均包含**設定精靈**，可選擇語言（English / 日本語 / 中文）。語言可隨時在**設定**中變更。

---

## 🚀 快速開始

2 分鐘內即可啟動運行：

### 步驟 1：安裝

```bash
# PyPI
pip install zero-employee-orchestrator

# 從原始碼安裝
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .

# Docker
docker compose up -d
```

### 步驟 2：設定（無需 API 金鑰即可開始）

```bash
# 方式 A：訂閱模式（無需金鑰）
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# 方式 B：Ollama 本地 LLM（完全離線）
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# 方式 C：多 LLM 平台（一把金鑰存取多個模型）
zero-employee config set OPENROUTER_API_KEY <your-key>

# 方式 D：各供應商 API 金鑰個別設定
zero-employee config set GEMINI_API_KEY <your-key>
```

> **ZEO 本身是免費的。** LLM API 費用由使用者直接向各供應商支付。詳見 [USER_SETUP.md](../../USER_SETUP.md)。

### 步驟 3：啟動

```bash
# Web 介面
zero-employee serve
# → http://localhost:18234

# 本地聊天（Ollama）
zero-employee local --model qwen3:8b --lang zh
```

✨ **完成了！** 您現在擁有了一個具備人類審批閘門和稽核功能的完整 AI 編排平台。

### 切換語言 (CLI)

預設語言為英語。您可以透過以下方式變更：

```bash
# 啟動時指定
zero-employee chat --lang ja    # 日語
zero-employee chat --lang zh    # 中文

# 持久化設定（儲存到 ~/.zero-employee/config.json）
zero-employee config set LANGUAGE zh

# 執行時切換（在聊天模式中）
/lang en                         # 切換到英語
/lang ja                         # 切換到日語
/lang zh                         # 切換到中文

# 透過 API
curl -X PUT http://localhost:18234/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"key": "LANGUAGE", "value": "zh"}'
```

語言設定在系統範圍內生效：CLI 輸出、AI 回覆和 Web 介面會同時切換。

---

## 📦 專案結構

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                  # FastAPI 後端
│   │   └── app/
│   │       ├── core/               # 設定、資料庫、安全、國際化
│   │       ├── api/routes/         # 39 個 REST API 路由模組
│   │       ├── api/ws/             # WebSocket
│   │       ├── models/             # SQLAlchemy ORM
│   │       ├── schemas/            # Pydantic DTO
│   │       ├── services/           # 商業邏輯
│   │       ├── repositories/       # 資料庫 I/O 抽象
│   │       ├── orchestration/      # DAG、Judge、狀態機
│   │       ├── providers/          # LLM 閘道、Ollama、RAG
│   │       ├── security/           # IAM、密鑰、清理、提示防禦
│   │       ├── policies/           # 審批閘門、自主執行邊界
│   │       ├── integrations/       # Sentry、MCP、外部技能、瀏覽器輔助
│   │       └── tools/              # 外部工具連接器
│   ├── desktop/              # Tauri v2 + React UI
│   ├── edge/                 # Cloudflare Workers
│   └── worker/               # 背景工作程序
├── skills/                   # 8 個內建技能
├── plugins/                  # 10 個外掛清單
├── extensions/               # 5 個擴充清單
│   └── browser-assist/
│       └── chrome-extension/ # 瀏覽器輔助 Chrome 擴充功能
├── packages/                 # 共享 NPM 套件
├── docs/                     # 多語言文件與指南
│   ├── ja-JP/                # 日本語
│   ├── zh-CN/                # 简体中文
│   ├── zh-TW/                # 繁體中文
│   ├── ko-KR/                # 한국어
│   ├── pt-BR/                # Português (Brasil)
│   ├── tr/                   # Türkçe
│   └── guides/               # 架構、安全、快速入門指南
└── assets/
    └── images/
        ├── guides/           # 指南標頭圖片
        └── logo/             # Logo 素材
```

---

## 🏗️ 9 層架構

```
┌─────────────────────────────────────────┐
│  1. User Layer       — 用自然語言傳達目的         │
│  2. Design Interview — 需求探索與深挖           │
│  3. Task Orchestrator — DAG 分解與進度管理       │
│  4. Skill Layer      — 專業 Skill + Context     │
│  5. Judge Layer      — Two-stage + Cross-Model QA │
│  6. Re-Propose       — 駁回 → 動態 DAG 重構      │
│  7. State & Memory   — Experience Memory        │
│  8. Provider         — LLM 閘道 (LiteLLM)       │
│  9. Skill Registry   — 發布 / 搜尋 / Import      │
└─────────────────────────────────────────┘
```

---

## 🎯 主要功能

### 核心編排

| 功能 | 描述 |
|------|------|
| **Design Interview** | 自然語言需求探索與深挖 |
| **Spec / Plan / Tasks** | 結構化中間產物 — 可複用、可稽核、可退回 |
| **Task Orchestrator** | 基於 DAG 的計畫生成、成本估算、品質模式切換 |
| **Judge Layer** | 基於規則的初判 + 跨模型高精度驗證 |
| **Self-Healing / Re-Propose** | 失敗時自動重新規劃，動態 DAG 重構 |
| **Experience Memory** | 從歷史執行中學習，提升未來效能 |

### 可擴充性

| 功能 | 描述 |
|------|------|
| **Skill / Plugin / Extension** | 三層可擴充體系（完整 CRUD 管理） |
| **自然語言技能生成** | 用自然語言描述 → AI 自動生成（含安全性檢查） |
| **Skill 市場** | 社群技能的發布、搜尋、評審和安裝 |
| **外部技能匯入** | 從 GitHub 儲存庫匯入技能 |
| **自我改進** | AI 分析和改進自身技能（需審批） |
| **元技能** | AI 學習如何學習（Feeling / Seeing / Dreaming / Making / Learning） |

### AI 能力

| 功能 | 描述 |
|------|------|
| **瀏覽器輔助** | Chrome 擴充功能疊加 — AI 即時檢視您的螢幕 |
| **媒體生成** | 圖片、影片、音訊、音樂、3D — 支援動態供應商註冊 |
| **AI 工具整合** | 25+ 外部工具（GitHub、Slack、Jira、Figma 等） |
| **A2A 通訊** | 代理間點對點訊息、頻道和協商 |
| **分身 AI** | 從使用者對話中學習判斷標準，共同成長 |
| **秘書 AI** | 腦力激盪 → 結構化任務，作為使用者和 AI 組織的橋樑 |
| **再利用引擎** | 自動將 1 個內容轉換為 10 種媒體格式 |

### 安全

| 功能 | 描述 |
|------|------|
| **提示注入防禦** | 5 個類別、40+ 偵測模式 |
| **審批閘門** | 12 類危險操作需要人類審批 |
| **檔案沙箱** | AI 僅可存取使用者許可的資料夾（預設：STRICT） |
| **資料保護** | 上傳/下載原則控制（預設：LOCKDOWN） |
| **PII 保護** | 自動偵測和遮罩 13 個類別的個人資訊 |
| **IAM** | 人類/AI 帳戶分離，AI 無法存取密鑰和管理權限 |
| **紅隊安全** | 8 個類別、20+ 測試的自我弱點評估 |

### 營運

| 功能 | 描述 |
|------|------|
| **多模型支援** | 動態目錄、自動回退、按任務指定供應商 |
| **多語言（i18n）** | 日本語 / English / 中文 — 介面、AI 回覆、CLI |
| **自主運行** | Docker / Cloudflare Workers — 即使 PC 關機也能運行 |
| **24/365 排程器** | 9 種觸發類型：cron、工單建立、預算閾值等 |
| **iPaaS 整合** | n8n / Zapier / Make Webhook 整合 |
| **雲端原生** | AWS / GCP / Azure / Cloudflare 抽象層 |
| **治理與合規** | GDPR / HIPAA / SOC2 / ISO27001 / CCPA / APPI |

---

## 🔒 安全

ZEO 採用**安全優先**設計，具備多層防禦：

| 層級 | 描述 |
|------|------|
| **提示注入防禦** | 偵測並阻止來自外部輸入的指令注入（5 個類別、40+ 模式） |
| **審批閘門** | 12 類危險操作（傳送、刪除、計費、權限變更等）需要人類審批 |
| **自主執行邊界** | 明確限制 AI 可自主執行的操作 |
| **IAM** | 人類/AI 帳戶分離；AI 無法存取密鑰和管理權限 |
| **密鑰管理** | Fernet 加密、自動遮罩、輪換支援 |
| **清理** | API 金鑰、權杖和個人資訊的自動移除 |
| **安全標頭** | 所有回應新增 CSP、HSTS、X-Frame-Options |
| **速率限制** | 基於 slowapi 的 API 速率限制 |
| **稽核日誌** | 記錄所有關鍵操作（從設計階段內建，非事後新增） |

弱點報告請參閱 [SECURITY.md](../../SECURITY.md)。

---

## 🖥️ CLI 參考

```bash
zero-employee serve              # 啟動 API 伺服器
zero-employee serve --port 8000  # 指定連接埠
zero-employee serve --reload     # 熱重新載入

zero-employee chat               # 聊天模式（所有供應商）
zero-employee chat --mode free   # 免費模式（Ollama / g4f）
zero-employee chat --lang zh     # 語言選擇

zero-employee local              # 本地聊天（Ollama）
zero-employee local --model qwen3:8b --lang zh

zero-employee models             # 已安裝模型清單
zero-employee pull qwen3:8b      # 下載模型

zero-employee config list        # 顯示所有設定
zero-employee config set <KEY>   # 設定值
zero-employee config get <KEY>   # 取得值

zero-employee db upgrade         # 資料庫遷移
zero-employee health             # 健康檢查
zero-employee security status    # 安全狀態
zero-employee update             # 更新至最新版本
```

---

## 🤖 支援的 LLM 模型

透過 `model_catalog.json` 統一管理 — 無需修改程式碼即可切換模型。

| 模式 | 描述 | 範例 |
|------|------|------|
| **Quality** | 最高品質 | Claude Opus, GPT-5.4, Gemini 2.5 Pro |
| **Speed** | 快速回應 | Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash |
| **Cost** | 低成本 | Haiku, Mini, Flash Lite, DeepSeek |
| **Free** | 免費 | Gemini 免費額度, Ollama 本地 |
| **Subscription** | 無需 API 金鑰 | 透過 g4f |

支援按任務指定供應商 — 可為每個任務指定供應商、模型和執行模式。

---

## 🧩 Skill / Plugin / Extension

### 三層可擴充體系

| 類型 | 描述 | 範例 |
|------|------|------|
| **Skill** | 單一用途的專業處理 | spec-writer, review-assistant, browser-assist |
| **Plugin** | 捆綁多個 Skill | ai-secretary, ai-self-improvement, youtube |
| **Extension** | 系統整合與基礎設施 | mcp, oauth, notifications, browser-assist |

### 用自然語言生成技能

```bash
POST /api/v1/registry/skills/generate
{
  "description": "將長篇文件摘要為3個要點的技能"
}
```

自動偵測 16 種危險模式。僅通過安全性檢查的技能才會被註冊。

---

## 🌐 瀏覽器輔助

Chrome 擴充功能疊加聊天 — AI 即時檢視您的螢幕並指導操作。

- **疊加聊天**：在任意網站上直接顯示聊天 UI
- **即時螢幕分享**：無需手動擷取螢幕，AI 直接檢視您的螢幕
- **錯誤診斷**：AI 讀取螢幕上的錯誤訊息並建議修復方案
- **表單輔助**：逐欄位的步驟式指導
- **隱私優先**：螢幕擷取僅暫時處理，PII 自動遮罩，密碼欄位自動模糊

### 設定

```
1. 在 Chrome 中載入 extensions/browser-assist/chrome-extension/
   → chrome://extensions → 開發人員模式 → 「載入未封裝項目」
2. 在任意網站上按一下聊天圖示
3. 輸入文字提問，或透過螢幕擷取按鈕將螢幕分享給 AI
```

---

## 🛠️ 技術堆疊

### 後端
- Python 3.12+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- SQLite（開發）/ PostgreSQL（生產推薦）
- LiteLLM Router SDK
- bcrypt / Fernet 加密
- slowapi 速率限制

### 前端
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand

### 桌面端
- Tauri v2 (Rust) + Python sidecar

### 部署
- Docker + docker-compose
- Cloudflare Workers（無伺服器）

---

## ❓ 常見問題

<details>
<summary><b>需要 API 金鑰才能開始嗎？</b></summary>

不需要。您可以使用訂閱模式（無需金鑰）或 Ollama（完全離線的本地 AI）。請參閱上方的快速開始部分。
</details>

<details>
<summary><b>費用是多少？</b></summary>

ZEO 本身是免費的。LLM API 費用由您直接向各供應商（OpenAI、Anthropic、Google 等）支付。您也可以使用 Ollama 本地模型完全免費運行。
</details>

<details>
<summary><b>可以同時使用多個 LLM 供應商嗎？</b></summary>

可以。ZEO 支援按任務指定供應商 — 您可以在同一工作流程中使用 Claude 進行高品質的規格審查，使用 GPT 進行快速任務執行。
</details>

<details>
<summary><b>我的資料安全嗎？</b></summary>

ZEO 採用自架設計。您的資料始終保留在您的基礎設施上。檔案沙箱預設為 STRICT，資料傳輸預設為 LOCKDOWN，PII 自動偵測預設啟用。
</details>

<details>
<summary><b>與 AutoGen / CrewAI / LangGraph 有什麼區別？</b></summary>

ZEO 是一個**業務工作流程平台**，而非開發者框架。它提供人類審批閘門、稽核日誌、三層可擴充體系、瀏覽器輔助、媒體生成和完整的 REST API — 所有這些都是為將 AI 作為組織來營運而設計的，而不僅僅是鏈式提示。
</details>

---

## 🧪 開發

```bash
# 設定
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# 啟動（熱重新載入）
zero-employee serve --reload

# 測試
pytest apps/api/app/tests/

# 程式碼檢查
ruff check apps/api/app/
ruff format apps/api/app/
```

---

## 🤝 貢獻

歡迎貢獻。

1. Fork → Branch → PR（標準流程）
2. 安全問題：請按照 [SECURITY.md](../../SECURITY.md) 進行非公開報告
3. 編碼規範：ruff 格式化、型別提示必須、async def

---

## 💜 贊助

本專案免費且開源。贊助有助於專案的持續維護和成長。

[**成為贊助者**](https://github.com/sponsors/OrosiTororo)

---

## 🌟 Star 歷史

[![Star History Chart](https://api.star-history.com/svg?repos=OrosiTororo/Zero-Employee-Orchestrator&type=Date)](https://star-history.com/#OrosiTororo/Zero-Employee-Orchestrator&Date)

---

## 📄 授權條款

MIT — 自由使用和修改，如果可以的話請貢獻回來。

---

<p align="center">
  <strong>Zero-Employee Orchestrator</strong> — 將 AI 作為組織來營運。<br>
  以安全性、可稽核性和人類監督為核心建構。
</p>
