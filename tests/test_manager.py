from fastapi_caching import CacheManager, InMemoryBackend


def test_that_ttl_can_be_set_lazily():
    cache_backend = InMemoryBackend()
    cache_manager = CacheManager(cache_backend)
    cache_manager.setup(ttl=1337)

    assert cache_manager.backend is not None
