import logging

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
        ttl: int = None,
    ):
        self._backend = backend
        self._no_cache_query_param = no_cache_query_param
        self._ttl = ttl

    async def __call__(self, request: Request) -> ResponseCache:
        cache = ResponseCache(
            self._backend,
            request,
            no_cache_query_param=self._no_cache_query_param,
            ttl=self._ttl,
        )

        if "authorization" in request.headers:
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
