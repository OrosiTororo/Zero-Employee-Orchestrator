"""Zero-Employee Orchestrator CLI エントリーポイント.

コマンドラインから API サーバーの起動・管理を行う。

使い方:
    zero-employee serve          # API サーバーを起動
    zero-employee serve --port 8000
    zero-employee db upgrade     # DB マイグレーション実行
    zero-employee health         # ヘルスチェック
"""

import argparse
import sys


def cmd_serve(args: argparse.Namespace) -> None:
    """API サーバーを起動する."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def cmd_db_upgrade(args: argparse.Namespace) -> None:
    """DB マイグレーションを実行する."""
    import asyncio

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
            print(f"✅ サーバーは正常です: {resp.json()}")
        else:
            print(f"⚠️ ステータス: {resp.status_code}")
            sys.exit(1)
    except httpx.ConnectError:
        print(f"❌ サーバーに接続できません: {url}")
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

    return parser


def main() -> None:
    """CLI メインエントリーポイント."""
    from app.banner import print_banner

    print_banner()

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
