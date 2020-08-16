import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from . import helpers


@pytest.fixture
def app():
    return FastAPI()


@pytest.fixture
async def async_client(app):
    async with AsyncClient(app=app, base_url="http://127.0.0.1") as ac:
        yield ac


@pytest.fixture
def redis_backend():
    return helpers.make_redis_backend()


@pytest.fixture
def inmem_backend():
    return helpers.make_inmemory_backend()
