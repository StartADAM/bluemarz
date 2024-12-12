from http import HTTPMethod, HTTPStatus
from typing import Any, AsyncIterable, Iterable
import httpx

_sync_client: httpx.Client = httpx.Client(timeout=60)
_async_client: httpx.AsyncClient = httpx.AsyncClient(timeout=60)


class HTTPRequestError(Exception):
    def __init__(
        self,
        req: httpx.Request,
        status: int = None,
        response: str = None,
        *args: object,
    ) -> None:
        self.req = req
        self.status = None if status is None else HTTPStatus(status)
        self.response = response
        super().__init__(
            f"Error executing request. Status: {self.status} Message:{self.response}",
            *args,
        )


class HTTPClient:
    def __init__(self, base_url: str, *, headers: dict[str, Any] = None) -> None:
        self.base_url = base_url
        self.headers = headers

    class ClientRequest:
        def __init__(
            self,
            client: "HTTPClient",
            method: HTTPMethod,
            path: str,
            *,
            params: dict[str, Any] = None,
            headers: dict[str, Any] = None,
            cookies: dict[str, Any] = None,
            content: str | bytes | Iterable[bytes] | AsyncIterable[bytes] = None,
            data: dict[str, Any] = None,
            files: dict[str, Any] = None,
            json: Any = None,
            stream: httpx.SyncByteStream | httpx.AsyncByteStream = None,
            extensions: dict[str, Any] = None,
        ) -> None:
            self._request = httpx.Request(
                str(method),
                client.base_url + path,
                params=params,
                headers=_join_dicts_none_safe(client.headers, headers),
                cookies=cookies,
                content=content,
                data=data,
                json=json,
                files=files,
                stream=stream,
                extensions=extensions,
            )
            self._client = client

        def send(self) -> httpx.Response:
            return self._client.send(self._request)

        async def asend(self) -> httpx.Response:
            return await self._client.asend(self._request)

    @property
    def client(self) -> httpx.Client:
        return _sync_client

    @property
    def aclient(self) -> httpx.AsyncClient:
        return _async_client

    def request(
        self,
        method: HTTPMethod,
        path: str,
        *,
        params: dict[str, Any] = None,
        headers: dict[str, Any] = None,
        cookies: dict[str, Any] = None,
        content: str | bytes | Iterable[bytes] | AsyncIterable[bytes] = None,
        data: dict[str, Any] = None,
        files: dict[str, Any] = None,
        json: Any = None,
        stream: httpx.SyncByteStream | httpx.AsyncByteStream = None,
        extensions: dict[str, Any] = None,
    ) -> ClientRequest:
        return HTTPClient.ClientRequest(
            self,
            method,
            path,
            params=params,
            headers=headers,
            cookies=cookies,
            content=content,
            data=data,
            json=json,
            files=files,
            stream=stream,
            extensions=extensions,
        )

    def send(self, req: httpx.Request) -> httpx.Response:
        try:
            response = self.client.send(req)
            response.raise_for_status()
            return response
        except httpx.HTTPError as ex:
            raise _convert_exception(req, ex)

    async def asend(self, req: httpx.Request) -> httpx.Response:
        try:
            response = await self.aclient.send(req)
            response.raise_for_status()
            return response
        except httpx.HTTPError as ex:
            raise _convert_exception(req, ex)


def _join_dicts_none_safe(d1: dict | None, d2: dict | None):
    if d1 and d2:
        return d1 | d2
    elif d1:
        return d1
    else:
        return d2


def _convert_exception(req: httpx.Request, ex: httpx.HTTPError) -> HTTPRequestError:
    try:
        raise ex
    except httpx.TimeoutException as ex:
        raise HTTPRequestError(
            req, HTTPStatus.GATEWAY_TIMEOUT, "Gateway timed out"
        ) from ex
    except httpx.RequestError as ex:
        raise HTTPRequestError(
            req, None, "Request could not be completed: " + str(ex)
        ) from ex
    except httpx.HTTPStatusError as ex:
        raise HTTPRequestError(req, ex.response.status_code, ex.response.text) from ex
