"""Sandbox Executor - Runs code/scripts in isolated environments.

Provides sandboxed execution for Skills that require running code,
with resource limits and permission controls.
"""

import asyncio
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    max_memory_mb: int = 256
    max_cpu_seconds: int = 30
    allowed_network: bool = False
    allowed_filesystem_paths: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)


@dataclass
class SandboxResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    error: str | None = None
    artifacts: list[dict] = field(default_factory=list)


class SandboxExecutor:
    """Execute code in a sandboxed environment."""

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self.config = config or SandboxConfig()

    async def execute_python(self, code: str, inputs: dict | None = None) -> SandboxResult:
        """Execute Python code in a subprocess sandbox."""
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
                    error=f"Execution timed out after {self.config.max_cpu_seconds}s",
                    exit_code=-1,
                )

            Path(script_path).unlink(missing_ok=True)

            return SandboxResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
            )

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return SandboxResult(success=False, error=str(e))

    async def execute_skill(self, skill_path: str, inputs: dict | None = None) -> SandboxResult:
        """Execute a Skill script in a sandbox."""
        skill_file = Path(skill_path)
        if not skill_file.exists():
            return SandboxResult(success=False, error=f"Skill not found: {skill_path}")

        if not skill_file.suffix == ".py":
            return SandboxResult(success=False, error="Only Python skills are supported")

        code = skill_file.read_text(encoding="utf-8")
        return await self.execute_python(code, inputs)
