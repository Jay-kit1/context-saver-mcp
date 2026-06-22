from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings, load_settings


@dataclass(frozen=True)
class AnySearchResult:
    text: str
    raw: dict[str, Any]


class AnySearchClient:
    def __init__(self, settings: Settings | None = None, timeout: float = 30.0):
        self.settings = settings or load_settings()
        self.timeout = timeout

    def _headers(self, api_key: str = "") -> dict[str, str]:
        key = api_key or self.settings.anysearch_api_key
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def call_tool(self, tool_name: str, arguments: dict[str, Any], api_key: str = "") -> AnySearchResult:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.settings.anysearch_base_url,
                    json=payload,
                    headers=self._headers(api_key),
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"AnySearch API HTTP error: {exc.response.status_code}") from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError("AnySearch API request timed out.") from exc
        except httpx.NetworkError as exc:
            raise RuntimeError("AnySearch API network error.") from exc

        data = response.json()
        if "error" in data:
            error = data["error"]
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            raise RuntimeError(f"AnySearch API error: {message}")
        result = data.get("result", {})
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                return AnySearchResult(text=item.get("text", ""), raw=data)
        return AnySearchResult(text="", raw=data)

    def search(
        self,
        query: str,
        max_results: int = 5,
        domain: str = "",
        sub_domain: str = "",
        sub_domain_params: dict[str, Any] | None = None,
        api_key: str = "",
    ) -> AnySearchResult:
        arguments: dict[str, Any] = {"query": query, "max_results": min(max(1, max_results), 10)}
        if domain:
            arguments["domain"] = domain
        if sub_domain:
            arguments["sub_domain"] = sub_domain
        if sub_domain_params:
            arguments["sub_domain_params"] = sub_domain_params
        return self.call_tool("search", arguments, api_key=api_key)

    def extract(self, url: str, api_key: str = "") -> AnySearchResult:
        return self.call_tool("extract", {"url": url}, api_key=api_key)

    def get_sub_domains(self, domain: str = "", domains: list[str] | None = None, api_key: str = "") -> AnySearchResult:
        arguments: dict[str, Any] = {}
        if domains:
            arguments["domains"] = domains
        elif domain:
            arguments["domain"] = domain
        else:
            raise ValueError("domain or domains is required")
        return self.call_tool("get_sub_domains", arguments, api_key=api_key)
