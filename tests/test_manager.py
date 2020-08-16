import pytest

from fastapi_caching import CacheManager, InMemoryBackend, NoBackendConfigured


def test_that_manager_cant_be_used_without_backend():
    cache_manager = CacheManager()

    with pytest.raises(NoBackendConfigured):
        cache_manager.backend  # Verified on property access


def test_that_backend_can_be_set_lazily():
    cache_manager = CacheManager()
    cache_backend = InMemoryBackend()
    cache_manager.setup(backend=cache_backend)

    assert cache_manager.backend is not None
