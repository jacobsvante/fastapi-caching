from typing import Any, Sequence, Dict, Optional, List

from starlette.requests import Request

from .backends import CacheBackendBase
from .raw import RawCacheObject

__all__ = ("ResponseCache",)


class ResponseCache:
    """Object returned by ResponseCacheDependency

    Dependency ensures that an existing cached item for the given endpoint is
    automatically fetched.
    """

    def __init__(
        self,
        backend: CacheBackendBase,
        request: Request,
        no_cache_query_param: str = "no-cache",
        ttl: int = None,
        include_headers: List[str] = None,
        include_state: List[str] = None,
    ):
        self._backend = backend
        self._request = request
        self._no_cache_query_param = no_cache_query_param
        self._include_headers = include_headers
        self._include_state = include_state
        self._ttl = ttl
        self.key = self._make_key(request)
        self._obj = None

    @property
    def obj(self) -> RawCacheObject:
        return self._obj

    @property
    def data(self) -> Any:
        return None if self._obj is None else self._obj.data

    def exists(self) -> bool:
        """Return whether or not there's an existing cache for this response"""
        return self._obj is not None

    async def fetch(self):
        """Fetch and associate existing cache data"""
        self._obj = await self._backend.get(self.key)

    async def set(
        self, data: Any, *, ttl: int = None, tag: str = None, tags: Sequence[Any] = (),
    ) -> bool:
        tags = list(tags)
        if tag is not None:
            tags.append(tag)
        return await self._backend.set(
            key=self.key,
            obj=self._make_raw_cache_object(data),
            tags=tags,
            ttl=ttl or self._ttl,
        )

    def _make_raw_cache_object(self, data: Any) -> RawCacheObject:
        return RawCacheObject(data)

    def _make_key(self, request: Request) -> str:
        parts = [request.method, request.url.path]

        for k in request.query_params.keys():
            if k == self._no_cache_query_param:
                continue
            for v in request.query_params.getlist(k):
                parts.append(f"{k}={v}")

        for key in self._include_headers or []:
            parts.append(f'{key}={request.headers.get(key)}')

        for key in self._include_state or []:
            parts.append(f'{key}={getattr(request.state, key, None)}')

        return "|".join(sorted(parts))


class NoOpResponseCache(ResponseCache):
    """No-op version of the ResponseCache object returned by CacheDependency"""

    def __init__(self):
        self._obj = None

    async def fetch(self, *args, **kw):
        return

    async def set(self, *args, **kw):
        return
