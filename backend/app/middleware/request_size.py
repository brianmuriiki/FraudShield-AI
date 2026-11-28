"""Streaming ASGI request-body limit; never buffers a full request body."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable


class _BodyTooLarge(BaseException):
    pass


def _contains_body_limit(error: BaseException) -> bool:
    if isinstance(error, _BodyTooLarge):
        return True
    if isinstance(error, BaseExceptionGroup):
        return any(_contains_body_limit(child) for child in error.exceptions)
    return False


class RequestBodyLimitMiddleware:
    def __init__(self, app: Callable[..., Awaitable[None]], max_bytes: int,
                 allowed_origins: list[str] | None = None, production: bool = False,
                 hsts_seconds: int = 31_536_000) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.allowed_origins = set(allowed_origins or [])
        self.production = production
        self.hsts_seconds = hsts_seconds

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[dict]], send: Callable[..., Awaitable[None]]) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        length = next((v.decode("latin-1") for k, v in scope.get("headers", []) if k.lower() == b"content-length"), None)
        if length and length.isdigit() and int(length) > self.max_bytes:
            await self._reject(scope, send)
            return

        consumed = 0

        async def limited_receive() -> dict:
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > self.max_bytes:
                    raise _BodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _BodyTooLarge:
            await self._reject(scope, send)
        except BaseExceptionGroup as exc:
            if not _contains_body_limit(exc):
                raise
            await self._reject(scope, send)

    async def _reject(self, scope: dict[str, Any], send: Callable[..., Awaitable[None]]) -> None:
        body = json.dumps({"detail": "Request body too large"}).encode()
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
            (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"),
            (b"referrer-policy", b"no-referrer"),
            (b"x-frame-options", b"DENY"),
            (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"),
            (b"pragma", b"no-cache"),
        ]
        request_headers = dict(scope.get("headers", []))
        origin = request_headers.get(b"origin", b"").decode("latin-1")
        if origin in self.allowed_origins:
            headers.extend([(b"access-control-allow-origin", origin.encode()), (b"vary", b"Origin")])
        if self.production and scope.get("scheme") == "https":
            headers.append((b"strict-transport-security", f"max-age={self.hsts_seconds}".encode()))
        await send({"type": "http.response.start", "status": 413, "headers": headers})
        await send({"type": "http.response.body", "body": body})
