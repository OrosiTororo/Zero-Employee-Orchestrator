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
    # -- Security --
    "security_injection_detected": {
        "ja": "プロンプトインジェクションを検出しました（レベル: {level}）",
        "en": "Prompt injection detected (level: {level})",
        "zh": "检测到提示注入（级别：{level}）",
        "ko": "프롬프트 인젝션 감지 (수준: {level})",
        "pt": "Injeção de prompt detectada (nível: {level})",
        "tr": "Prompt enjeksiyonu algılandı (seviye: {level})",
    },
    "security_pii_detected": {
        "ja": "個人情報が {count} 件検出されました。マスキングを適用します。",
        "en": "{count} PII item(s) detected. Masking applied.",
        "zh": "检测到 {count} 项个人信息。已应用掩码。",
        "ko": "개인정보 {count}건이 감지되었습니다. 마스킹이 적용됩니다.",
        "pt": "{count} item(ns) de PII detectado(s). Mascaramento aplicado.",
        "tr": "{count} kişisel veri tespit edildi. Maskeleme uygulandı.",
    },
    "security_sandbox_blocked": {
        "ja": "ファイルアクセスがブロックされました: {path}",
        "en": "File access blocked: {path}",
        "zh": "文件访问被阻止：{path}",
        "ko": "파일 접근이 차단되었습니다: {path}",
        "pt": "Acesso ao arquivo bloqueado: {path}",
        "tr": "Dosya erişimi engellendi: {path}",
    },
    "security_approval_needed": {
        "ja": "この操作は承認が必要です: {category}",
        "en": "This operation requires approval: {category}",
        "zh": "此操作需要审批：{category}",
        "ko": "이 작업은 승인이 필요합니다: {category}",
        "pt": "Esta operação requer aprovação: {category}",
        "tr": "Bu işlem onay gerektiriyor: {category}",
    },
    "security_data_protected": {
        "ja": "データ保護ポリシーによりブロックされました",
        "en": "Blocked by data protection policy",
        "zh": "被数据保护策略阻止",
        "ko": "데이터 보호 정책에 의해 차단됨",
        "pt": "Bloqueado pela política de proteção de dados",
        "tr": "Veri koruma politikası tarafından engellendi",
    },
    "security_redteam_passed": {
        "ja": "セキュリティテスト合格: {passed}/{total}",
        "en": "Security tests passed: {passed}/{total}",
        "zh": "安全测试通过：{passed}/{total}",
        "ko": "보안 테스트 통과: {passed}/{total}",
        "pt": "Testes de segurança aprovados: {passed}/{total}",
        "tr": "Güvenlik testleri geçti: {passed}/{total}",
    },
    # -- Settings --
    "settings_language": {
        "ja": "言語設定",
        "en": "Language Settings",
        "zh": "语言设置",
        "ko": "언어 설정",
        "pt": "Configurações de Idioma",
        "tr": "Dil Ayarları",
    },
    "settings_provider": {
        "ja": "LLM プロバイダー設定",
        "en": "LLM Provider Settings",
        "zh": "LLM 提供商设置",
        "ko": "LLM 프로바이더 설정",
        "pt": "Configurações do Provedor LLM",
        "tr": "LLM Sağlayıcı Ayarları",
    },
    "settings_security": {
        "ja": "セキュリティ設定",
        "en": "Security Settings",
        "zh": "安全设置",
        "ko": "보안 설정",
        "pt": "Configurações de Segurança",
        "tr": "Güvenlik Ayarları",
    },
    "settings_saved": {
        "ja": "設定を保存しました",
        "en": "Settings saved",
        "zh": "设置已保存",
        "ko": "설정이 저장되었습니다",
        "pt": "Configurações salvas",
        "tr": "Ayarlar kaydedildi",
    },
    # -- Navigation --
    "nav_dashboard": {
        "ja": "ダッシュボード",
        "en": "Dashboard",
        "zh": "仪表板",
        "ko": "대시보드",
        "pt": "Painel",
        "tr": "Kontrol Paneli",
    },
    "nav_tickets": {
        "ja": "チケット",
        "en": "Tickets",
        "zh": "工单",
        "ko": "티켓",
        "pt": "Tickets",
        "tr": "Biletler",
    },
    "nav_approvals": {
        "ja": "承認管理",
        "en": "Approvals",
        "zh": "审批管理",
        "ko": "승인 관리",
        "pt": "Aprovações",
        "tr": "Onaylar",
    },
    "nav_audit": {
        "ja": "監査ログ",
        "en": "Audit Log",
        "zh": "审计日志",
        "ko": "감사 로그",
        "pt": "Log de Auditoria",
        "tr": "Denetim Günlüğü",
    },
    "nav_settings": {
        "ja": "設定",
        "en": "Settings",
        "zh": "设置",
        "ko": "설정",
        "pt": "Configurações",
        "tr": "Ayarlar",
    },
    "nav_skills": {
        "ja": "スキル管理",
        "en": "Skills",
        "zh": "技能管理",
        "ko": "스킬 관리",
        "pt": "Skills",
        "tr": "Beceriler",
    },
    "nav_plugins": {
        "ja": "プラグイン",
        "en": "Plugins",
        "zh": "插件",
        "ko": "플러그인",
        "pt": "Plugins",
        "tr": "Eklentiler",
    },
    "nav_marketplace": {
        "ja": "マーケットプレイス",
        "en": "Marketplace",
        "zh": "市场",
        "ko": "마켓플레이스",
        "pt": "Marketplace",
        "tr": "Pazar Yeri",
    },
    # -- Common actions --
    "action_save": {
        "ja": "保存",
        "en": "Save",
        "zh": "保存",
        "ko": "저장",
        "pt": "Salvar",
        "tr": "Kaydet",
    },
    "action_cancel": {
        "ja": "キャンセル",
        "en": "Cancel",
        "zh": "取消",
        "ko": "취소",
        "pt": "Cancelar",
        "tr": "İptal",
    },
    "action_delete": {
        "ja": "削除",
        "en": "Delete",
        "zh": "删除",
        "ko": "삭제",
        "pt": "Excluir",
        "tr": "Sil",
    },
    "action_edit": {
        "ja": "編集",
        "en": "Edit",
        "zh": "编辑",
        "ko": "편집",
        "pt": "Editar",
        "tr": "Düzenle",
    },
    "action_create": {
        "ja": "作成",
        "en": "Create",
        "zh": "创建",
        "ko": "생성",
        "pt": "Criar",
        "tr": "Oluştur",
    },
    "action_approve": {
        "ja": "承認",
        "en": "Approve",
        "zh": "审批",
        "ko": "승인",
        "pt": "Aprovar",
        "tr": "Onayla",
    },
    "action_reject": {
        "ja": "却下",
        "en": "Reject",
        "zh": "拒绝",
        "ko": "거부",
        "pt": "Rejeitar",
        "tr": "Reddet",
    },
    "action_retry": {
        "ja": "再試行",
        "en": "Retry",
        "zh": "重试",
        "ko": "재시도",
        "pt": "Tentar Novamente",
        "tr": "Yeniden Dene",
    },
    # -- Skill / Plugin / Extension --
    "skill_installed": {
        "ja": "スキルをインストールしました: {name}",
        "en": "Skill installed: {name}",
        "zh": "已安装技能：{name}",
        "ko": "스킬이 설치되었습니다: {name}",
        "pt": "Skill instalado: {name}",
        "tr": "Beceri yüklendi: {name}",
    },
    "skill_generated": {
        "ja": "スキルを自動生成しました: {name}",
        "en": "Skill auto-generated: {name}",
        "zh": "已自动生成技能：{name}",
        "ko": "스킬이 자동 생성되었습니다: {name}",
        "pt": "Skill gerado automaticamente: {name}",
        "tr": "Beceri otomatik oluşturuldu: {name}",
    },
    "plugin_loaded": {
        "ja": "プラグインをロードしました: {name}",
        "en": "Plugin loaded: {name}",
        "zh": "已加载插件：{name}",
        "ko": "플러그인이 로드되었습니다: {name}",
        "pt": "Plugin carregado: {name}",
        "tr": "Eklenti yüklendi: {name}",
    },
    # -- Server / health --
    "server_starting": {
        "ja": "サーバーを起動中...",
        "en": "Starting server...",
        "zh": "正在启动服务器...",
        "ko": "서버 시작 중...",
        "pt": "Iniciando servidor...",
        "tr": "Sunucu başlatılıyor...",
    },
    "server_ready": {
        "ja": "サーバー起動完了: http://localhost:{port}",
        "en": "Server ready: http://localhost:{port}",
        "zh": "服务器就绪：http://localhost:{port}",
        "ko": "서버 준비 완료: http://localhost:{port}",
        "pt": "Servidor pronto: http://localhost:{port}",
        "tr": "Sunucu hazır: http://localhost:{port}",
    },
    "server_shutdown": {
        "ja": "サーバーを停止しました",
        "en": "Server stopped",
        "zh": "服务器已停止",
        "ko": "서버가 중지되었습니다",
        "pt": "Servidor parado",
        "tr": "Sunucu durduruldu",
    },
    "health_ok": {
        "ja": "ヘルスチェック: 正常",
        "en": "Health check: OK",
        "zh": "健康检查：正常",
        "ko": "헬스 체크: 정상",
        "pt": "Verificação de saúde: OK",
        "tr": "Sağlık kontrolü: Tamam",
    },
    "health_degraded": {
        "ja": "ヘルスチェック: 一部劣化（{detail}）",
        "en": "Health check: degraded ({detail})",
        "zh": "健康检查：部分降级（{detail}）",
        "ko": "헬스 체크: 일부 저하 ({detail})",
        "pt": "Verificação de saúde: degradado ({detail})",
        "tr": "Sağlık kontrolü: bozulmuş ({detail})",
    },
    # -- Budget / cost --
    "budget_exceeded": {
        "ja": "予算上限に達しました（使用額: ${spent}, 上限: ${limit}）",
        "en": "Budget limit reached (spent: ${spent}, limit: ${limit})",
        "zh": "已达预算上限（已用：${spent}，上限：${limit}）",
        "ko": "예산 한도에 도달했습니다 (사용: ${spent}, 한도: ${limit})",
        "pt": "Limite de orçamento atingido (gasto: ${spent}, limite: ${limit})",
        "tr": "Bütçe limitine ulaşıldı (harcanan: ${spent}, limit: ${limit})",
    },
    "cost_estimate": {
        "ja": "推定コスト: ${cost}（モデル: {model}）",
        "en": "Estimated cost: ${cost} (model: {model})",
        "zh": "预估成本：${cost}（模型：{model}）",
        "ko": "예상 비용: ${cost} (모델: {model})",
        "pt": "Custo estimado: ${cost} (modelo: {model})",
        "tr": "Tahmini maliyet: ${cost} (model: {model})",
    },
    # -- Judge Layer --
    "judge_pass": {
        "ja": "品質検証合格（スコア: {score}）",
        "en": "Quality check passed (score: {score})",
        "zh": "质量验证通过（分数：{score}）",
        "ko": "품질 검증 통과 (점수: {score})",
        "pt": "Verificação de qualidade aprovada (pontuação: {score})",
        "tr": "Kalite kontrolü geçti (puan: {score})",
    },
    "judge_fail": {
        "ja": "品質検証不合格（理由: {reason}）→ Re-Propose を開始",
        "en": "Quality check failed ({reason}) → starting Re-Propose",
        "zh": "质量验证未通过（{reason}）→ 开始重新提案",
        "ko": "품질 검증 실패 ({reason}) → Re-Propose 시작",
        "pt": "Verificação falhou ({reason}) → iniciando Re-Propose",
        "tr": "Kalite kontrolü başarısız ({reason}) → Yeniden Öneri başlatılıyor",
    },
    # -- Browser Assist --
    "browser_connected": {
        "ja": "ブラウザアシストに接続しました",
        "en": "Connected to Browser Assist",
        "zh": "已连接到浏览器助手",
        "ko": "브라우저 어시스트에 연결되었습니다",
        "pt": "Conectado ao Browser Assist",
        "tr": "Tarayıcı Yardımcısı'na bağlanıldı",
    },
    "browser_screenshot": {
        "ja": "スクリーンショットを分析中...",
        "en": "Analyzing screenshot...",
        "zh": "正在分析截图...",
        "ko": "스크린샷 분석 중...",
        "pt": "Analisando captura de tela...",
        "tr": "Ekran görüntüsü analiz ediliyor...",
    },
}


# ---------------------------------------------------------------------------
# Translation function
# ---------------------------------------------------------------------------

_current_lang: str = "en"


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
            set_language("en")  # default to English for wider adoption


init_language_from_env()
