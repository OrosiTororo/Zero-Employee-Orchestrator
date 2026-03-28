"""Service dependency injection — provides lazily-initialized singletons via FastAPI ``Depends()``.

This module replaces direct imports of global instances (e.g.,
``from app.security.sandbox import filesystem_sandbox``) with injectable
dependencies that can be easily overridden in tests.

Usage in route handlers::

    from app.api.deps.services import get_sandbox, get_gateway

    @router.get("/example")
    async def example(
        sandbox: FileSystemSandbox = Depends(get_sandbox),
        gateway: LLMGateway = Depends(get_gateway),
    ):
        ...

Override in tests::

    app.dependency_overrides[get_sandbox] = lambda: mock_sandbox
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def get_sandbox():
    """Return the global FileSystemSandbox instance."""
    from app.security.sandbox import filesystem_sandbox

    return filesystem_sandbox


@lru_cache(maxsize=1)
def get_data_protection():
    """Return the global DataProtectionGuard instance."""
    from app.security.data_protection import data_protection_guard

    return data_protection_guard


@lru_cache(maxsize=1)
def get_workspace_isolation():
    """Return the global WorkspaceIsolation instance."""
    from app.security.workspace_isolation import workspace_isolation

    return workspace_isolation


@lru_cache(maxsize=1)
def get_secret_store():
    """Return the global SecretStore instance."""
    from app.security.secret_manager import secret_store

    return secret_store


@lru_cache(maxsize=1)
def get_gateway():
    """Return the global LLMGateway instance."""
    from app.providers.gateway import llm_gateway

    return llm_gateway


@lru_cache(maxsize=1)
def get_a2a_hub():
    """Return the global A2A communication hub."""
    from app.orchestration.a2a_communication import a2a_hub

    return a2a_hub


@lru_cache(maxsize=1)
def get_model_registry():
    """Return the global ModelRegistry instance (thread-safe)."""
    from app.providers.model_registry import get_model_registry as _get

    return _get()
