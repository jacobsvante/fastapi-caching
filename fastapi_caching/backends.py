import logging
import pickle
from typing import Any, Optional, Sequence

import cachetools

from . import constants
from .exceptions import CachingNotEnabled
from .raw import RawCacheObject

try:
    import aioredis
except ImportError:
    aioredis = None


__all__ = ("RedisBackend", "InMemoryBackend", "NoOpBackend")

logger = logging.getLogger(__name__)


class CacheBackendBase:
    def setup(self):
        """Configure backend lazily, may be needed in advanced use cases"""
        # NOTE: Default method is a no-op

    def enable(self):
        self._is_enabled = True

    def disable(self):
        self._is_enabled = False

    def is_enabled(self) -> bool:
        return getattr(self, "_is_enabled", True)

    async def get(self, key: str) -> Optional[RawCacheObject]:
        self._ensure_enabled()
        return await self._get_impl(key)

    async def set(
        self,
        key: str,
        obj: RawCacheObject,
        *,
        tags: Sequence[str] = (),
        ttl: int = None,
    ) -> bool:
        self._ensure_enabled()
        if not isinstance(obj, RawCacheObject):
            obj = RawCacheObject(data=obj)
        return await self._set_impl(key, obj, tags=tags, ttl=ttl)

    async def invalidate_tag(self, tag: str):
        """Delete cache entries associated with the given tag"""
        self._ensure_enabled()
        return await self._invalidate_tag_impl(tag)

    async def invalidate_tags(self, tags: Sequence[str]):
        """Delete cache entries associated with the given tags"""
        self._ensure_enabled()
        return await self._invalidate_tags_impl(tags)

    async def reset(self):
        """Delete all stored cache related keys"""
        self._ensure_enabled()
        return await self._reset_impl()

    async def _get_impl(self, key: str) -> Optional[RawCacheObject]:
        raise NotImplementedError

    async def _set_impl(
        self,
        key: str,
        cache_object: RawCacheObject,
        *,
        tags: Sequence[str] = (),
        ttl: int = None,
    ) -> bool:
        raise NotImplementedError

    async def _invalidate_tag_impl(self, tag: str):
        raise NotImplementedError

    async def _invalidate_tags_impl(self, tags: Sequence[str]):
        raise NotImplementedError

    async def _reset_impl(self):
        raise NotImplementedError

    def _dumps(self, obj: Any) -> bytes:
        return pickle.dumps(obj)

    def _loads(self, raw: bytes) -> Any:
        return pickle.loads(raw)

    def _ensure_enabled(self):
        if not self.is_enabled():
            raise CachingNotEnabled()


class NoOpBackend(CacheBackendBase):
    async def _get_impl(self, key: str) -> Optional[RawCacheObject]:
        return None

    async def _set_impl(
        self,
        key: str,
        cache_object: RawCacheObject,
        *,
        tags: Sequence[str] = (),
        ttl: int = None,
    ) -> bool:
        return True

    async def _invalidate_tag_impl(self, tag: str):
        pass

    async def _invalidate_tags_impl(self, tags: Sequence[str]):
        pass

    async def _reset_impl(self):
        pass


class InMemoryBackend(CacheBackendBase):
    def __init__(
        self, maxsize: int = 50_000, ttl: int = constants.DEFAULT_TTL,
    ):
        self._cached = cachetools.TTLCache(maxsize, ttl)
        self._tag_to_keys = {}

    def setup(
        self, *, maxsize: int = 50_000, ttl: int = constants.DEFAULT_TTL,
    ):
        """Configure backend lazily, may be needed in advanced use cases"""
        self._cached = cachetools.TTLCache(maxsize, ttl)

    async def _get_impl(self, key: str) -> Optional[RawCacheObject]:
        try:
            obj = self._cached[key]
        except KeyError:
            return None
        else:
            return self._loads(obj)

    async def _set_impl(
        self,
        key: str,
        cache_object: RawCacheObject,
        *,
        tags: Sequence[str] = (),
        ttl: int = None,
    ) -> bool:
        self._cached[key] = self._dumps(cache_object)
        for tag in tags:
            tag_keys = self._tag_to_keys.setdefault(tag, [])
            tag_keys.append(key)
        return True

    async def _invalidate_tag_impl(self, tag: str):
        try:
            keys = self._tag_to_keys[tag]
        except KeyError:
            return
        else:
            for key in keys:
                self._cached.pop(key, None)
            del self._tag_to_keys[tag]

    async def _invalidate_tags_impl(self, tags: Sequence[str]):
        for tag in tags:
            await self.invalidate_tag(tag)

    async def _reset_impl(self):
        """Reset cache completely"""
        self._cached = {}
        self._tag_to_keys = {}


class RedisBackend(CacheBackendBase):
    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 6379,
        password: str = None,
        prefix: str = "fastapi-caching",
        app_version: str = None,
        ttl: int = constants.DEFAULT_TTL,
        redis: Any = None,
    ):
        self._app_version = app_version
        self._host = host
        self._port = port
        self._password = password
        self._prefix = prefix
        self._ttl = ttl
        self._redis = redis
        self._setup_prefix(prefix)

    def setup(
        self,
        *,
        host: str = None,
        port: int = None,
        password: str = None,
        prefix: str = None,
        app_version: str = None,
        ttl: int = None,
    ):
        """Configure backend lazily, may be needed in advanced use cases"""
        if host is not None:
            self._host = host
        if port is not None:
            self._port = port
        if password is not None:
            self._password = password
        if prefix is not None:
            self._setup_prefix(prefix)
        if app_version is not None:
            self._app_version = app_version
        if ttl is not None:
            self._ttl = ttl

    def _setup_prefix(self, prefix: str):
        if not prefix:
            raise RuntimeError("`prefix` is required for redis backend")
        if prefix.endswith(":"):
            prefix = prefix[0:-1]
        self._prefix = prefix

    def _get_full_prefix(self) -> str:
        if self._app_version is not None:
            return f"{self._prefix}:{self._app_version}"
        else:
            return self._prefix

    async def _get_impl(self, key: str) -> Optional[RawCacheObject]:
        redis = await self._get_redis()
        obj = await redis.get(self._prefixed(key))
        if obj is None:
            return None
        else:
            return self._loads(obj)

    async def _set_impl(
        self,
        key: str,
        cache_object: RawCacheObject,
        *,
        tags: Sequence[str] = (),
        ttl: int = None,
    ) -> bool:
        redis = await self._get_redis()
        dumped = self._dumps(cache_object)
        tr = redis.multi_exec()

        tr.set(self._prefixed(key), dumped, expire=ttl or self._ttl)

        for tag in tags:
            logger.debug(f"Adding key {key} to tag {tag}")
            tr.sadd(self._prefixed(f"tags_to_keys:{tag}"), key)

        success, *rest = await tr.execute()
        return success

    async def _invalidate_tag_impl(self, tag: str):
        await self.invalidate_tags([tag])

    async def _invalidate_tags_impl(self, tags: Sequence[str]):
        redis = await self._get_redis()

        all_keys = []
        for tag in tags:
            tag_key = self._prefixed(f"tags_to_keys:{tag}")
            keys = [
                *(
                    self._prefixed(k)
                    for k in await redis.smembers(tag_key, encoding="utf-8",)
                ),
                tag_key,
            ]
            logger.debug(f"Invalidating tag {tag}, containing the given keys: {keys}")
            all_keys.extend(keys)

        if len(all_keys) > 0:
            await redis.unlink(*all_keys)

    async def _reset_impl(self):
        await self._unlink_by_prefix(self._prefix)

    async def reset_version(self):
        """Delete all stored cache related keys for the current app version"""
        full_prefix = self._get_full_prefix()
        await self._unlink_by_prefix(full_prefix)

    async def _get_redis(self):
        if self._redis is None:
            if aioredis is None:
                raise RuntimeError(
                    "Cannot instantiate Redis backend without aioredis installed",
                )
            else:
                self._redis = await aioredis.create_redis_pool(
                    f"redis://{self._host}:{self._port}", password=self._password
                )
        return self._redis

    async def _unlink_by_prefix(self, prefix: str):
        if prefix.endswith(":"):
            prefix = prefix[0:-1]
        redis = await self._get_redis()
        resp = await redis.eval(
            """local keys = redis.call('keys', ARGV[1])
            local unpack = table.unpack or unpack
            for i=1,#keys,5000 do
            redis.call('unlink', unpack(keys, i, math.min(i+4999, #keys)))
                end
            return keys""",
            args=[f"{prefix}:*"],
        )
        unlinked_keys = ", ".join(k.decode() for k in resp)
        logger.debug(f"Unlinked keys: {unlinked_keys}")

    def _prefixed(self, unprefixed_key: str) -> str:
        full_prefix = self._get_full_prefix()
        return f"{full_prefix}:{unprefixed_key}"
