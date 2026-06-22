import httpx

from context_saver.config import Settings
from context_saver.deepseek_client import DeepSeekClient


def _settings() -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_flash_model="deepseek-v4-flash",
        deepseek_pro_model="deepseek-v4-pro",
        deepseek_retry_backoff_seconds=0,
    )


def _success_response(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "compressed context"}}],
            "usage": {"total_tokens": 42},
        },
        request=request,
    )


def test_deepseek_retries_transport_error_then_succeeds(monkeypatch):
    attempts = {"count": 0}
    original_client = httpx.Client

    class FakeClient:
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(self.handler)
            self.client = original_client(*args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.client.close()

        def handler(self, request: httpx.Request) -> httpx.Response:
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise httpx.ConnectError("temporary network drop", request=request)
            return _success_response(request)

        def post(self, *args, **kwargs):
            return self.client.post(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = DeepSeekClient(settings=_settings(), max_retries=1).chat([{"role": "user", "content": "hello"}])

    assert result.content == "compressed context"
    assert result.usage == {"total_tokens": 42}
    assert attempts["count"] == 2


def test_deepseek_retries_retryable_http_status(monkeypatch):
    attempts = {"count": 0}
    original_client = httpx.Client

    class FakeClient:
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(self.handler)
            self.client = original_client(*args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.client.close()

        def handler(self, request: httpx.Request) -> httpx.Response:
            attempts["count"] += 1
            if attempts["count"] == 1:
                return httpx.Response(429, headers={"retry-after": "0"}, request=request)
            return _success_response(request)

        def post(self, *args, **kwargs):
            return self.client.post(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = DeepSeekClient(settings=_settings(), max_retries=1).chat([{"role": "user", "content": "hello"}])

    assert result.content == "compressed context"
    assert attempts["count"] == 2


def test_deepseek_auth_error_is_not_retried(monkeypatch):
    attempts = {"count": 0}
    original_client = httpx.Client

    class FakeClient:
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(self.handler)
            self.client = original_client(*args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.client.close()

        def handler(self, request: httpx.Request) -> httpx.Response:
            attempts["count"] += 1
            return httpx.Response(401, request=request)

        def post(self, *args, **kwargs):
            return self.client.post(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    try:
        DeepSeekClient(settings=_settings(), max_retries=3).chat([{"role": "user", "content": "hello"}])
    except RuntimeError as exc:
        assert "authentication failed" in str(exc)
    else:
        raise AssertionError("Expected authentication failure")

    assert attempts["count"] == 1


def test_deepseek_empty_content_reports_reasoning_budget(monkeypatch):
    original_client = httpx.Client

    class FakeClient:
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(self.handler)
            self.client = original_client(*args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.client.close()

        def handler(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": ""}}],
                    "usage": {
                        "completion_tokens_details": {"reasoning_tokens": 8},
                    },
                },
                request=request,
            )

        def post(self, *args, **kwargs):
            return self.client.post(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", FakeClient)

    try:
        DeepSeekClient(settings=_settings()).chat([{"role": "user", "content": "hello"}])
    except RuntimeError as exc:
        assert "output budget was consumed by reasoning" in str(exc)
    else:
        raise AssertionError("Expected empty-content failure")
