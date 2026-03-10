"""Internationalization (i18n) — Japanese / English / Chinese support.

Provides a simple translation mechanism for CLI/TUI messages and UI labels.
Covers the three supported languages: ja (Japanese), en (English), zh (Chinese).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------

_TRANSLATIONS: dict[str, dict[str, str]] = {
    # -- Banner / startup --
    "banner_subtitle": {
        "ja": "Zero-Employee Orchestrator",
        "en": "Zero-Employee Orchestrator",
        "zh": "Zero-Employee Orchestrator",
    },
    "banner_tagline": {
        "ja": "AI オーケストレーション基盤",
        "en": "AI Orchestration Platform",
        "zh": "AI 编排平台",
    },
    "banner_offline": {
        "ja": "オフライン AI 業務エージェント",
        "en": "Offline AI Task Agent",
        "zh": "离线 AI 任务代理",
    },
    "banner_desc": {
        "ja": "ログイン不要 · クラウド不要 · 完全ローカル · Ollama搭載",
        "en": "No login · No cloud · Fully local · Powered by Ollama",
        "zh": "无需登录 · 无需云端 · 完全本地 · 由 Ollama 驱动",
    },
    # -- Status labels --
    "label_model": {
        "ja": "モデル",
        "en": "Model",
        "zh": "模型",
    },
    "label_engine": {
        "ja": "エンジン",
        "en": "Engine",
        "zh": "引擎",
    },
    "label_mode": {
        "ja": "モード",
        "en": "Mode",
        "zh": "模式",
    },
    "label_cwd": {
        "ja": "作業ディレクトリ",
        "en": "Working Dir",
        "zh": "工作目录",
    },
    "label_language": {
        "ja": "言語",
        "en": "Language",
        "zh": "语言",
    },
    "label_status": {
        "ja": "状態",
        "en": "Status",
        "zh": "状态",
    },
    "label_tasks": {
        "ja": "タスク",
        "en": "Tasks",
        "zh": "任务",
    },
    "label_agents": {
        "ja": "エージェント",
        "en": "Agents",
        "zh": "代理",
    },
    "label_approvals": {
        "ja": "承認待ち",
        "en": "Pending Approvals",
        "zh": "待审批",
    },
    # -- Mode names --
    "mode_orchestrator": {
        "ja": "オーケストレーター",
        "en": "Orchestrator",
        "zh": "编排器",
    },
    "mode_auto_approve": {
        "ja": "自動承認",
        "en": "Auto-Approve",
        "zh": "自动审批",
    },
    "mode_manual_approve": {
        "ja": "手動承認",
        "en": "Manual-Approve",
        "zh": "手动审批",
    },
    # -- Chat messages --
    "chat_welcome": {
        "ja": "何をお手伝いしましょうか？自然言語で業務を指示できます。",
        "en": "How can I help? Describe your task in natural language.",
        "zh": "我能帮您什么？请用自然语言描述您的任务。",
    },
    "chat_first_time": {
        "ja": "初めての方は: 「売上レポートを作成して」と入力してみてください",
        "en": 'First time? Try: "Create a sales report"',
        "zh": "第一次使用？试试输入：「创建销售报告」",
    },
    "chat_help_hint": {
        "ja": "/help コマンド一覧 · Ctrl+C 中断 · /quit 終了",
        "en": "/help commands · Ctrl+C interrupt · /quit to exit",
        "zh": "/help 命令列表 · Ctrl+C 中断 · /quit 退出",
    },
    "chat_thinking": {
        "ja": "考え中...",
        "en": "Thinking...",
        "zh": "思考中...",
    },
    "chat_executing": {
        "ja": "タスクを実行中...",
        "en": "Executing task...",
        "zh": "正在执行任务...",
    },
    "chat_approval_required": {
        "ja": "この操作には承認が必要です。承認しますか？ [y/N]",
        "en": "This operation requires approval. Approve? [y/N]",
        "zh": "此操作需要审批。是否批准？ [y/N]",
    },
    "chat_goodbye": {
        "ja": "お疲れ様でした。",
        "en": "Goodbye.",
        "zh": "再见。",
    },
    # -- Error messages --
    "error_no_ollama": {
        "ja": "Ollama が起動していません。起動: ollama serve",
        "en": "Ollama is not running. Start it with: ollama serve",
        "zh": "Ollama 未运行。请启动: ollama serve",
    },
    "error_no_model": {
        "ja": "モデルがありません。インストール: ollama pull qwen3:8b",
        "en": "No models available. Install: ollama pull qwen3:8b",
        "zh": "没有可用模型。安装: ollama pull qwen3:8b",
    },
    "error_timeout": {
        "ja": "リクエストがタイムアウトしました（モデルが読み込み中かRAM不足）",
        "en": "Request timed out (model may be loading or insufficient RAM)",
        "zh": "请求超时（模型可能正在加载或内存不足）",
    },
    "error_connection": {
        "ja": "接続エラー: {detail}",
        "en": "Connection error: {detail}",
        "zh": "连接错误: {detail}",
    },
    # -- Orchestration --
    "orch_task_created": {
        "ja": "タスクを作成しました: {title}",
        "en": "Task created: {title}",
        "zh": "任务已创建: {title}",
    },
    "orch_task_completed": {
        "ja": "タスク完了: {title}",
        "en": "Task completed: {title}",
        "zh": "任务完成: {title}",
    },
    "orch_task_failed": {
        "ja": "タスク失敗: {title} — {reason}",
        "en": "Task failed: {title} — {reason}",
        "zh": "任务失败: {title} — {reason}",
    },
    "orch_agent_assigned": {
        "ja": "エージェント {agent} をタスク {task} に割当",
        "en": "Agent {agent} assigned to task {task}",
        "zh": "代理 {agent} 已分配到任务 {task}",
    },
    "orch_dag_rebuilt": {
        "ja": "DAG を再構築しました（Self-Healing）",
        "en": "DAG rebuilt (Self-Healing)",
        "zh": "DAG 已重建（自修复）",
    },
    "orch_plan_generated": {
        "ja": "実行計画を生成しました（{n_tasks} タスク）",
        "en": "Execution plan generated ({n_tasks} tasks)",
        "zh": "执行计划已生成（{n_tasks} 个任务）",
    },
    # -- Audit --
    "audit_dangerous_op": {
        "ja": "危険操作を検出: {op}（承認が必要）",
        "en": "Dangerous operation detected: {op} (approval required)",
        "zh": "检测到危险操作: {op}（需要审批）",
    },
}


# ---------------------------------------------------------------------------
# Translation function
# ---------------------------------------------------------------------------

_current_lang: str = "ja"


def set_language(lang: str) -> None:
    """Set the current language (ja/en/zh)."""
    global _current_lang
    if lang in ("ja", "en", "zh"):
        _current_lang = lang
    else:
        _current_lang = "en"  # fallback


def get_language() -> str:
    """Get the current language code."""
    return _current_lang


def t(key: str, **kwargs: str) -> str:
    """Translate a message key to the current language.

    Args:
        key:    Translation key (e.g. "chat_welcome")
        kwargs: Format parameters (e.g. title="My Task")

    Returns:
        Translated string, or the key itself if not found.
    """
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key

    text = entry.get(_current_lang, entry.get("en", key))

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text


# ---------------------------------------------------------------------------
# Initialize from environment
# ---------------------------------------------------------------------------


def init_language_from_env() -> None:
    """Initialize language from LANGUAGE env var or config."""
    lang = os.environ.get("LANGUAGE", "").lower()[:2]
    if lang in ("ja", "en", "zh"):
        set_language(lang)
    else:
        # Auto-detect from LANG env var
        system_lang = os.environ.get("LANG", "").lower()
        if "ja" in system_lang:
            set_language("ja")
        elif "zh" in system_lang:
            set_language("zh")
        else:
            set_language("ja")  # default to Japanese per project convention


init_language_from_env()
