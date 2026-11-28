import asyncio
import httpx

from app.middleware.request_size import RequestBodyLimitMiddleware
from app.main import app


def _run(chunks, headers=(), limit=5):
    consumed = 0
    sent = []
    messages = iter([{"type": "http.request", "body": part, "more_body": i < len(chunks) - 1}
                     for i, part in enumerate(chunks)])

    async def app(scope, receive, send):
        nonlocal consumed
        while True:
            message = await receive()
            consumed += len(message.get("body", b""))
            if not message.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "method": "POST", "path": "/", "headers": list(headers)}
    asyncio.run(RequestBodyLimitMiddleware(app, limit)(scope, receive, send))
    return sent, consumed


def test_request_body_limit_allows_normal_and_exact_limit():
    for chunks in ([b"ok"], [b"12", b"345"]):
        sent, consumed = _run(chunks)
        assert sent[0]["status"] == 200
        assert consumed == sum(map(len, chunks))


def test_request_body_limit_rejects_declared_oversize_before_reading():
    sent, consumed = _run([b"123456"], [(b"content-length", b"6")])
    assert sent[0]["status"] == 413
    assert consumed == 0


def test_request_body_limit_rejects_streamed_body_without_content_length():
    sent, consumed = _run([b"123", b"456", b"ignored"])
    assert sent[0]["status"] == 413
    assert consumed == 3  # first in-limit chunk is delivered; crossing chunk is stopped
    assert dict(sent[0]["headers"])[b"cache-control"] == b"no-store"


def test_actual_asgi_app_returns_413_with_security_headers(client, admin_headers):
    response = client.post("/api/v1/auth/login", content=b"x" * 1_048_577,
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_asgi_server_stack_rejects_chunked_body_without_content_length():
    async def send_chunked():
        async def chunks():
            yield b'{"email":"'
            yield b'x' * 1_048_600

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post("/api/v1/auth/login", content=chunks(),
                                     headers={"Content-Type": "application/json"})

    response = asyncio.run(send_chunked())
    assert response.status_code == 413
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
