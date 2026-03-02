"""LiteLLM Router Gateway.
providers.json を読み込み litellm.Router を構築。
全呼び出しは router.acompletion() 経由。openrouter/ プレフィックス必須。
"""

import json
from typing import Optional

import litellm

from app.main import resource_path
from app.auth import token_store

_router: Optional[litellm.Router] = None


async def init_gateway() -> bool:
    """Router を初期化。成功時 True、キー未設定時 False。"""
    global _router
    token = await token_store.load_token("openrouter")
    if not token or "key" not in token:
        _router = None
        return False

    api_key = token["key"]
    providers_path = resource_path("gateway/providers.json")
    with open(providers_path, encoding="utf-8") as f:
        config = json.load(f)

    model_list = []
    for m in config["models"]:
        params = dict(m["litellm_params"])
        params["api_key"] = api_key
        model_list.append({
            "model_name": m["model_name"],
            "litellm_params": params,
        })

    rs = config.get("router_settings", {})
    _router = litellm.Router(
        model_list=model_list,
        routing_strategy=rs.get("routing_strategy", "simple-shuffle"),
        num_retries=rs.get("num_retries", 3),
        allowed_fails=rs.get("allowed_fails", 3),
        cooldown_time=rs.get("cooldown_time", 30),
        enable_pre_call_checks=True,
    )
    return True


async def call_llm(
    messages: list[dict],
    model_group: str = "fast",
    **kwargs,
) -> dict:
    """LLM を呼び出す。Router 未初期化時は例外。"""
    if _router is None:
        raise RuntimeError("Gateway not initialized. OpenRouter authentication required.")
    response = await _router.acompletion(
        model=model_group,
        messages=messages,
        **kwargs,
    )
    return response


def is_ready() -> bool:
    """Router が初期化済みか。"""
    return _router is not None
