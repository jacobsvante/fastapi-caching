import logging
from typing import Sequence, Optional, Dict, List

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
        no_skip_authorized: bool = False,
    ):
        self._backend = backend
        self._ttl = ttl
        self._no_cache_query_param = no_cache_query_param
        self._no_skip_authorized = no_skip_authorized

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

    def from_request(self, ttl: int = None, include_headers: List[str] = None, include_state: List[str] = None) -> Depends:
        """Create a cache instance from the current request.

        Parameters
        ----------
        ttl : int
            (Optional) Time to live for cached objects in seconds
        no_cache_query_param : bool
            (Optional) Query parameter that indicates to skip caching
        no_skip_authorized : bool
            (Optional) Whether to disable skipping requests containing an 'Authorization' header (i.e. true means to still cache them)
        include_headers : List[str]
            (Optional) Additional headers field to consider for caching (case-insensitive)
        include_state : List[str]
            (Optional) Addition properties of the Starlette Request's state object to consider for caching (see https://www.starlette.io/requests/#other-state)
        """
        d = ResponseCacheDependency(
            self.backend, ttl=ttl, no_cache_query_param=self._no_cache_query_param, no_skip_authorized=self._no_skip_authorized, include_headers=include_headers, include_state=include_state,
        )
        return Depends(d)

    async def invalidate_tag(self, tag: str):
        """Delete cache entries associated with the given tag"""
        await self.backend.invalidate_tag(tag)

    async def invalidate_tags(self, tags: Sequence[str]):
        """Delete cache entries associated with the given tags"""
        await self.backend.invalidate_tags(tags)
