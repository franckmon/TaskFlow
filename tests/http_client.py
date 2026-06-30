from __future__ import annotations

import typing

import httpx
import starlette.testclient as starlette_testclient
from starlette.types import ASGIApp

if typing.TYPE_CHECKING:
    import httpx._client


class TestClient(starlette_testclient.TestClient):
    """Starlette TestClient that uses explicit transport= only for httpx.Client."""

    def __init__(
        self,
        app: ASGIApp,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: typing.Optional[typing.Dict[str, typing.Any]] = None,
        cookies: httpx._client.CookieTypes = None,
        headers: typing.Dict[str, str] | None = None,
    ) -> None:
        self.async_backend = starlette_testclient._AsyncBackend(
            backend=backend,
            backend_options=backend_options or {},
        )
        if starlette_testclient._is_asgi3(app):
            asgi_app = typing.cast(starlette_testclient.ASGI3App, app)
        else:
            app = typing.cast(starlette_testclient.ASGI2App, app)
            asgi_app = starlette_testclient._WrapASGI2(app)
        self.app = asgi_app
        self.app_state: dict[str, typing.Any] = {}
        transport = starlette_testclient._TestClientTransport(
            self.app,
            portal_factory=self._portal_factory,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
            app_state=self.app_state,
        )
        if headers is None:
            headers = {}
        headers.setdefault("user-agent", "testclient")
        httpx.Client.__init__(
            self,
            base_url=base_url,
            headers=headers,
            transport=transport,
            follow_redirects=True,
            cookies=cookies,
        )
