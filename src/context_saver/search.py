from __future__ import annotations

from typing import Any

from .anysearch_client import AnySearchClient
from .config import Settings, load_settings


def local_search_stub(query: str) -> list[str]:
    return [f"Search query recorded: {query}", "External search was not used; enable AnySearch or call an MCP search tool when live results are needed."]


def web_search(
    query: str,
    max_results: int = 5,
    domain: str = "",
    sub_domain: str = "",
    sub_domain_params: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> tuple[list[str], str]:
    settings = settings or load_settings()
    if not settings.anysearch_enabled and not settings.anysearch_api_key:
        return local_search_stub(query), "AnySearch is not enabled; set ANYSEARCH_ENABLED=true or ANYSEARCH_API_KEY."
    try:
        result = AnySearchClient(settings=settings).search(
            query=query,
            max_results=max_results,
            domain=domain,
            sub_domain=sub_domain,
            sub_domain_params=sub_domain_params,
        )
        return [result.text], ""
    except RuntimeError as exc:
        return local_search_stub(query), str(exc)
