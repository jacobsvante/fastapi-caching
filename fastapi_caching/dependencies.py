import logging
from typing import Optional, Dict, List

from starlette.requests import Request

from .backends import CacheBackendBase
from .objects import NoOpResponseCache, ResponseCache

logger = logging.getLogger(__name__)

__all__ = ("ResponseCacheDependency",)


class ResponseCacheDependency:
    def __init__(
        self,
        backend: CacheBackendBase,
        *,
        no_cache_query_param: str = "no-cache",
        no_skip_authorized: bool = False,
        ttl: int = None,
        include_headers: List[str] = None,
        include_state: List[str] = None,
    ):
        self._backend = backend
        self._no_cache_query_param = no_cache_query_param
        self._no_skip_authorized = no_skip_authorized
        self._ttl = ttl
        self._include_headers = include_headers
        self._include_state = include_state

    async def __call__(self, request: Request) -> ResponseCache:
        cache = ResponseCache(
            self._backend,
            request,
            no_cache_query_param=self._no_cache_query_param,
            ttl=self._ttl,
            include_headers=self._include_headers,
            include_state=self._include_state,
        )

        if not self._backend.is_enabled():
            logger.debug(
                f"{cache.key}: Caching backend not enabled - returning no-op cache"
            )
            return NoOpResponseCache()
        elif "authorization" in request.headers and not self._no_skip_authorized:
            logger.debug(
                f"{cache.key}: Authorization header set - not fetching from cache"
            )
            return NoOpResponseCache()
        elif (
            self._no_cache_query_param is not None
            and self._no_cache_query_param in request.query_params
        ):
            logger.debug(
                f"{cache.key}: The no-cache query parameter was specified - not "
                f"fetching from cache, but will update it afterwards."
            )
            return cache
        else:
            await cache.fetch()
            if cache.data is None:
                logger.debug(f"{cache.key}: No cached response data found")
            else:
                logger.debug(
                    f"{cache.key}: Found cached response data with "
                    f"timestamp {cache.obj.timestamp}"
                )
            return cache
