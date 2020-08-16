import aioredis
from fakeredis.aioredis import FakeConnectionsPool

from fastapi_caching import InMemoryBackend, RedisBackend


def make_inmemory_backend():
    return InMemoryBackend()


def make_redis_backend():
    pool = FakeConnectionsPool(minsize=1, maxsize=10)
    return RedisBackend(redis=aioredis.Redis(pool))


def make_caching_backends():
    return (make_inmemory_backend(), make_redis_backend())
