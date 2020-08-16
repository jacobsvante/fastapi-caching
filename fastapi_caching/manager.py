import logging
from typing import Sequence

from fastapi import Depends

from . import constants
from .backends import CacheBackendBase
from .dependencies import ResponseCacheDependency

__all__ = ("CacheManager",)

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(
        self,
        backend: CacheBackendBase,
        *,
        ttl: int = constants.DEFAULT_TTL,
        no_cache_query_param: str = "no-cache",
    ):
        self._backend = backend
        self._ttl = ttl
        self._no_cache_query_param = no_cache_query_param

    def setup(
        self, *, ttl: int = None, no_cache_query_param: str = None,
    ):
        if ttl is not None:
            self._ttl = ttl
        if no_cache_query_param is not None:
            self._no_cache_query_param = no_cache_query_param

    def enable(self):
        self._backend.enable()

    def disable(self):
        self._backend.disable()

    def is_enabled(self) -> bool:
        self._backend.is_enabled()

    @property
    def backend(self) -> CacheBackendBase:
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
