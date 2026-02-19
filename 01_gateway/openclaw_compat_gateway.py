"""
OpenClaw Web 介面相容 Gateway

用途：
- 將 LobsterShell 作為 OpenClaw 控制頁前置層
- 保持 OpenClaw Web 介面協議兼容（HTTP + WebSocket）
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

from aiohttp import ClientSession, ClientTimeout, WSMsgType, web

logger = logging.getLogger(__name__)


_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
}


def _clean_headers(headers: Dict[str, str], target_host: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _HOP_HEADERS:
            continue
        result[key] = value
    result["Host"] = target_host
    return result


class OpenClawCompatGateway:
    def __init__(
        self,
        target_base: str,
        request_timeout: int = 120,
    ):
        self.target_base = target_base.rstrip("/")
        self.timeout = ClientTimeout(total=request_timeout)
        self._session: Optional[ClientSession] = None

    async def startup(self, app: web.Application) -> None:
        self._session = ClientSession(timeout=self.timeout)
        logger.info("OpenClaw 相容 Gateway 已啟動，目標: %s", self.target_base)

    async def shutdown(self, app: web.Application) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def create_app(self) -> web.Application:
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self.handle_request)
        app.on_startup.append(self.startup)
        app.on_shutdown.append(self.shutdown)
        return app

    async def handle_request(self, request: web.Request) -> web.StreamResponse:
        ws_probe = web.WebSocketResponse()
        ws_ready = ws_probe.can_prepare(request)
        if ws_ready.ok:
            return await self._proxy_websocket(request)
        return await self._proxy_http(request)

    async def _proxy_http(self, request: web.Request) -> web.Response:
        if not self._session:
            raise web.HTTPServiceUnavailable(text="Gateway session is not ready")

        path_qs = request.rel_url.path_qs
        upstream_url = f"{self.target_base}{path_qs}"
        target_host = self.target_base.split("//", 1)[-1]

        body = await request.read()
        headers = _clean_headers(dict(request.headers), target_host)

        try:
            async with self._session.request(
                request.method,
                upstream_url,
                headers=headers,
                data=body if body else None,
                allow_redirects=False,
            ) as upstream_resp:
                response_body = await upstream_resp.read()
                resp_headers = {
                    key: value
                    for key, value in upstream_resp.headers.items()
                    if key.lower() not in _HOP_HEADERS
                }
                return web.Response(
                    status=upstream_resp.status,
                    headers=resp_headers,
                    body=response_body,
                )
        except Exception as exc:
            logger.exception("HTTP 轉發失敗: %s", exc)
            raise web.HTTPBadGateway(text=f"Upstream request failed: {exc}")

    async def _proxy_websocket(self, request: web.Request) -> web.WebSocketResponse:
        if not self._session:
            raise web.HTTPServiceUnavailable(text="Gateway session is not ready")

        ws_server = web.WebSocketResponse()
        await ws_server.prepare(request)

        path_qs = request.rel_url.path_qs
        if self.target_base.startswith("https://"):
            ws_url = f"wss://{self.target_base.split('://', 1)[1]}{path_qs}"
        else:
            ws_url = f"ws://{self.target_base.split('://', 1)[1]}{path_qs}"

        target_host = self.target_base.split("//", 1)[-1]
        headers = _clean_headers(dict(request.headers), target_host)

        try:
            async with self._session.ws_connect(ws_url, headers=headers) as ws_client:
                await asyncio.gather(
                    self._pipe_client_to_upstream(ws_server, ws_client),
                    self._pipe_upstream_to_client(ws_server, ws_client),
                )
        except Exception as exc:
            logger.exception("WebSocket 轉發失敗: %s", exc)
            await ws_server.close(message=b"upstream websocket failed")

        return ws_server

    async def _pipe_client_to_upstream(self, ws_server: web.WebSocketResponse, ws_client) -> None:
        async for msg in ws_server:
            if msg.type == WSMsgType.TEXT:
                await ws_client.send_str(msg.data)
            elif msg.type == WSMsgType.BINARY:
                await ws_client.send_bytes(msg.data)
            elif msg.type == WSMsgType.CLOSE:
                await ws_client.close()
                break

    async def _pipe_upstream_to_client(self, ws_server: web.WebSocketResponse, ws_client) -> None:
        async for msg in ws_client:
            if msg.type == WSMsgType.TEXT:
                await ws_server.send_str(msg.data)
            elif msg.type == WSMsgType.BINARY:
                await ws_server.send_bytes(msg.data)
            elif msg.type == WSMsgType.CLOSE:
                await ws_server.close()
                break


def run_compat_gateway(
    listen_host: str,
    listen_port: int,
    target_base: str,
    timeout: int,
) -> None:
    gateway = OpenClawCompatGateway(target_base=target_base, request_timeout=timeout)
    app = gateway.create_app()
    web.run_app(app, host=listen_host, port=listen_port)
