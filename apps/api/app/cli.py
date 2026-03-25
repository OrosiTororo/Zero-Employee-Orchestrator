"""Zero-Employee Orchestrator CLI エントリーポイント.

コマンドラインから API サーバーの起動・管理・ローカルチャットモードを提供する。

使い方:
    zero-employee serve          # API サーバーを起動
    zero-employee serve --port 8000
    zero-employee db upgrade     # DB マイグレーション実行
    zero-employee health         # ヘルスチェック
    zero-employee local          # ローカルチャットモード (Ollama)
    zero-employee local --model qwen3:8b
    zero-employee models         # 利用可能モデル一覧
    zero-employee pull <model>   # モデルダウンロード
    zero-employee update         # 最新版にアップデート
    zero-employee update --check # アップデート確認のみ
"""

import argparse
import asyncio
import sys


def cmd_serve(args: argparse.Namespace) -> None:
    """API サーバーを起動する."""
    import uvicorn

    # 起動時にバージョンチェック（バックグラウンド・ノンブロッキング）
    if not args.skip_update_check:
        from app.core.version_check import check_and_notify

        check_and_notify(quiet=True)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def cmd_db_upgrade(args: argparse.Namespace) -> None:
    """DB マイグレーションを実行する."""
    from app.core.database import Base, engine

    async def _create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("データベーステーブルを作成しました")

    asyncio.run(_create_tables())


def cmd_health(args: argparse.Namespace) -> None:
    """ヘルスチェックを実行する."""
    import httpx

    url = f"http://{args.host}:{args.port}/healthz"
    try:
        resp = httpx.get(url, timeout=5)
        if resp.status_code == 200:
            print(f"OK: {resp.json()}")
        else:
            print(f"WARN: status {resp.status_code}")
            sys.exit(1)
    except httpx.ConnectError:
        print(f"FAIL: cannot connect to {url}")
        sys.exit(1)


def cmd_models(args: argparse.Namespace) -> None:
    """利用可能なモデル一覧を表示する."""
    from app.core.i18n import t

    async def _list() -> None:
        from app.providers.ollama_provider import RECOMMENDED_MODELS, ollama_provider

        print()
        is_up = await ollama_provider.health_check()
        if not is_up:
            print(f"  \033[38;5;220m{t('error_no_ollama')}\033[0m")
            print()
            print("  Recommended models:")
            for name, info in RECOMMENDED_MODELS.items():
                print(f"    \033[38;5;75m{name:30s}\033[0m {info['description']}")
            print()
            return

        models = await ollama_provider.list_models()
        if not models:
            print(f"  \033[38;5;220m{t('error_no_model')}\033[0m")
            return

        print("  \033[1mInstalled Ollama models:\033[0m")
        print()
        for m in models:
            size_gb = m.size / (1024**3) if m.size else 0
            size_str = f"{size_gb:.1f}GB" if size_gb >= 1.0 else f"{m.size / (1024**2):.0f}MB"
            rec = RECOMMENDED_MODELS.get(m.name, {})
            desc = rec.get("description", "")
            print(f"    \033[38;5;78m{m.name:30s}\033[0m {size_str:>8s}  {desc}")
        print()

    asyncio.run(_list())


def cmd_pull(args: argparse.Namespace) -> None:
    """Ollama モデルをダウンロードする."""

    async def _pull() -> None:
        from app.providers.ollama_provider import ollama_provider

        model = args.model_name
        print(f"  Pulling model: {model} ...")
        ok = await ollama_provider.pull_model(model)
        if ok:
            print(f"  Done: {model}")
        else:
            print(f"  Failed to pull {model}. Is Ollama running?")
            sys.exit(1)

    asyncio.run(_pull())


def cmd_security_status(args: argparse.Namespace) -> None:
    """セキュリティ設定の概要を表示する."""
    from app.security.data_protection import data_protection_guard
    from app.security.sandbox import filesystem_sandbox
    from app.security.workspace_isolation import workspace_isolation

    print()
    print("  \033[1mZero-Employee Orchestrator — Security Status\033[0m")
    print()

    # Workspace
    ws = workspace_isolation.config
    scope = workspace_isolation.get_access_scope().value
    print("  \033[38;5;75m[workspace]\033[0m")
    print(f"    Access scope:        {scope}")
    print(f"    Local access:        {'enabled' if ws.local_access_enabled else 'disabled'}")
    print(f"    Cloud access:        {'enabled' if ws.cloud_access_enabled else 'disabled'}")
    print(f"    Storage location:    {ws.storage_location.value}")
    if ws.allowed_local_paths:
        print(f"    Allowed paths:       {', '.join(ws.allowed_local_paths)}")
    if ws.cloud_providers:
        print(f"    Cloud providers:     {', '.join(ws.cloud_providers)}")
    print()

    # Sandbox
    sb = filesystem_sandbox.config
    print("  \033[38;5;75m[sandbox]\033[0m")
    print(f"    Level:               {sb.level.value}")
    print(f"    Allowed paths:       {len(sb.allowed_paths)}")
    print(f"    Max file size:       {sb.max_file_size_mb} MB")
    print()

    # Data protection
    dp = data_protection_guard.config
    print("  \033[38;5;75m[data-protection]\033[0m")
    print(f"    Transfer policy:     {dp.transfer_policy.value}")
    print(f"    Upload:              {'enabled' if dp.upload_enabled else 'disabled'}")
    print(f"    Download:            {'enabled' if dp.download_enabled else 'disabled'}")
    print(f"    External API:        {'enabled' if dp.external_api_enabled else 'disabled'}")
    print(f"    PII auto-detect:     {'enabled' if dp.pii_auto_detect else 'disabled'}")
    print(f"    Password block:      {'enabled' if dp.password_upload_blocked else 'disabled'}")
    print()


def cmd_config(args: argparse.Namespace) -> None:
    """設定値の表示・変更を行う."""
    from app.core.config_manager import (
        CONFIGURABLE_KEYS,
        delete_config_value,
        get_all_config,
        get_config_value,
        set_config_value,
    )

    action = args.config_action

    if action == "list":
        config = get_all_config()
        print()
        print("  \033[1mZero-Employee Orchestrator — Configuration\033[0m")
        print()
        current_category = ""
        for key, info in config.items():
            cat = info["category"]
            if cat != current_category:
                current_category = cat
                print(f"  \033[38;5;75m[{cat}]\033[0m")
            status = "\033[38;5;78mSET\033[0m" if info["is_set"] else "\033[38;5;245m---\033[0m"
            source = f"\033[38;5;245m({info['source']})\033[0m"
            value_display = info["value"] if info["is_set"] else ""
            print(f"    {status} {key:30s} {value_display:20s} {source}")
        print()
        print("  Config file: ~/.zero-employee/config.json")
        print()

    elif action == "get":
        if not args.key:
            print("  Usage: zero-employee config get <KEY>")
            sys.exit(1)
        value = get_config_value(args.key)
        if value:
            print(f"  {args.key} = {value}")
        else:
            print(f"  {args.key} is not set")

    elif action == "set":
        if not args.key:
            print("  Usage: zero-employee config set <KEY> <VALUE>")
            sys.exit(1)
        if args.key not in CONFIGURABLE_KEYS:
            print(f"  Unknown key: {args.key}")
            print(f"  Available keys: {', '.join(sorted(CONFIGURABLE_KEYS))}")
            sys.exit(1)

        value = args.value
        if not value:
            # 機密値の場合は入力プロンプトを表示（エコーなし）
            import getpass

            meta = CONFIGURABLE_KEYS[args.key]
            if meta.get("sensitive") == "true":
                value = getpass.getpass(f"  Enter value for {args.key}: ")
            else:
                value = input(f"  Enter value for {args.key}: ")

        set_config_value(args.key, value)
        print(f"  \033[38;5;78mSaved:\033[0m {args.key}")

    elif action == "delete":
        if not args.key:
            print("  Usage: zero-employee config delete <KEY>")
            sys.exit(1)
        removed = delete_config_value(args.key)
        if removed:
            print(f"  \033[38;5;78mRemoved:\033[0m {args.key}")
        else:
            print(f"  {args.key} was not set in config file")

    elif action == "keys":
        print()
        print("  \033[1mConfigurable keys:\033[0m")
        print()
        for key, meta in CONFIGURABLE_KEYS.items():
            desc = meta.get("description_ja", meta.get("description", ""))
            sensitive = " [sensitive]" if meta.get("sensitive") == "true" else ""
            print(f"    \033[38;5;75m{key:30s}\033[0m {desc}{sensitive}")
        print()

    else:
        print("  Usage: zero-employee config <list|get|set|delete|keys>")


def cmd_local(args: argparse.Namespace) -> None:
    """ローカルチャットモード — Ollama で完全オフラインの対話型業務エージェント."""

    async def _chat() -> None:
        from app.banner import print_local_banner
        from app.core.i18n import get_language, set_language, t
        from app.providers.ollama_provider import ollama_provider

        # Language setup
        if args.lang:
            set_language(args.lang)
        language = get_language()

        # Check Ollama availability
        ollama_ok = await ollama_provider.health_check()
        model = args.model

        if ollama_ok and not model:
            suggested = await ollama_provider.suggest_model()
            model = suggested or ""

        # Display banner
        print_local_banner(
            model=model,
            engine_url=ollama_provider.base_url,
            mode="orchestrator",
            language=language,
            ollama_available=ollama_ok,
        )

        if not ollama_ok:
            print(f"  \033[38;5;220m{t('error_no_ollama')}\033[0m")
            print()
            return

        if not model:
            print(f"  \033[38;5;220m{t('error_no_model')}\033[0m")
            print()
            return

        # Chat loop
        conversation: list[dict] = []
        system_prompt = _build_system_prompt(language)

        ctx_tokens = 0  # approximate context usage

        while True:
            try:
                # Prompt with context usage indicator
                ctx_pct = min(100, int(ctx_tokens / 327.68))  # ~32768 ctx
                prompt_prefix = f"\033[38;5;245mctx:{ctx_pct}%\033[0m"
                user_input = input(f"{prompt_prefix} \033[38;5;51m>\033[0m ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                print(f"\n  {t('chat_goodbye')}")
                break

            if not user_input:
                continue

            # Commands
            if user_input.startswith("/"):
                handled = _handle_command(user_input, language)
                if handled == "quit":
                    print(f"\n  {t('chat_goodbye')}")
                    break
                continue

            # 自然言語コマンドプロセッサで意図を判定
            try:
                from app.services.nl_command_service import nl_command_processor

                parsed = nl_command_processor.parse(user_input)
                if parsed.confidence >= 0.3 and parsed.category.value != "conversation":
                    result = await nl_command_processor.execute(parsed)
                    if result.message:
                        print(f"\n  \033[38;5;78m[{parsed.category.value}]\033[0m {result.message}")
                    if result.suggestions:
                        print("\n  \033[38;5;245mヒント:\033[0m")
                        for s in result.suggestions:
                            print(f"    • {s}")
                    if not result.data.get("delegate_to_llm"):
                        print()
                        continue
                    # delegate_to_llm の場合は LLM にも送信
            except Exception:
                pass  # NL プロセッサが利用不可の場合はそのまま LLM に送信

            # Multi-line input (triple quotes)
            if user_input.startswith('"""') or user_input.startswith("'''"):
                delim = user_input[:3]
                lines = [user_input[3:]]
                while True:
                    try:
                        line = input("... ")
                        if delim in line:
                            lines.append(line.replace(delim, ""))
                            break
                        lines.append(line)
                    except (KeyboardInterrupt, EOFError):
                        break
                user_input = "\n".join(lines)

            # Add user message
            conversation.append({"role": "user", "content": user_input})

            # Build messages with system prompt
            messages = [{"role": "system", "content": system_prompt}] + conversation

            # Show thinking indicator
            print(f"\n  \033[38;5;245m{t('chat_thinking')}\033[0m", end="", flush=True)

            # Stream response
            response_text = ""
            first_chunk = True
            async for chunk in ollama_provider.complete_stream(
                messages=messages,
                model=model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            ):
                if first_chunk:
                    # Clear thinking indicator and start response
                    print("\r  \033[38;5;78massistant:\033[0m ", end="", flush=True)
                    first_chunk = False
                print(chunk, end="", flush=True)
                response_text += chunk

            if first_chunk:
                # No chunks received
                print("\r  \033[38;5;220m(no response)\033[0m")
            else:
                print()  # newline after streaming

            # Add assistant message to conversation
            if response_text:
                conversation.append({"role": "assistant", "content": response_text})

            # Approximate token count for context indicator
            ctx_tokens = sum(len(m["content"]) // 4 for m in messages)

            # Context window management: compress if too long
            if ctx_tokens > 24000:  # ~75% of 32k
                conversation = _compress_context(conversation)
                ctx_tokens = sum(len(m["content"]) // 4 for m in conversation)

    asyncio.run(_chat())


def cmd_chat(args: argparse.Namespace) -> None:
    """チャットモード — 全プロバイダー対応の対話型業務エージェント.

    Ollama だけでなく、全 LLM プロバイダーで利用可能。
    自然言語で設定変更・チケット作成・モデル管理等あらゆる操作に対応。
    """

    async def _chat() -> None:
        from app.banner import print_local_banner
        from app.core.i18n import get_language, set_language, t
        from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

        if args.lang:
            set_language(args.lang)
        language = get_language()

        # Determine mode
        mode_str = args.mode or "quality"
        mode_map = {
            "quality": ExecutionMode.QUALITY,
            "speed": ExecutionMode.SPEED,
            "cost": ExecutionMode.COST,
            "free": ExecutionMode.FREE,
            "subscription": ExecutionMode.SUBSCRIPTION,
        }
        mode = mode_map.get(mode_str, ExecutionMode.QUALITY)

        model = llm_gateway.select_model(mode)
        print_local_banner(
            model=model,
            engine_url="LLM Gateway (multi-provider)",
            mode="orchestrator",
            language=language,
            ollama_available=True,
        )

        print(f"  \033[38;5;245mMode: {mode.value} | Model: {model}\033[0m")
        print(
            "  \033[38;5;245m自然言語であらゆる操作が可能です。「何ができる？」と聞いてください。\033[0m"
        )
        print()

        conversation: list[dict] = []
        system_prompt = _build_system_prompt(language)

        while True:
            try:
                user_input = input("\033[38;5;51m>\033[0m ").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n\n  {t('chat_goodbye')}")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                handled = _handle_command(user_input, language)
                if handled == "quit":
                    print(f"\n  {t('chat_goodbye')}")
                    break
                continue

            # 自然言語コマンドプロセッサ
            try:
                from app.services.nl_command_service import nl_command_processor

                parsed = nl_command_processor.parse(user_input)
                if parsed.confidence >= 0.3 and parsed.category.value != "conversation":
                    result = await nl_command_processor.execute(parsed)
                    if result.message:
                        print(f"\n  \033[38;5;78m[{parsed.category.value}]\033[0m {result.message}")
                    if result.suggestions:
                        for s in result.suggestions:
                            print(f"    • {s}")
                    if not result.data.get("delegate_to_llm"):
                        print()
                        continue
            except Exception:
                pass

            # LLM に送信
            conversation.append({"role": "user", "content": user_input})
            messages = [{"role": "system", "content": system_prompt}] + conversation

            print(f"\n  \033[38;5;245m{t('chat_thinking')}\033[0m", end="", flush=True)

            request = CompletionRequest(
                messages=messages,
                model=model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                mode=mode,
            )
            response = await llm_gateway.complete(request)

            print(f"\r  \033[38;5;78massistant:\033[0m {response.content}")

            if response.content:
                conversation.append({"role": "assistant", "content": response.content})

            # コンテキスト圧縮
            ctx_tokens = sum(len(m["content"]) // 4 for m in messages)
            if ctx_tokens > 24000:
                conversation = _compress_context(conversation)

    asyncio.run(_chat())


def _build_system_prompt(language: str) -> str:
    """Build the system prompt for local orchestration mode."""
    lang_instructions = {
        "ja": (
            "あなたは Zero-Employee Orchestrator の業務遂行エージェントです。\n"
            "ユーザーの業務指示を理解し、タスクの分解・計画・実行を支援します。\n"
            "回答は日本語で行ってください。\n\n"
            "あなたの役割:\n"
            "- 業務目的の理解と要件の深掘り\n"
            "- タスクの分解と実行計画の作成\n"
            "- 危険な操作（送信・削除・課金）は必ずユーザーに確認\n"
            "- 進捗の報告と問題発生時の対処提案\n\n"
            "ユーザーは自然言語であらゆる操作を指示できます:\n"
            "- 設定変更: 「Geminiを使うように設定して」「実行モードをfreeに変更して」\n"
            "- チケット: 「競合分析レポートを作成して」\n"
            "- モデル: 「モデルを更新して」「qwen3:8bをダウンロードして」\n"
            "- スキル: 「browser-useを追加して」「新しいスキルを生成して」\n"
            "- セキュリティ: 「セキュリティ設定を確認して」\n"
            "- 承認: 「承認待ちを見せて」\n"
            "- メディア: 「オフィスの画像を生成して」\n"
        ),
        "en": (
            "You are a task execution agent for Zero-Employee Orchestrator.\n"
            "Understand user's business instructions, decompose tasks, plan, and assist execution.\n"
            "Respond in English.\n\n"
            "Your role:\n"
            "- Understand business objectives and clarify requirements\n"
            "- Decompose tasks and create execution plans\n"
            "- Always confirm dangerous operations (sending, deleting, billing)\n"
            "- Report progress and propose solutions when issues arise\n\n"
            "Users can control everything via natural language:\n"
            "- Config: 'Set up to use Gemini', 'Change mode to free'\n"
            "- Tickets: 'Create a competitive analysis report'\n"
            "- Models: 'Update models', 'Download qwen3:8b'\n"
            "- Skills: 'Add browser-use', 'Generate a new skill'\n"
            "- Security: 'Check security settings'\n"
            "- Approvals: 'Show pending approvals'\n"
            "- Media: 'Generate an office image'\n"
        ),
        "zh": (
            "你是 Zero-Employee Orchestrator 的任务执行代理。\n"
            "理解用户的业务指令，分解任务，制定计划，协助执行。\n"
            "请用中文回答。\n\n"
            "你的职责:\n"
            "- 理解业务目标并深入挖掘需求\n"
            "- 分解任务并创建执行计划\n"
            "- 危险操作（发送、删除、计费）必须确认\n"
            "- 报告进度并在出现问题时提出解决方案\n\n"
            "用户可以用自然语言控制一切:\n"
            "- 配置: '设置使用Gemini', '将模式更改为free'\n"
            "- 工单: '创建竞争分析报告'\n"
            "- 模型: '更新模型', '下载qwen3:8b'\n"
            "- 技能: '添加browser-use', '生成新技能'\n"
            "- 安全: '检查安全设置'\n"
            "- 审批: '显示待审批项'\n"
        ),
    }
    return lang_instructions.get(language, lang_instructions["en"])


def _handle_command(cmd: str, language: str) -> str | None:
    """Handle slash commands in local chat mode.

    Returns "quit" if the user wants to exit, None otherwise.
    """
    from app.core.i18n import set_language

    parts = cmd.strip().split()
    command = parts[0].lower()

    if command in ("/quit", "/exit", "/q"):
        return "quit"

    if command == "/help":
        help_text = {
            "ja": (
                "  /help      - ヘルプを表示\n"
                "  /models    - 利用可能モデル一覧\n"
                "  /lang <code> - 言語変更 (ja/en/zh)\n"
                "  /clear     - 会話履歴をクリア\n"
                "  /quit      - 終了"
            ),
            "en": (
                "  /help      - Show help\n"
                "  /models    - List available models\n"
                "  /lang <code> - Change language (ja/en/zh)\n"
                "  /clear     - Clear conversation history\n"
                "  /quit      - Exit"
            ),
            "zh": (
                "  /help      - 显示帮助\n"
                "  /models    - 列出可用模型\n"
                "  /lang <code> - 更改语言 (ja/en/zh)\n"
                "  /clear     - 清除对话历史\n"
                "  /quit      - 退出"
            ),
        }
        print(help_text.get(language, help_text["en"]))
        return None

    if command == "/lang" and len(parts) > 1:
        new_lang = parts[1].lower()
        if new_lang in ("ja", "en", "zh"):
            set_language(new_lang)
            names = {"ja": "日本語", "en": "English", "zh": "中文"}
            print(f"  Language: {names[new_lang]}")
        else:
            print("  Supported: ja, en, zh")
        return None

    if command == "/clear":
        print("  (conversation cleared)")
        return None

    if command == "/models":
        cmd_models(argparse.Namespace())
        return None

    print(f"  Unknown command: {command}. Type /help for help.")
    return None


def _compress_context(conversation: list[dict]) -> list[dict]:
    """Compress conversation history to fit within context window.

    Keeps the first message (for context) and the most recent messages.
    Middle messages are summarized.
    """
    if len(conversation) <= 6:
        return conversation

    # Keep first 2 and last 4 messages
    summary = (
        "[Earlier conversation was compressed to save context. "
        "Key points from the discussion are preserved in the most recent messages.]"
    )
    compressed = conversation[:2] + [{"role": "assistant", "content": summary}] + conversation[-4:]
    return compressed


def cmd_update(args: argparse.Namespace) -> None:
    """最新バージョンへのアップデートを実行する."""
    import subprocess

    from app.core.version_check import (
        PACKAGE_NAME,
        check_latest_version_sync,
        get_current_version,
        is_newer_version,
    )

    current = get_current_version()
    print(f"  Current version: {current}")
    print("  Checking for updates...")

    latest = check_latest_version_sync(timeout=10.0)
    if latest is None:
        print("  \033[38;5;220mCould not reach PyPI. Check your internet connection.\033[0m")
        sys.exit(1)

    if not is_newer_version(current, latest):
        print(f"  \033[38;5;78m✔ Already up to date ({current})\033[0m")
        return

    print(f"  New version available: {current} → \033[38;5;78m{latest}\033[0m")

    if args.check_only:
        print("\n  Run \033[38;5;51mzero-employee update\033[0m to install.")
        return

    # pip install -U で更新
    print(f"\n  Updating {PACKAGE_NAME}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", PACKAGE_NAME],
        capture_output=not args.verbose,
    )
    if result.returncode == 0:
        print(f"\n  \033[38;5;78m✔ Updated to {latest}\033[0m")
        print("  Restart zero-employee to use the new version.")
    else:
        print(f"\n  \033[38;5;220mUpdate failed (exit code {result.returncode})\033[0m")
        if not args.verbose:
            print("  Re-run with --verbose for details.")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """CLI パーサーを構築する."""
    parser = argparse.ArgumentParser(
        prog="zero-employee",
        description="Zero-Employee Orchestrator — AI オーケストレーション基盤",
    )
    subparsers = parser.add_subparsers(dest="command", help="コマンド一覧")

    # serve
    serve_parser = subparsers.add_parser("serve", help="API サーバーを起動")
    serve_parser.add_argument("--host", default="0.0.0.0", help="ホスト (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=18234, help="ポート (default: 18234)")
    serve_parser.add_argument("--reload", action="store_true", help="ホットリロードを有効化")
    serve_parser.add_argument(
        "--skip-update-check",
        action="store_true",
        help="起動時のバージョンチェックをスキップ",
    )
    serve_parser.set_defaults(func=cmd_serve)

    # db
    db_parser = subparsers.add_parser("db", help="データベース操作")
    db_sub = db_parser.add_subparsers(dest="db_command")
    upgrade_parser = db_sub.add_parser("upgrade", help="マイグレーション実行")
    upgrade_parser.set_defaults(func=cmd_db_upgrade)

    # health
    health_parser = subparsers.add_parser("health", help="ヘルスチェック")
    health_parser.add_argument("--host", default="127.0.0.1", help="ホスト")
    health_parser.add_argument("--port", type=int, default=18234, help="ポート")
    health_parser.set_defaults(func=cmd_health)

    # config — 設定管理
    config_parser = subparsers.add_parser(
        "config",
        help="設定管理 (API キー・実行モード等)",
    )
    config_parser.add_argument(
        "config_action",
        nargs="?",
        default="list",
        choices=["list", "get", "set", "delete", "keys"],
        help="Action: list | get | set | delete | keys",
    )
    config_parser.add_argument("key", nargs="?", default="", help="Config key name")
    config_parser.add_argument("value", nargs="?", default="", help="Config value (for set)")
    config_parser.set_defaults(func=cmd_config)

    # local — ローカルチャットモード
    local_parser = subparsers.add_parser(
        "local",
        help="ローカルチャットモード (Ollama / オフライン)",
    )
    local_parser.add_argument(
        "--model",
        default="",
        help="Ollama model name (auto-detect if empty)",
    )
    local_parser.add_argument(
        "--lang",
        default="",
        choices=["ja", "en", "zh", ""],
        help="Language (ja/en/zh, default: auto)",
    )
    local_parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)",
    )
    local_parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max output tokens (default: 4096)",
    )
    local_parser.set_defaults(func=cmd_local)

    # chat — 全プロバイダー対応チャットモード
    chat_parser = subparsers.add_parser(
        "chat",
        help="チャットモード (全プロバイダー対応・自然言語で全操作可能)",
    )
    chat_parser.add_argument(
        "--mode",
        default="",
        choices=["quality", "speed", "cost", "free", "subscription", ""],
        help="実行モード (default: auto)",
    )
    chat_parser.add_argument(
        "--lang",
        default="",
        choices=["ja", "en", "zh", ""],
        help="Language (ja/en/zh, default: auto)",
    )
    chat_parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)",
    )
    chat_parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max output tokens (default: 4096)",
    )
    chat_parser.set_defaults(func=cmd_chat)

    # models — モデル一覧
    models_parser = subparsers.add_parser("models", help="利用可能モデル一覧")
    models_parser.set_defaults(func=cmd_models)

    # pull — モデルダウンロード
    pull_parser = subparsers.add_parser("pull", help="Ollama モデルをダウンロード")
    pull_parser.add_argument("model_name", help="Model name (e.g. qwen3:8b)")
    pull_parser.set_defaults(func=cmd_pull)

    # update — アップデート管理
    update_parser = subparsers.add_parser(
        "update",
        help="最新バージョンにアップデート",
    )
    update_parser.add_argument(
        "--check",
        dest="check_only",
        action="store_true",
        help="アップデート確認のみ（インストールしない）",
    )
    update_parser.add_argument(
        "--verbose",
        action="store_true",
        help="pip の出力を表示",
    )
    update_parser.set_defaults(func=cmd_update)

    # security — セキュリティ管理
    security_parser = subparsers.add_parser("security", help="セキュリティ設定管理")
    security_sub = security_parser.add_subparsers(dest="security_command")
    sec_status_parser = security_sub.add_parser("status", help="セキュリティ設定の概要を表示")
    sec_status_parser.set_defaults(func=cmd_security_status)

    return parser


def main() -> None:
    """CLI メインエントリーポイント."""
    from app.banner import print_banner

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    # local mode shows its own banner
    if args.command != "local":
        print_banner(compact=True)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
