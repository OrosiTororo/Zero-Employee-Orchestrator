"""Internationalization (i18n) — multi-language support.

Provides a simple translation mechanism for CLI/TUI messages and UI labels.
Supported languages: ja (Japanese), en (English), zh (Chinese), ko (Korean),
pt (Portuguese), tr (Turkish).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Supported language codes
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES: set[str] = {"ja", "en", "zh", "ko", "pt", "tr"}

# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------

_TRANSLATIONS: dict[str, dict[str, str]] = {
    # -- Banner / startup --
    "banner_subtitle": {
        "ja": "Zero-Employee Orchestrator",
        "en": "Zero-Employee Orchestrator",
        "zh": "Zero-Employee Orchestrator",
        "ko": "Zero-Employee Orchestrator",
        "pt": "Zero-Employee Orchestrator",
        "tr": "Zero-Employee Orchestrator",
    },
    "banner_tagline": {
        "ja": "AI オーケストレーション基盤",
        "en": "AI Orchestration Platform",
        "zh": "AI 编排平台",
        "ko": "AI 오케스트레이션 플랫폼",
        "pt": "Plataforma de Orquestração de IA",
        "tr": "AI Orkestrasyon Platformu",
    },
    "banner_offline": {
        "ja": "オフライン AI 業務エージェント",
        "en": "Offline AI Task Agent",
        "zh": "离线 AI 任务代理",
        "ko": "오프라인 AI 작업 에이전트",
        "pt": "Agente de Tarefas de IA Offline",
        "tr": "Çevrimdışı AI Görev Ajanı",
    },
    "banner_desc": {
        "ja": "ログイン不要 · クラウド不要 · 完全ローカル · Ollama搭載",
        "en": "No login · No cloud · Fully local · Powered by Ollama",
        "zh": "无需登录 · 无需云端 · 完全本地 · 由 Ollama 驱动",
        "ko": "로그인 불필요 · 클라우드 불필요 · 완전 로컬 · Ollama 탑재",
        "pt": "Sem login · Sem nuvem · Totalmente local · Powered by Ollama",
        "tr": "Giriş gereksiz · Bulut gereksiz · Tamamen yerel · Ollama ile çalışır",
    },
    # -- Status labels --
    "label_model": {
        "ja": "モデル",
        "en": "Model",
        "zh": "模型",
        "ko": "모델",
        "pt": "Modelo",
        "tr": "Model",
    },
    "label_engine": {
        "ja": "エンジン",
        "en": "Engine",
        "zh": "引擎",
        "ko": "엔진",
        "pt": "Motor",
        "tr": "Motor",
    },
    "label_mode": {
        "ja": "モード",
        "en": "Mode",
        "zh": "模式",
        "ko": "모드",
        "pt": "Modo",
        "tr": "Mod",
    },
    "label_cwd": {
        "ja": "作業ディレクトリ",
        "en": "Working Dir",
        "zh": "工作目录",
        "ko": "작업 디렉토리",
        "pt": "Diretório de Trabalho",
        "tr": "Çalışma Dizini",
    },
    "label_language": {
        "ja": "言語",
        "en": "Language",
        "zh": "语言",
        "ko": "언어",
        "pt": "Idioma",
        "tr": "Dil",
    },
    "label_status": {
        "ja": "状態",
        "en": "Status",
        "zh": "状态",
        "ko": "상태",
        "pt": "Status",
        "tr": "Durum",
    },
    "label_tasks": {
        "ja": "タスク",
        "en": "Tasks",
        "zh": "任务",
        "ko": "작업",
        "pt": "Tarefas",
        "tr": "Görevler",
    },
    "label_agents": {
        "ja": "エージェント",
        "en": "Agents",
        "zh": "代理",
        "ko": "에이전트",
        "pt": "Agentes",
        "tr": "Ajanlar",
    },
    "label_approvals": {
        "ja": "承認待ち",
        "en": "Pending Approvals",
        "zh": "待审批",
        "ko": "승인 대기",
        "pt": "Aprovações Pendentes",
        "tr": "Onay Bekleyenler",
    },
    # -- Mode names --
    "mode_orchestrator": {
        "ja": "オーケストレーター",
        "en": "Orchestrator",
        "zh": "编排器",
        "ko": "오케스트레이터",
        "pt": "Orquestrador",
        "tr": "Orkestratör",
    },
    "mode_auto_approve": {
        "ja": "自動承認",
        "en": "Auto-Approve",
        "zh": "自动审批",
        "ko": "자동 승인",
        "pt": "Aprovação Automática",
        "tr": "Otomatik Onay",
    },
    "mode_manual_approve": {
        "ja": "手動承認",
        "en": "Manual-Approve",
        "zh": "手动审批",
        "ko": "수동 승인",
        "pt": "Aprovação Manual",
        "tr": "Manuel Onay",
    },
    # -- Chat messages --
    "chat_welcome": {
        "ja": "何をお手伝いしましょうか？自然言語で業務を指示できます。",
        "en": "How can I help? Describe your task in natural language.",
        "zh": "我能帮您什么？请用自然语言描述您的任务。",
        "ko": "무엇을 도와드릴까요? 자연어로 업무를 지시할 수 있습니다.",
        "pt": "Como posso ajudar? Descreva sua tarefa em linguagem natural.",
        "tr": "Size nasıl yardımcı olabilirim? Görevinizi doğal dilde açıklayın.",
    },
    "chat_first_time": {
        "ja": "初めての方は: 「売上レポートを作成して」と入力してみてください",
        "en": 'First time? Try: "Create a sales report"',
        "zh": "第一次使用？试试输入：「创建销售报告」",
        "ko": '처음이신가요? "매출 보고서를 작성해 주세요"라고 입력해 보세요',
        "pt": 'Primeira vez? Tente: "Criar um relatório de vendas"',
        "tr": 'İlk kez mi kullanıyorsunuz? Deneyin: "Satış raporu oluştur"',
    },
    "chat_help_hint": {
        "ja": "/help コマンド一覧 · Ctrl+C 中断 · /quit 終了",
        "en": "/help commands · Ctrl+C interrupt · /quit to exit",
        "zh": "/help 命令列表 · Ctrl+C 中断 · /quit 退出",
        "ko": "/help 명령어 목록 · Ctrl+C 중단 · /quit 종료",
        "pt": "/help comandos · Ctrl+C interromper · /quit para sair",
        "tr": "/help komutlar · Ctrl+C kesme · /quit çıkış",
    },
    "chat_thinking": {
        "ja": "考え中...",
        "en": "Thinking...",
        "zh": "思考中...",
        "ko": "생각 중...",
        "pt": "Pensando...",
        "tr": "Düşünüyor...",
    },
    "chat_executing": {
        "ja": "タスクを実行中...",
        "en": "Executing task...",
        "zh": "正在执行任务...",
        "ko": "작업 실행 중...",
        "pt": "Executando tarefa...",
        "tr": "Görev yürütülüyor...",
    },
    "chat_approval_required": {
        "ja": "この操作には承認が必要です。承認しますか？ [y/N]",
        "en": "This operation requires approval. Approve? [y/N]",
        "zh": "此操作需要审批。是否批准？ [y/N]",
        "ko": "이 작업은 승인이 필요합니다. 승인하시겠습니까? [y/N]",
        "pt": "Esta operação requer aprovação. Aprovar? [y/N]",
        "tr": "Bu işlem onay gerektiriyor. Onaylıyor musunuz? [y/N]",
    },
    "chat_goodbye": {
        "ja": "お疲れ様でした。",
        "en": "Goodbye.",
        "zh": "再见。",
        "ko": "수고하셨습니다.",
        "pt": "Até logo.",
        "tr": "Hoşça kalın.",
    },
    # -- Error messages --
    "error_no_ollama": {
        "ja": "Ollama が起動していません。起動: ollama serve",
        "en": "Ollama is not running. Start it with: ollama serve",
        "zh": "Ollama 未运行。请启动: ollama serve",
        "ko": "Ollama가 실행되고 있지 않습니다. 시작: ollama serve",
        "pt": "Ollama não está em execução. Inicie com: ollama serve",
        "tr": "Ollama çalışmıyor. Başlatın: ollama serve",
    },
    "error_no_model": {
        "ja": "モデルがありません。インストール: ollama pull qwen3:8b",
        "en": "No models available. Install: ollama pull qwen3:8b",
        "zh": "没有可用模型。安装: ollama pull qwen3:8b",
        "ko": "사용 가능한 모델이 없습니다. 설치: ollama pull qwen3:8b",
        "pt": "Nenhum modelo disponível. Instale: ollama pull qwen3:8b",
        "tr": "Kullanılabilir model yok. Kurun: ollama pull qwen3:8b",
    },
    "error_timeout": {
        "ja": "リクエストがタイムアウトしました（モデルが読み込み中かRAM不足）",
        "en": "Request timed out (model may be loading or insufficient RAM)",
        "zh": "请求超时（模型可能正在加载或内存不足）",
        "ko": "요청 시간이 초과되었습니다 (모델 로딩 중이거나 RAM 부족)",
        "pt": "Tempo limite da solicitação (modelo pode estar carregando ou RAM insuficiente)",
        "tr": "İstek zaman aşımına uğradı (model yükleniyor veya yetersiz RAM olabilir)",
    },
    "error_connection": {
        "ja": "接続エラー: {detail}",
        "en": "Connection error: {detail}",
        "zh": "连接错误: {detail}",
        "ko": "연결 오류: {detail}",
        "pt": "Erro de conexão: {detail}",
        "tr": "Bağlantı hatası: {detail}",
    },
    # -- Orchestration --
    "orch_task_created": {
        "ja": "タスクを作成しました: {title}",
        "en": "Task created: {title}",
        "zh": "任务已创建: {title}",
        "ko": "작업이 생성되었습니다: {title}",
        "pt": "Tarefa criada: {title}",
        "tr": "Görev oluşturuldu: {title}",
    },
    "orch_task_completed": {
        "ja": "タスク完了: {title}",
        "en": "Task completed: {title}",
        "zh": "任务完成: {title}",
        "ko": "작업 완료: {title}",
        "pt": "Tarefa concluída: {title}",
        "tr": "Görev tamamlandı: {title}",
    },
    "orch_task_failed": {
        "ja": "タスク失敗: {title} — {reason}",
        "en": "Task failed: {title} — {reason}",
        "zh": "任务失败: {title} — {reason}",
        "ko": "작업 실패: {title} — {reason}",
        "pt": "Tarefa falhou: {title} — {reason}",
        "tr": "Görev başarısız: {title} — {reason}",
    },
    "orch_agent_assigned": {
        "ja": "エージェント {agent} をタスク {task} に割当",
        "en": "Agent {agent} assigned to task {task}",
        "zh": "代理 {agent} 已分配到任务 {task}",
        "ko": "에이전트 {agent}가 작업 {task}에 배정됨",
        "pt": "Agente {agent} atribuído à tarefa {task}",
        "tr": "Ajan {agent}, {task} görevine atandı",
    },
    "orch_dag_rebuilt": {
        "ja": "DAG を再構築しました（Self-Healing）",
        "en": "DAG rebuilt (Self-Healing)",
        "zh": "DAG 已重建（自修复）",
        "ko": "DAG가 재구축되었습니다 (자가 복구)",
        "pt": "DAG reconstruído (Auto-Recuperação)",
        "tr": "DAG yeniden oluşturuldu (Kendi Kendine İyileşme)",
    },
    "orch_plan_generated": {
        "ja": "実行計画を生成しました（{n_tasks} タスク）",
        "en": "Execution plan generated ({n_tasks} tasks)",
        "zh": "执行计划已生成（{n_tasks} 个任务）",
        "ko": "실행 계획이 생성되었습니다 ({n_tasks}개 작업)",
        "pt": "Plano de execução gerado ({n_tasks} tarefas)",
        "tr": "Yürütme planı oluşturuldu ({n_tasks} görev)",
    },
    # -- Audit --
    "audit_dangerous_op": {
        "ja": "危険操作を検出: {op}（承認が必要）",
        "en": "Dangerous operation detected: {op} (approval required)",
        "zh": "检测到危险操作: {op}（需要审批）",
        "ko": "위험한 작업 감지: {op} (승인 필요)",
        "pt": "Operação perigosa detectada: {op} (aprovação necessária)",
        "tr": "Tehlikeli işlem algılandı: {op} (onay gerekli)",
    },
}


# ---------------------------------------------------------------------------
# Translation function
# ---------------------------------------------------------------------------

_current_lang: str = "ja"


def set_language(lang: str) -> None:
    """Set the current language.

    Supported: ja, en, zh, ko, pt, tr.
    Falls back to English for unsupported codes.
    """
    global _current_lang
    if lang in SUPPORTED_LANGUAGES:
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
    if lang in SUPPORTED_LANGUAGES:
        set_language(lang)
    else:
        # Auto-detect from LANG env var
        system_lang = os.environ.get("LANG", "").lower()
        if "ja" in system_lang:
            set_language("ja")
        elif "zh" in system_lang:
            set_language("zh")
        elif "ko" in system_lang:
            set_language("ko")
        elif "pt" in system_lang:
            set_language("pt")
        elif "tr" in system_lang:
            set_language("tr")
        else:
            set_language("ja")  # default to Japanese per project convention


init_language_from_env()
