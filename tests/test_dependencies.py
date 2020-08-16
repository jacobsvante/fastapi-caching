import pytest

from fastapi_caching import CacheManager, InMemoryBackend, ResponseCache
from fastapi_caching.objects import NoOpResponseCache


@pytest.mark.asyncio
async def test_that_response_cache_can_be_set(app, async_client):
    cache_backend = InMemoryBackend()
    cache_manager = CacheManager(cache_backend)

    cached_object = await cache_backend.get("/|GET")
    assert cached_object is None

    @app.get("/")
    async def get_products(rcache: ResponseCache = cache_manager.from_request()):
        assert rcache.__class__ is ResponseCache
        resp_data = [{"foo": "bar"}]
        await rcache.set(resp_data)
        return resp_data

    resp = await async_client.get("/")
    assert resp.status_code == 200

    cached_object = await cache_backend.get("/|GET")
    assert cached_object.data == [{"foo": "bar"}]


@pytest.mark.asyncio
async def test_that_cache_isnt_fetched_from_disabled_backend(app, async_client):
    cache_backend = InMemoryBackend()
    cache_manager = CacheManager(cache_backend)
    cache_manager.disable()

    @app.get("/")
    async def home(rcache: ResponseCache = cache_manager.from_request()):
        assert rcache.__class__ is NoOpResponseCache

    await async_client.get("/")
