"""Zero-Employee Orchestrator CLI entry point.

Provides API server startup, management, and local chat mode from the command line.

Usage:
    zero-employee serve          # Start the API server
    zero-employee serve --port 8000
    zero-employee db upgrade     # Run DB migration
    zero-employee health         # Health check
    zero-employee local          # Local chat mode (Ollama)
    zero-employee local --model qwen3:8b
    zero-employee models         # List available models
    zero-employee pull <model>   # Download a model
    zero-employee update         # Update to the latest version
    zero-employee update --check # Check for updates only
"""

import argparse
import asyncio
import os
import sys


def _find_and_chdir_api() -> None:
    """Ensure the working directory is the API root (where app/ lives).

    When installed as a package, the CLI may be invoked from any directory.
    This helper finds the correct API directory and changes into it so that
    ``uvicorn app.main:app`` can locate the module.
    """
    import os
    import pathlib

    # Already correct?
    if pathlib.Path("app/main.py").exists():
        return

    # Check common relative locations
    for candidate in [
        pathlib.Path(__file__).resolve().parents[1],  # apps/api (from app/cli.py)
        pathlib.Path.cwd() / "apps" / "api",  # project root
    ]:
        if (candidate / "app" / "main.py").exists():
            os.chdir(candidate)
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return


def _ensure_env_file() -> None:
    """Generate a default .env file if it doesn't exist."""
    import pathlib
    import secrets as _secrets

    env_path = pathlib.Path(".env")
    if env_path.exists():
        return

    secret = _secrets.token_urlsafe(32)
    env_path.write_text(
        f"DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db\n"
        f"SECRET_KEY={secret}\n"
        f"DEBUG=true\n"
        f'CORS_ORIGINS=["http://localhost:5173","http://localhost:3000",'
        f'"tauri://localhost","https://tauri.localhost","http://tauri.localhost"]\n'
        f"DEFAULT_EXECUTION_MODE=subscription\n"
        f"USE_G4F=true\n"
    )
    print("  .env file created with default settings")


async def _check_and_auto_pull_ollama(model: str) -> None:
    """Pull a default Ollama model if Ollama is running but has no models.

    This gives first-time users a working free LLM immediately without needing
    to run ``ollama pull`` manually.  Silently skips if Ollama is unavailable.
    """
    from app.core.i18n import t
    from app.providers.ollama_provider import ollama_provider

    try:
        is_up = await ollama_provider.health_check()
        if not is_up:
            return
        models = await ollama_provider.list_models()
        if models:
            return  # already has models, nothing to do
        print(f"  {t('ollama_auto_pull_start', model=model)}")
        ok = await ollama_provider.pull_model(model)
        if ok:
            print(f"  {t('ollama_auto_pull_done', model=model)}")
        else:
            print(f"  {t('ollama_auto_pull_failed', model=model)}")
    except Exception:
        pass  # non-blocking; never crash serve startup


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the API server."""
    import uvicorn

    _find_and_chdir_api()
    _ensure_env_file()

    # Version check at startup (background, non-blocking)
    if not args.skip_update_check:
        from app.core.version_check import check_and_notify

        check_and_notify(quiet=True)

    # Ollama auto-pull: if Ollama is running but has no models, pull default
    if not args.no_auto_pull:
        asyncio.run(_check_and_auto_pull_ollama(args.auto_pull_model))

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def cmd_db_upgrade(args: argparse.Namespace) -> None:
    """Run DB migration."""
    _find_and_chdir_api()
    _ensure_env_file()
    from app.core.database import Base, engine

    async def _create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created")

    asyncio.run(_create_tables())


def cmd_health(args: argparse.Namespace) -> None:
    """Run health check."""
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
    """Display list of available models."""
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
    """Download an Ollama model."""

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


def cmd_mcp(args: argparse.Namespace) -> None:
    """Inspect and test the built-in Model Context Protocol (MCP) server.

    Subcommands:
        mcp info         — show ZEO's advertised MCP capabilities
        mcp tools        — list registered MCP tools
        mcp call <name>  — call a tool locally (for quick smoke tests)
    """
    _find_and_chdir_api()

    action = getattr(args, "mcp_command", None) or "info"

    async def _run() -> None:
        from app.integrations.mcp_server import MCP_PROTOCOL_VERSION, mcp_server

        if action == "info":
            caps = mcp_server.get_capabilities()
            print()
            print("  \033[1mZero-Employee Orchestrator MCP Server\033[0m")
            print(
                f"  protocol:  \033[38;5;78m{MCP_PROTOCOL_VERSION}\033[0m"
                f"   server:  \033[38;5;78mv{caps['server_version']}\033[0m"
            )
            print(
                f"  tools:     {caps['tools_count']}   "
                f"resources: {caps['resources_count']}   "
                f"prompts:   {caps['prompts_count']}"
            )
            print()
            print("  \033[2mJSON-RPC endpoint:\033[0m  POST /api/v1/mcp/rpc")
            print("  \033[2mSSE endpoint:\033[0m       GET  /api/v1/mcp/sse")
            print("  \033[2mREST wrapper:\033[0m       GET  /api/v1/mcp/tools")
            print()
            return

        if action == "tools":
            result = await mcp_server.handle_list_tools()
            print()
            print("  \033[1mMCP tools\033[0m")
            for tool in result["tools"]:
                print(f"    \033[38;5;78m{tool['name']:24s}\033[0m {tool['description']}")
            print()
            return

        if action == "call":
            name = getattr(args, "tool_name", "")
            if not name:
                print("  Usage: zero-employee mcp call <tool_name> [--args JSON]")
                sys.exit(2)
            import json

            raw_args = getattr(args, "tool_args", "") or "{}"
            try:
                parsed = json.loads(raw_args)
            except json.JSONDecodeError as exc:
                print(f"  Invalid --args JSON: {exc}")
                sys.exit(2)
            result = await mcp_server.handle_call_tool(name, parsed)
            print()
            if result.get("isError"):
                print(f"  \033[38;5;220m{result.get('error', 'error')}\033[0m")
            else:
                for item in result.get("content", []):
                    print(f"  {item.get('text', '')}")
            print()
            return

        print(f"  Unknown mcp subcommand: {action}")
        sys.exit(2)

    asyncio.run(_run())


def cmd_security_status(args: argparse.Namespace) -> None:
    """Display security configuration summary."""
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
    """Display and modify configuration values."""
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
            # Show input prompt for sensitive values (no echo)
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
    """Local chat mode -- fully offline interactive business agent using Ollama."""
    _find_and_chdir_api()
    _ensure_env_file()

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

        # Chat loop with Neovim-inspired modes
        conversation: list[dict] = []
        system_prompt = _build_system_prompt(language)
        ctx_tokens = 0  # approximate context usage
        cli_mode = "NORMAL"  # NORMAL | INSERT | COMMAND

        # Color constants (ZEO palette / Neovim)
        _C_NORMAL = "\033[38;2;86;186;159m"  # success green
        _C_INSERT = "\033[38;2;0;122;204m"  # accent blue
        _C_COMMAND = "\033[38;2;243;215;104m"  # warning yellow
        _C_MUTED = "\033[38;2;110;118;129m"
        _C_ACCENT = "\033[38;2;0;122;204m"
        _C_RESET = "\033[0m"

        while True:
            try:
                ctx_pct = min(100, int(ctx_tokens / 327.68))  # ~32768 ctx
                mode_color = (
                    _C_NORMAL
                    if cli_mode == "NORMAL"
                    else _C_INSERT
                    if cli_mode == "INSERT"
                    else _C_COMMAND
                )
                prompt_prefix = (
                    f"{mode_color}{cli_mode}{_C_RESET} {_C_MUTED}ctx:{ctx_pct}%{_C_RESET}"
                )
                user_input = input(f"{prompt_prefix} {_C_ACCENT}>{_C_RESET} ").strip()
            except (KeyboardInterrupt, EOFError):
                if cli_mode == "INSERT":
                    # Ctrl+C in INSERT mode returns to NORMAL
                    cli_mode = "NORMAL"
                    print(f"\n  {_C_MUTED}-- NORMAL --{_C_RESET}")
                    continue
                print()
                print(f"\n  {t('chat_goodbye')}")
                break

            if not user_input:
                continue

            # Triple-quote enters INSERT mode (multi-line input)
            if user_input == '"""' or user_input == "'''":
                cli_mode = "INSERT"
                print(f'  {_C_INSERT}-- INSERT -- (enter """ to finish){_C_RESET}')
                lines = []
                while True:
                    try:
                        line = input(f"  {_C_INSERT}│{_C_RESET} ")
                    except (KeyboardInterrupt, EOFError):
                        break
                    if line.strip() in ('"""', "'''"):
                        break
                    lines.append(line)
                cli_mode = "NORMAL"
                user_input = "\n".join(lines)
                if not user_input.strip():
                    continue

            # Commands — enter COMMAND mode briefly
            if user_input.startswith("/"):
                cli_mode = "COMMAND"
                handled = _handle_command(user_input, language)
                cli_mode = "NORMAL"
                if handled == "quit":
                    print(f"\n  {t('chat_goodbye')}")
                    break
                continue

            # Determine intent using natural language command processor
            try:
                from app.services.nl_command_service import nl_command_processor

                parsed = nl_command_processor.parse(user_input)
                if parsed.confidence >= 0.3 and parsed.category.value != "conversation":
                    result = await nl_command_processor.execute(parsed)
                    if result.message:
                        print(f"\n  \033[38;5;78m[{parsed.category.value}]\033[0m {result.message}")
                    if result.suggestions:
                        print("\n  \033[38;5;245mHints:\033[0m")
                        for s in result.suggestions:
                            print(f"    • {s}")
                    if not result.data.get("delegate_to_llm"):
                        print()
                        continue
                    # If delegate_to_llm, also send to LLM
            except Exception:
                pass  # If NL processor is unavailable, send directly to LLM

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
    """Chat mode -- interactive business agent supporting all providers.

    Available with all LLM providers, not just Ollama.
    Supports all operations via natural language: config changes, ticket creation, model management, etc.
    """
    _find_and_chdir_api()
    _ensure_env_file()

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
            "  \033[38;5;245mAll operations available via natural language. Ask 'What can you do?' to get started.\033[0m"
        )
        print()

        conversation: list[dict] = []
        system_prompt = _build_system_prompt(language)

        while True:
            try:
                user_input = input(
                    "\033[38;2;86;186;159mNORMAL\033[0m \033[38;2;0;122;204m>\033[0m "
                ).strip()
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

            # Natural language command processor
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

            # Send to LLM
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

            # Context compression
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
            "- メディア: 「オフィスの画像を生成して」\n\n"
            "ユーザーはファイル操作やシェルコマンドも利用できます:\n"
            "- ファイル: /read, /write, /edit\n"
            "- シェル: /run, /ls, /cd, /pwd\n"
            "- 検索: /find, /grep\n"
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
            "- Media: 'Generate an office image'\n\n"
            "Users can also use file operations and shell commands:\n"
            "- Files: /read, /write, /edit\n"
            "- Shell: /run, /ls, /cd, /pwd\n"
            "- Search: /find, /grep\n"
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
            "- 审批: '显示待审批项'\n\n"
            "用户还可以使用文件操作和Shell命令:\n"
            "- 文件: /read, /write, /edit\n"
            "- Shell: /run, /ls, /cd, /pwd\n"
            "- 搜索: /find, /grep\n"
        ),
    }
    return lang_instructions.get(language, lang_instructions["en"])


# ---------------------------------------------------------------------------
# Task management helpers (Dispatch API client for CLI slash commands)
# ---------------------------------------------------------------------------

_API_BASE = "http://127.0.0.1:18234/api/v1"
_cli_auth_token: str | None = None


def _get_api_headers() -> dict[str, str]:
    """Get API request headers with cached anonymous session token.

    Lazily creates an anonymous session on first call. Subsequent calls
    reuse the cached token for the lifetime of the CLI process.
    """
    global _cli_auth_token
    if _cli_auth_token:
        return {"Authorization": f"Bearer {_cli_auth_token}"}

    import httpx

    try:
        resp = httpx.post(f"{_API_BASE}/auth/anonymous-session", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            _cli_auth_token = data.get("access_token", "")
            return {"Authorization": f"Bearer {_cli_auth_token}"}
    except httpx.ConnectError:
        pass
    return {}


# Color/icon constants for task status display
_STATUS_ICONS: dict[str, str] = {
    "queued": "\033[38;5;245m\u25cb\033[0m",  # grey circle
    "running": "\033[38;5;33m\u25cf\033[0m",  # blue circle
    "completed": "\033[38;5;78m\u2714\033[0m",  # green check
    "failed": "\033[38;5;196m\u2718\033[0m",  # red X
    "cancelled": "\033[38;5;245m\u2718\033[0m",  # grey X
    "needs_input": "\033[38;5;220m?\033[0m",  # yellow ?
    "preview": "\033[38;5;141m\u25b7\033[0m",  # purple triangle
}


def _cli_dispatch(instruction: str) -> str:
    """Fire a background task via the Dispatch API."""
    import httpx

    headers = _get_api_headers()
    if not headers:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"

    try:
        resp = httpx.post(
            f"{_API_BASE}/dispatch",
            json={"instruction": instruction},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            task_id = data.get("task_id", "?")
            status = data.get("status", "?")
            icon = _STATUS_ICONS.get(status, status)
            return (
                f"  {icon} Task dispatched: \033[38;5;75m{task_id[:8]}...\033[0m\n"
                f"  Status: {status}\n"
                f"  Use \033[38;5;245m/status {task_id[:8]}\033[0m to check progress"
            )
        return f"  \033[38;5;196mDispatch failed ({resp.status_code}): {resp.text}\033[0m"
    except httpx.ConnectError:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_tasks() -> str:
    """List active/completed/failed dispatch tasks."""
    import httpx

    headers = _get_api_headers()
    if not headers:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"

    try:
        resp = httpx.get(f"{_API_BASE}/dispatch", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            tasks = data.get("tasks", [])
            total = data.get("total", 0)
            if not tasks:
                return "  \033[38;5;245mNo tasks found.\033[0m"

            lines = [f"  \033[1mTasks ({total}):\033[0m", ""]
            for t in tasks:
                status = t.get("status", "?")
                icon = _STATUS_ICONS.get(status, status)
                task_id = t.get("task_id", "?")
                instruction = t.get("instruction", "")[:60]
                created = t.get("created_at", "")[:19]
                lines.append(
                    f"  {icon} \033[38;5;75m{task_id[:8]}\033[0m  "
                    f"{status:12s}  {instruction}  "
                    f"\033[38;5;245m{created}\033[0m"
                )
            return "\n".join(lines)
        return f"  \033[38;5;196mFailed to list tasks ({resp.status_code}): {resp.text}\033[0m"
    except httpx.ConnectError:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_task_status(task_id_prefix: str) -> str:
    """Show detailed status for a task (supports prefix matching)."""
    import httpx

    headers = _get_api_headers()
    if not headers:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"

    try:
        # First try exact match, then prefix match via task list
        resp = httpx.get(f"{_API_BASE}/dispatch/{task_id_prefix}", headers=headers, timeout=10)
        if resp.status_code == 404 and len(task_id_prefix) < 36:
            # Try prefix match: list all and find matching
            list_resp = httpx.get(f"{_API_BASE}/dispatch", headers=headers, timeout=10)
            if list_resp.status_code == 200:
                for t in list_resp.json().get("tasks", []):
                    if t["task_id"].startswith(task_id_prefix):
                        resp = httpx.get(
                            f"{_API_BASE}/dispatch/{t['task_id']}",
                            headers=headers,
                            timeout=10,
                        )
                        break
                else:
                    return f"  \033[38;5;196mNo task matching '{task_id_prefix}'\033[0m"

        if resp.status_code == 200:
            t = resp.json()
            status = t.get("status", "?")
            icon = _STATUS_ICONS.get(status, status)
            lines = [
                "  \033[1mTask Detail\033[0m",
                f"  ID:          \033[38;5;75m{t.get('task_id', '?')}\033[0m",
                f"  Status:      {icon} {status}",
                f"  Instruction: {t.get('instruction', '')}",
                f"  Created:     {t.get('created_at', '')[:19]}",
            ]
            if t.get("completed_at"):
                lines.append(f"  Completed:   {t['completed_at'][:19]}")
            if t.get("result"):
                result_text = t["result"][:200]
                lines.append(f"  Result:      {result_text}")
            if t.get("needs_input_reason"):
                lines.append(f"  \033[38;5;220mNeeds input: {t['needs_input_reason']}\033[0m")
            plan = t.get("plan_preview")
            if plan:
                lines.append("")
                lines.append(f"  \033[1mPlan Steps ({len(plan)}):\033[0m")
                for step in plan:
                    step_icon = _STATUS_ICONS.get(step.get("status", "pending"), " ")
                    title = step.get("title", "?")
                    deps = step.get("depends_on", [])
                    dep_str = f" (after: {', '.join(deps)})" if deps else ""
                    lines.append(f"    {step_icon} {title}{dep_str}")
            return "\n".join(lines)
        return f"  \033[38;5;196mTask not found ({resp.status_code})\033[0m"
    except httpx.ConnectError:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_approve(request_id: str) -> str:
    """Approve a pending approval request."""
    import httpx

    headers = _get_api_headers()
    if not headers:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"

    try:
        resp = httpx.post(
            f"{_API_BASE}/approvals/{request_id}/approve",
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return f"  \033[38;5;78m\u2714 Approved: {request_id}\033[0m"
        return (
            f"  \033[38;5;196mApproval failed ({resp.status_code}): "
            f"{resp.json().get('detail', resp.text)}\033[0m"
        )
    except httpx.ConnectError:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_reject(request_id: str, reason: str = "") -> str:
    """Reject a pending approval request."""
    import httpx

    headers = _get_api_headers()
    if not headers:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"

    try:
        params = {"reason": reason} if reason else {}
        resp = httpx.post(
            f"{_API_BASE}/approvals/{request_id}/reject",
            params=params,
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            msg = f"  \033[38;5;78m\u2714 Rejected: {request_id}\033[0m"
            if reason:
                msg += f"\n  Reason: {reason}"
            return msg
        return (
            f"  \033[38;5;196mRejection failed ({resp.status_code}): "
            f"{resp.json().get('detail', resp.text)}\033[0m"
        )
    except httpx.ConnectError:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_cancel(task_id_prefix: str) -> str:
    """Cancel a running dispatch task (supports prefix matching)."""
    import httpx

    headers = _get_api_headers()
    if not headers:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"

    try:
        # Resolve prefix to full task_id
        full_id = task_id_prefix
        if len(task_id_prefix) < 36:
            list_resp = httpx.get(f"{_API_BASE}/dispatch", headers=headers, timeout=10)
            if list_resp.status_code == 200:
                for t in list_resp.json().get("tasks", []):
                    if t["task_id"].startswith(task_id_prefix):
                        full_id = t["task_id"]
                        break
                else:
                    return f"  \033[38;5;196mNo task matching '{task_id_prefix}'\033[0m"

        resp = httpx.delete(f"{_API_BASE}/dispatch/{full_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            return f"  \033[38;5;78m\u2714 Cancelled: {full_id[:8]}...\033[0m"
        return f"  \033[38;5;196mCancel failed ({resp.status_code}): {resp.text}\033[0m"
    except httpx.ConnectError:
        return "  \033[38;5;196mCannot connect to API server. Is it running on port 18234?\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_read_file(path: str) -> str:
    """Read and display a file."""
    from pathlib import Path

    from app.security.sandbox import AccessType, FileSystemSandbox

    sandbox = FileSystemSandbox()
    target = Path(path).resolve()
    check = sandbox.check_access(str(target), AccessType.READ)
    if not check.allowed:
        return f"  \033[38;5;196mAccess denied: {check.reason}\033[0m"

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")
        # Show with line numbers
        numbered = []
        for i, line in enumerate(lines[:200], 1):
            numbered.append(f"  \033[38;5;245m{i:4d}\033[0m  {line}")
        result = "\n".join(numbered)
        if len(lines) > 200:
            result += f"\n  \033[38;5;245m... ({len(lines) - 200} more lines)\033[0m"
        return result
    except FileNotFoundError:
        return f"  \033[38;5;196mFile not found: {path}\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError reading file: {e}\033[0m"


def _cli_write_file(path: str, content: str) -> str:
    """Write content to a file with sandbox check."""
    from pathlib import Path

    from app.security.sandbox import AccessType, FileSystemSandbox

    sandbox = FileSystemSandbox()
    target = Path(path).resolve()
    check = sandbox.check_access(str(target), AccessType.WRITE)
    if not check.allowed:
        return f"  \033[38;5;196mAccess denied: {check.reason}\033[0m"

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"  \033[38;5;78m\u2714 Written to {target}\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError writing file: {e}\033[0m"


def _cli_run_command(command: str) -> str:
    """Execute a shell command with safety checks."""
    import subprocess

    # Block obviously dangerous commands
    dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){:|:&};:", "fork bomb"]
    cmd_lower = command.lower()
    for d in dangerous:
        if d in cmd_lower:
            return "  \033[38;5;196mBlocked: dangerous command pattern detected\033[0m"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd(),
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\033[38;5;220m{result.stderr}\033[0m"
        if result.returncode != 0:
            output += f"\n\033[38;5;196m(exit code: {result.returncode})\033[0m"
        return output or "  (no output)"
    except subprocess.TimeoutExpired:
        return "  \033[38;5;220mCommand timed out (30s limit)\033[0m"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_list_dir(path: str = ".") -> str:
    """List directory contents."""
    from pathlib import Path

    try:
        target = Path(path).resolve()
        if not target.is_dir():
            return f"  \033[38;5;196mNot a directory: {path}\033[0m"
        entries = sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        lines = []
        for entry in entries[:100]:
            if entry.is_dir():
                lines.append(f"  \033[38;5;33m{entry.name}/\033[0m")
            else:
                size = entry.stat().st_size
                if size < 1024:
                    sz = f"{size}B"
                elif size < 1048576:
                    sz = f"{size // 1024}K"
                else:
                    sz = f"{size // 1048576}M"
                lines.append(f"  {entry.name}  \033[38;5;245m{sz}\033[0m")
        total = len(list(target.iterdir()))
        if total > 100:
            lines.append(f"  \033[38;5;245m... ({total - 100} more)\033[0m")
        return "\n".join(lines) or "  (empty directory)"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_find_files(pattern: str) -> str:
    """Find files matching a glob pattern."""
    from pathlib import Path

    try:
        matches = sorted(Path(".").rglob(pattern))[:50]
        if not matches:
            return f"  No files matching '{pattern}'"
        lines = [f"  {m}" for m in matches]
        total = sum(1 for _ in Path(".").rglob(pattern))
        if total > 50:
            lines.append("  ... (showing first 50)")
        return "\n".join(lines)
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


def _cli_grep(pattern: str, path: str = ".") -> str:
    """Search file contents for a pattern."""
    import subprocess

    try:
        result = subprocess.run(
            ["grep", "-rn", "--color=never", "-I", pattern, path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.stdout:
            lines = result.stdout.strip().split("\n")[:30]
            output = "\n".join(f"  {line}" for line in lines)
            if len(result.stdout.strip().split("\n")) > 30:
                output += "\n  ... (showing first 30 matches)"
            return output
        return f"  No matches for '{pattern}'"
    except Exception as e:
        return f"  \033[38;5;196mError: {e}\033[0m"


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
                "  /lang <code> - 言語変更 (ja/en/zh/ko/pt/tr)\n"
                "  /clear     - 会話履歴をクリア\n"
                "  /quit      - 終了\n"
                "\n"
                "  \033[1mFile Operations:\033[0m\n"
                "  /read <path>   - ファイルを読み込む\n"
                "  /write <path>  - ファイルに書き込む\n"
                "  /edit <path>   - ファイルを表示\n"
                "  /run <cmd>     - シェルコマンドを実行\n"
                "  /ls [path]     - ディレクトリ一覧\n"
                "  /cd <path>     - ディレクトリ移動\n"
                "  /pwd           - 現在のディレクトリ\n"
                "  /find <pattern> - ファイル検索\n"
                "  /grep <pattern> - ファイル内容検索\n"
                "\n"
                "  \033[1mTask Management:\033[0m\n"
                "  /dispatch <instruction> - バックグラウンドタスクを実行\n"
                "  /tasks                  - タスク一覧を表示\n"
                "  /status <task_id>       - タスクの詳細を表示\n"
                "  /approve <request_id>   - 承認リクエストを承認\n"
                "  /reject <request_id> [reason] - 承認リクエストを却下\n"
                "  /cancel <task_id>       - 実行中のタスクをキャンセル"
            ),
            "en": (
                "  /help      - Show help\n"
                "  /models    - List available models\n"
                "  /lang <code> - Change language (ja/en/zh/ko/pt/tr)\n"
                "  /clear     - Clear conversation history\n"
                "  /quit      - Exit\n"
                "\n"
                "  \033[1mFile Operations:\033[0m\n"
                "  /read <path>   - Read a file\n"
                "  /write <path>  - Write to a file\n"
                "  /edit <path>   - View a file for editing\n"
                "  /run <cmd>     - Execute shell command\n"
                "  /ls [path]     - List directory\n"
                "  /cd <path>     - Change directory\n"
                "  /pwd           - Current directory\n"
                "  /find <pattern> - Find files\n"
                "  /grep <pattern> - Search file contents\n"
                "\n"
                "  \033[1mTask Management:\033[0m\n"
                "  /dispatch <instruction> - Fire a background task\n"
                "  /tasks                  - List tasks with status\n"
                "  /status <task_id>       - Show detailed task status\n"
                "  /approve <request_id>   - Approve a pending request\n"
                "  /reject <request_id> [reason] - Reject a pending request\n"
                "  /cancel <task_id>       - Cancel a running task"
            ),
            "zh": (
                "  /help      - 显示帮助\n"
                "  /models    - 列出可用模型\n"
                "  /lang <code> - 更改语言 (ja/en/zh/ko/pt/tr)\n"
                "  /clear     - 清除对话历史\n"
                "  /quit      - 退出\n"
                "\n"
                "  \033[1mFile Operations:\033[0m\n"
                "  /read <path>   - 读取文件\n"
                "  /write <path>  - 写入文件\n"
                "  /edit <path>   - 查看文件\n"
                "  /run <cmd>     - 执行命令\n"
                "  /ls [path]     - 列出目录\n"
                "  /cd <path>     - 切换目录\n"
                "  /pwd           - 当前目录\n"
                "  /find <pattern> - 搜索文件\n"
                "  /grep <pattern> - 搜索文件内容\n"
                "\n"
                "  \033[1mTask Management:\033[0m\n"
                "  /dispatch <instruction> - 启动后台任务\n"
                "  /tasks                  - 列出任务及状态\n"
                "  /status <task_id>       - 显示任务详情\n"
                "  /approve <request_id>   - 批准待审请求\n"
                "  /reject <request_id> [reason] - 拒绝待审请求\n"
                "  /cancel <task_id>       - 取消运行中的任务"
            ),
        }
        print(help_text.get(language, help_text["en"]))
        return None

    if command == "/lang" and len(parts) > 1:
        new_lang = parts[1].lower()
        supported = {"ja", "en", "zh", "ko", "pt", "tr"}
        if new_lang in supported:
            set_language(new_lang)
            names = {
                "ja": "日本語",
                "en": "English",
                "zh": "中文",
                "ko": "한국어",
                "pt": "Português",
                "tr": "Türkçe",
            }
            print(f"  Language: {names[new_lang]}")
        else:
            print("  Supported: ja, en, zh, ko, pt, tr")
        return None

    if command == "/clear":
        print("  (conversation cleared)")
        return None

    if command == "/models":
        cmd_models(argparse.Namespace())
        return None

    if command == "/read" and len(parts) > 1:
        print(_cli_read_file(" ".join(parts[1:])))
        return None

    if command == "/write" and len(parts) > 1:
        filepath = " ".join(parts[1:])
        print("  Enter content (type '---' on a line by itself to finish):")
        content_lines: list[str] = []
        while True:
            try:
                line = input("  ")
                if line.strip() == "---":
                    break
                content_lines.append(line)
            except (KeyboardInterrupt, EOFError):
                print("\n  (write cancelled)")
                return None
        print(_cli_write_file(filepath, "\n".join(content_lines)))
        return None

    if command == "/edit" and len(parts) > 1:
        filepath = " ".join(parts[1:])
        print(_cli_read_file(filepath))
        print(f"\n  To modify, use /write {filepath}")
        return None

    if command == "/run":
        if len(parts) > 1:
            print(_cli_run_command(" ".join(parts[1:])))
        else:
            print("  Usage: /run <command>")
        return None

    if command == "/ls":
        path = parts[1] if len(parts) > 1 else "."
        print(_cli_list_dir(path))
        return None

    if command == "/cd" and len(parts) > 1:
        target = parts[1]
        try:
            os.chdir(target)
            print(f"  \033[38;5;78m\u2192 {os.getcwd()}\033[0m")
        except Exception as e:
            print(f"  \033[38;5;196mError: {e}\033[0m")
        return None

    if command == "/pwd":
        print(f"  {os.getcwd()}")
        return None

    if command == "/find" and len(parts) > 1:
        print(_cli_find_files(" ".join(parts[1:])))
        return None

    if command == "/grep":
        if len(parts) > 1:
            pat = parts[1]
            search_path = parts[2] if len(parts) > 2 else "."
            print(_cli_grep(pat, search_path))
        else:
            print("  Usage: /grep <pattern> [path]")
        return None

    # ── Task Management Commands ──
    if command == "/dispatch":
        if len(parts) > 1:
            instruction = " ".join(parts[1:])
            print(_cli_dispatch(instruction))
        else:
            print("  Usage: /dispatch <instruction>")
        return None

    if command == "/tasks":
        print(_cli_tasks())
        return None

    if command == "/status":
        if len(parts) > 1:
            print(_cli_task_status(parts[1]))
        else:
            print("  Usage: /status <task_id>")
        return None

    if command == "/approve":
        if len(parts) > 1:
            print(_cli_approve(parts[1]))
        else:
            print("  Usage: /approve <request_id>")
        return None

    if command == "/reject":
        if len(parts) > 1:
            reason = " ".join(parts[2:]) if len(parts) > 2 else ""
            print(_cli_reject(parts[1], reason))
        else:
            print("  Usage: /reject <request_id> [reason]")
        return None

    if command == "/cancel":
        if len(parts) > 1:
            print(_cli_cancel(parts[1]))
        else:
            print("  Usage: /cancel <task_id>")
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
    """Update to the latest version."""
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

    # Update via pip install -U
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
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        prog="zero-employee",
        description="Zero-Employee Orchestrator -- AI orchestration platform",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=18234, help="Port (default: 18234)")
    serve_parser.add_argument("--reload", action="store_true", help="Enable hot reload")
    serve_parser.add_argument(
        "--skip-update-check",
        action="store_true",
        help="Skip version check at startup",
    )
    serve_parser.add_argument(
        "--no-auto-pull",
        action="store_true",
        dest="no_auto_pull",
        help="Disable automatic Ollama model pull on startup",
    )
    serve_parser.add_argument(
        "--auto-pull-model",
        default="qwen3:8b",
        dest="auto_pull_model",
        metavar="MODEL",
        help="Ollama model to auto-pull when none are installed (default: qwen3:8b)",
    )
    serve_parser.set_defaults(func=cmd_serve)

    # db
    db_parser = subparsers.add_parser("db", help="Database operations")
    db_sub = db_parser.add_subparsers(dest="db_command")
    upgrade_parser = db_sub.add_parser("upgrade", help="Run migration")
    upgrade_parser.set_defaults(func=cmd_db_upgrade)

    # health
    health_parser = subparsers.add_parser("health", help="Health check")
    health_parser.add_argument("--host", default="127.0.0.1", help="Host")
    health_parser.add_argument("--port", type=int, default=18234, help="Port")
    health_parser.set_defaults(func=cmd_health)

    # config -- configuration management
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration management (API keys, execution mode, etc.)",
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

    # local -- local chat mode
    local_parser = subparsers.add_parser(
        "local",
        help="Local chat mode (Ollama / offline)",
    )
    local_parser.add_argument(
        "--model",
        default="",
        help="Ollama model name (auto-detect if empty)",
    )
    local_parser.add_argument(
        "--lang",
        default="",
        choices=["ja", "en", "zh", "ko", "pt", "tr", ""],
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

    # chat -- multi-provider chat mode
    chat_parser = subparsers.add_parser(
        "chat",
        help="Chat mode (all providers, all operations via natural language)",
    )
    chat_parser.add_argument(
        "--mode",
        default="",
        choices=["quality", "speed", "cost", "free", "subscription", ""],
        help="Execution mode (default: auto)",
    )
    chat_parser.add_argument(
        "--lang",
        default="",
        choices=["ja", "en", "zh", "ko", "pt", "tr", ""],
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

    # models -- model listing
    models_parser = subparsers.add_parser("models", help="List available models")
    models_parser.set_defaults(func=cmd_models)

    # pull -- model download
    pull_parser = subparsers.add_parser("pull", help="Download an Ollama model")
    pull_parser.add_argument("model_name", help="Model name (e.g. qwen3:8b)")
    pull_parser.set_defaults(func=cmd_pull)

    # update -- update management
    update_parser = subparsers.add_parser(
        "update",
        help="Update to the latest version",
    )
    update_parser.add_argument(
        "--check",
        dest="check_only",
        action="store_true",
        help="Check for updates only (do not install)",
    )
    update_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show pip output",
    )
    update_parser.set_defaults(func=cmd_update)

    # mcp -- Model Context Protocol server inspection & testing
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Model Context Protocol server: inspect, list tools, run tools",
    )
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command")

    mcp_info = mcp_sub.add_parser("info", help="Show MCP server capabilities")
    mcp_info.set_defaults(func=cmd_mcp)

    mcp_tools = mcp_sub.add_parser("tools", help="List all MCP tools")
    mcp_tools.set_defaults(func=cmd_mcp)

    mcp_call = mcp_sub.add_parser("call", help="Invoke an MCP tool locally")
    mcp_call.add_argument("tool_name", help="Tool name (e.g. get_server_info)")
    mcp_call.add_argument(
        "--args",
        dest="tool_args",
        default="{}",
        help="JSON-encoded arguments (default: {})",
    )
    mcp_call.set_defaults(func=cmd_mcp)

    mcp_parser.set_defaults(func=cmd_mcp)

    # security -- security management
    security_parser = subparsers.add_parser("security", help="Security configuration management")
    security_sub = security_parser.add_subparsers(dest="security_command")
    sec_status_parser = security_sub.add_parser(
        "status", help="Display security configuration summary"
    )
    sec_status_parser.set_defaults(func=cmd_security_status)

    return parser


def main() -> None:
    """CLI main entry point."""
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
