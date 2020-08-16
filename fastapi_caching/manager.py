import logging
from typing import Sequence

from fastapi import Depends

from . import constants
from .backends import CacheBackendBase
from .dependencies import ResponseCacheDependency
from .exceptions import NoBackendConfigured

__all__ = ("CacheManager",)

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(
        self,
        backend: CacheBackendBase = None,
        *,
        ttl: int = constants.DEFAULT_TTL,
        no_cache_query_param: str = "no-cache",
    ):
        self._backend = backend
        self._ttl = ttl
        self._no_cache_query_param = no_cache_query_param

    def setup(
        self,
        backend: CacheBackendBase = None,
        *,
        ttl: int = None,
        no_cache_query_param: str = None,
    ):
        if backend is not None:
            self._backend = backend
        if ttl is not None:
            self._ttl = ttl
        if no_cache_query_param is not None:
            self._no_cache_query_param = no_cache_query_param

    @property
    def backend(self) -> CacheBackendBase:
        if self._backend is None:
            raise NoBackendConfigured()
        return self._backend

    def from_request(self, ttl: int = None) -> Depends:
        d = ResponseCacheDependency(
            self.backend, no_cache_query_param=self._no_cache_query_param, ttl=ttl,
        )
        return Depends(d)

    async def invalidate_tag(self, tag: str):
        """Delete cache entries associated with the given tag"""
        await self.backend.invalidate_tag(tag)

    async def invalidate_tags(self, tags: Sequence[str]):
        """Delete cache entries associated with the given tags"""
        await self.backend.invalidate_tags(tags)
