"""Cloud Sandbox — Cloudflare Workers上でのサンドボックス実行環境.

Workers上でも動けてローカルのコードを直接編集できる
サンドボックス環境を提供する。

機能:
  - Cloudflare Workersへのデプロイ（wrangler経由）
  - ローカルファイルシステムへのアクセス（制限付き）
  - サンドボックス内でのコード実行
  - 実行結果のアーティファクト保存
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SandboxMode(str, Enum):
    LOCAL = "local"           # ローカルプロセスで実行
    DOCKER = "docker"         # Dockerコンテナで実行
    WORKERS = "workers"       # Cloudflare Workersで実行
    WASM = "wasm"             # WebAssembly サンドボックス


@dataclass
class SandboxConfig:
    """サンドボックス設定."""
    mode: SandboxMode = SandboxMode.LOCAL
    max_memory_mb: int = 256
    max_cpu_seconds: int = 30
    allowed_network: bool = False
    allowed_paths: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)
    cloudflare_account_id: str = ""
    wrangler_config_path: str = ""


@dataclass
class SandboxResult:
    """サンドボックス実行結果."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    error: str | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "local"
    duration_ms: int = 0


class CloudSandbox:
    """マルチモードサンドボックス実行環境.

    ローカル実行、Docker実行、Cloudflare Workers実行をサポート。
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self.config = config or SandboxConfig()

    async def execute(
        self,
        code: str,
        *,
        language: str = "python",
        inputs: dict[str, Any] | None = None,
        mode: SandboxMode | None = None,
    ) -> SandboxResult:
        """コードを実行."""
        sandbox_mode = mode or self.config.mode

        if sandbox_mode == SandboxMode.LOCAL:
            return await self._execute_local(code, language, inputs)
        elif sandbox_mode == SandboxMode.DOCKER:
            return await self._execute_docker(code, language, inputs)
        elif sandbox_mode == SandboxMode.WORKERS:
            return await self._execute_workers(code, language, inputs)
        else:
            return SandboxResult(success=False, error=f"Unsupported mode: {sandbox_mode}")

    async def _execute_local(
        self, code: str, language: str, inputs: dict[str, Any] | None
    ) -> SandboxResult:
        """ローカルプロセスで実行."""
        import time
        start = time.time()

        if language == "python":
            return await self._run_python(code, inputs, start)
        elif language in ("javascript", "typescript"):
            return await self._run_node(code, inputs, start)
        elif language == "shell":
            return await self._run_shell(code, start)
        else:
            return SandboxResult(
                success=False, error=f"Unsupported language: {language}", mode="local"
            )

    async def _run_python(
        self, code: str, inputs: dict[str, Any] | None, start: float
    ) -> SandboxResult:
        """Python コードの実行."""
        import time

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, dir=tempfile.gettempdir()
            ) as f:
                if inputs:
                    f.write(f"__inputs__ = {repr(inputs)}\n")
                f.write(code)
                script_path = f.name

            proc = await asyncio.create_subprocess_exec(
                "python3", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.config.max_cpu_seconds,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return SandboxResult(
                    success=False,
                    error=f"Timeout after {self.config.max_cpu_seconds}s",
                    mode="local",
                    duration_ms=int((time.time() - start) * 1000),
                )

            Path(script_path).unlink(missing_ok=True)

            return SandboxResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                mode="local",
                duration_ms=int((time.time() - start) * 1000),
            )

        except Exception as e:
            import time as t
            return SandboxResult(
                success=False, error=str(e), mode="local",
                duration_ms=int((t.time() - start) * 1000),
            )

    async def _run_node(
        self, code: str, inputs: dict[str, Any] | None, start: float
    ) -> SandboxResult:
        """Node.js コードの実行."""
        import time

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mjs", delete=False, dir=tempfile.gettempdir()
            ) as f:
                if inputs:
                    f.write(f"const __inputs__ = {json.dumps(inputs)};\n")
                f.write(code)
                script_path = f.name

            proc = await asyncio.create_subprocess_exec(
                "node", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.config.max_cpu_seconds,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return SandboxResult(
                    success=False,
                    error=f"Timeout after {self.config.max_cpu_seconds}s",
                    mode="local",
                    duration_ms=int((time.time() - start) * 1000),
                )

            Path(script_path).unlink(missing_ok=True)

            return SandboxResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                mode="local",
                duration_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), mode="local",
                duration_ms=int((time.time() - start) * 1000),
            )

    async def _run_shell(self, code: str, start: float) -> SandboxResult:
        """シェルコマンドの実行（制限付き）."""
        import time

        # 安全性チェック
        dangerous = ["rm -rf", "mkfs", "dd if=", ":(){ :|:", "chmod 777 /"]
        for d in dangerous:
            if d in code:
                return SandboxResult(
                    success=False,
                    error=f"Dangerous command blocked: {d}",
                    mode="local",
                )

        try:
            proc = await asyncio.create_subprocess_shell(
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.max_cpu_seconds,
            )
            return SandboxResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                mode="local",
                duration_ms=int((time.time() - start) * 1000),
            )
        except asyncio.TimeoutError:
            return SandboxResult(
                success=False, error="Timeout", mode="local",
                duration_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), mode="local",
                duration_ms=int((time.time() - start) * 1000),
            )

    async def _execute_docker(
        self, code: str, language: str, inputs: dict[str, Any] | None
    ) -> SandboxResult:
        """Dockerコンテナで実行（rootless対応）."""
        import time
        start = time.time()

        image = "python:3.12-slim" if language == "python" else "node:20-slim"
        ext = ".py" if language == "python" else ".mjs"

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext, delete=False
            ) as f:
                f.write(code)
                script_path = f.name

            cmd = [
                "docker", "run", "--rm",
                "--user", "1000:1000",
                "--memory", f"{self.config.max_memory_mb}m",
                "--network", "none" if not self.config.allowed_network else "bridge",
                "--read-only",
                "--tmpfs", "/tmp:size=64m",
                "-v", f"{script_path}:/sandbox/script{ext}:ro",
                image,
                "python3" if language == "python" else "node",
                f"/sandbox/script{ext}",
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.max_cpu_seconds + 10,
            )

            Path(script_path).unlink(missing_ok=True)

            return SandboxResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                mode="docker",
                duration_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), mode="docker",
                duration_ms=int((time.time() - start) * 1000),
            )

    async def _execute_workers(
        self, code: str, language: str, inputs: dict[str, Any] | None
    ) -> SandboxResult:
        """Cloudflare Workersで実行."""
        import time
        start = time.time()

        if language not in ("javascript", "typescript"):
            return SandboxResult(
                success=False,
                error="Workers mode only supports JavaScript/TypeScript",
                mode="workers",
            )

        try:
            # wrangler を使ってワーカースクリプトをデプロイ・実行
            worker_code = f"""
export default {{
  async fetch(request) {{
    try {{
      const inputs = {json.dumps(inputs or {})};
      {code}
      return new Response(JSON.stringify({{ success: true, result: "executed" }}));
    }} catch (e) {{
      return new Response(JSON.stringify({{ success: false, error: e.message }}), {{ status: 500 }});
    }}
  }}
}};
"""
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".js", delete=False
            ) as f:
                f.write(worker_code)
                script_path = f.name

            # wrangler dev でローカル実行テスト
            proc = await asyncio.create_subprocess_exec(
                "npx", "wrangler", "dev", script_path,
                "--port", "0",  # ランダムポート
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.config.max_cpu_seconds,
                )
            except asyncio.TimeoutError:
                proc.kill()

            Path(script_path).unlink(missing_ok=True)

            return SandboxResult(
                success=True,
                stdout=stdout.decode("utf-8", errors="replace") if stdout else "",
                stderr=stderr.decode("utf-8", errors="replace") if stderr else "",
                mode="workers",
                duration_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), mode="workers",
                duration_ms=int((time.time() - start) * 1000),
            )

    async def edit_local_file(
        self,
        file_path: str,
        content: str,
        *,
        create_if_missing: bool = False,
    ) -> SandboxResult:
        """ローカルファイルを編集（権限チェック付き）."""
        path = Path(file_path)

        # 許可されたパスかチェック
        if self.config.allowed_paths:
            allowed = any(
                str(path).startswith(p) for p in self.config.allowed_paths
            )
            if not allowed:
                return SandboxResult(
                    success=False,
                    error=f"Path not allowed: {file_path}",
                    mode="local",
                )

        try:
            if not path.exists() and not create_if_missing:
                return SandboxResult(
                    success=False,
                    error=f"File not found: {file_path}",
                    mode="local",
                )

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

            return SandboxResult(
                success=True,
                stdout=f"File written: {file_path} ({len(content)} bytes)",
                mode="local",
            )
        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), mode="local",
            )

    async def read_local_file(self, file_path: str) -> SandboxResult:
        """ローカルファイルを読み取り（権限チェック付き）."""
        path = Path(file_path)

        if self.config.allowed_paths:
            allowed = any(
                str(path).startswith(p) for p in self.config.allowed_paths
            )
            if not allowed:
                return SandboxResult(
                    success=False,
                    error=f"Path not allowed: {file_path}",
                    mode="local",
                )

        try:
            if not path.exists():
                return SandboxResult(
                    success=False,
                    error=f"File not found: {file_path}",
                    mode="local",
                )
            content = path.read_text(encoding="utf-8")
            return SandboxResult(
                success=True,
                stdout=content,
                mode="local",
            )
        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), mode="local",
            )

    async def deploy_to_workers(
        self,
        name: str,
        code: str,
        *,
        env_vars: dict[str, str] | None = None,
    ) -> SandboxResult:
        """Cloudflare Workersにデプロイ.

        Cloudflareのアカウントさえあれば、ローカルからクラウドデプロイまで簡単に。
        """
        import time
        start = time.time()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # wrangler.toml を生成
                wrangler_config = f"""
name = "{name}"
main = "index.js"
compatibility_date = "2024-12-01"
"""
                Path(tmpdir, "wrangler.toml").write_text(wrangler_config)
                Path(tmpdir, "index.js").write_text(code)

                if env_vars:
                    for key, value in env_vars.items():
                        proc = await asyncio.create_subprocess_exec(
                            "npx", "wrangler", "secret", "put", key,
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=tmpdir,
                        )
                        await proc.communicate(input=value.encode())

                proc = await asyncio.create_subprocess_exec(
                    "npx", "wrangler", "deploy",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=120,
                )

                return SandboxResult(
                    success=proc.returncode == 0,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    exit_code=proc.returncode or 0,
                    mode="workers",
                    duration_ms=int((time.time() - start) * 1000),
                )
        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), mode="workers",
                duration_ms=int((time.time() - start) * 1000),
            )
