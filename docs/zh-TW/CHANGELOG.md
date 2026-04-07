# Changelog

> [English](../CHANGELOG.md) | [日本語](../ja-JP/CHANGELOG.md) | [简体中文](../zh/CHANGELOG.md) | [한국어](../ko-KR/CHANGELOG.md) | [Português](../pt-BR/CHANGELOG.md) | [Türkçe](../tr/CHANGELOG.md) | 繁體中文

本專案的所有重要變更將記錄在此檔案中。

格式：[Keep a Changelog](https://keepachangelog.com/)
版本：[Semantic Versioning](https://semver.org/)

## [0.1.1] - 2026-03-28

### 新增

- **生產環境 Docker Compose** — 資源限制（記憶體/CPU）、網路隔離、日誌輪替、唯讀檔案系統、`no-new-privileges` 安全選項、健康檢查 `start_period`
- **CI 新增 Trivy 容器映像掃描** — 合併前掃描 Docker 映像的 CRITICAL/HIGH 弱點
- **CI 新增 Red-team 安全測試** — 執行完整 Red-team 測試套件，發現嚴重問題時使建置失敗
- **65+ i18n 翻譯鍵** — 全 6 種語言從約 30 個擴展到 65+ 個鍵，涵蓋安全訊息、設定、導覽、常用操作、技能/外掛管理、伺服器健康、預算/成本、Judge Layer 和瀏覽器助手
- **補充缺失的 PII 偵測模式** — 新增駕駛執照（日本/美國）和日語姓名模式，完善全部 13 個 PII 類別
- **6 語言 i18n 支援** — 在現有日語、英語、中文基礎上，新增韓語（한국어）、葡萄牙語（Português）、土耳其語（Türkçe）的 UI 翻譯
- **可擴展 LLM API 金鑰設定** — 可在內建四個供應商之外自由新增自訂供應商
- **Design Interview 過去失敗模式回饋** — 自動從 Experience Memory 和 Failure Taxonomy 搜尋類似失敗模式，動態注入警告和追加問題

### 變更

- **預設語言改為英語** — 從 `ja` 改為 `en` 以促進國際化採用（使用者可設定 `LANGUAGE=ja` 或 `--lang ja`）
- **模型目錄更新至最新** — GPT-5.4 / GPT-5.4 Mini（從 4.1）、Llama 4（從 3.2）、Phi-4（從 3）、Claude Haiku 非日期別名
- **文件準確性修正** — 修正誇大描述：提示防護模式 40+→28+、應用程式連接器 35+→34+、路由模組 41→40。全語言修正 "GPT-5 Mini"→"GPT-5.4 Mini"
- **Cowork 風格導覽列** — 移除雙側邊欄，改用帶提示的圖示導覽列

### 安全

- **CI 中 pip-audit 改為阻斷模式** — 移除 `continue-on-error`，依賴弱點將導致建置失敗
- **Red-team 測試強化** — 測試處理器使用真實載荷執行安全模組，而非僅配置驗證
- **Sandbox 符號連結攻擊防護增強** — 偵測並阻止解析路徑指向與原始路徑不同的目錄

## [0.1.0] - 2026-03-12 — Platform v0.1（整合版本）

初始實作。詳細內容請參閱 [英文 CHANGELOG](../CHANGELOG.md)。

[0.1.1]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.1
[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
