import httpx

from context_saver.anysearch_client import AnySearchClient
from context_saver.config import Settings


def test_anysearch_search_posts_jsonrpc_payload(monkeypatch):
    captured = {}
    original_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["payload"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"content": [{"type": "text", "text": "## Search Results"}]},
            },
        )

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.client = original_client(transport=httpx.MockTransport(handler))

        def __enter__(self):
            return self.client

        def __exit__(self, *args):
            self.client.close()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    settings = Settings(anysearch_api_key="ak-test")

    result = AnySearchClient(settings=settings).search(
        "AAPL",
        domain="finance",
        sub_domain="finance.us_stock",
        sub_domain_params={"ticker": "AAPL"},
    )

    assert result.text == "## Search Results"
    assert captured["headers"]["authorization"] == "Bearer ak-test"
    assert '"name":"search"' in captured["payload"].replace(" ", "")
    assert '"ticker":"AAPL"' in captured["payload"].replace(" ", "")
