import pytest

from fastapi_caching import CachingNotEnabled, InMemoryBackend, RedisBackend

from . import helpers


@pytest.mark.asyncio
@pytest.mark.parametrize("cache_backend", helpers.make_caching_backends())
async def test_that_cache_can_be_set(cache_backend):
    was_set = await cache_backend.set("hello_key", "world")
    assert was_set is True

    cache_obj = await cache_backend.get("hello_key")

    assert cache_obj.data == "world"


@pytest.mark.asyncio
@pytest.mark.parametrize("cache_backend", helpers.make_caching_backends())
async def test_that_cache_does_not_return_data_on_non_existing_keys(cache_backend):
    data = await cache_backend.get("hello_key")
    assert data is None


@pytest.mark.asyncio
@pytest.mark.parametrize("cache_backend", helpers.make_caching_backends())
async def test_that_cache_can_be_cleared(cache_backend):
    await cache_backend.set("a", "b")
    await cache_backend.set("c", "d")

    await cache_backend.reset()

    a_obj = await cache_backend.get("a")
    b_obj = await cache_backend.get("b")

    assert a_obj is None
    assert b_obj is None


def test_that_redis_backend_can_be_configured_lazily():
    backend = RedisBackend()
    backend.setup(prefix="my-cool-app")
    assert backend._get_full_prefix() == "my-cool-app"


def test_that_inmemory_backend_can_be_configured_lazily():
    backend = InMemoryBackend()
    backend.setup(maxsize=2)


@pytest.mark.asyncio
async def test_that_exception_is_raised_for_disabled_backend():
    cache_backend = InMemoryBackend()
    cache_backend.disable()
    with pytest.raises(CachingNotEnabled):
        await cache_backend.set("a", "b")
    with pytest.raises(CachingNotEnabled):
        await cache_backend.get("a")
    with pytest.raises(CachingNotEnabled):
        await cache_backend.invalidate_tag("foo")
    with pytest.raises(CachingNotEnabled):
        await cache_backend.invalidate_tags(["foo", "bar"])
    with pytest.raises(CachingNotEnabled):
        await cache_backend.invalidate_tags(["foo", "bar"])
    with pytest.raises(CachingNotEnabled):
        await cache_backend.reset()
