import asyncio
import logging
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException

from fastapi_caching import CacheManager, RedisBackend, ResponseCache, hashers

from . import db
from .models import Product
from .settings import get_settings

app = FastAPI()

settings = get_settings()
logger = logging.getLogger(__name__)

# NOTE: In a real world scenario a version identifier for the given code deployment
# should be used, commonly this would be the commit hash from your VCS.
# Here we're using a hash of installed packages combined with a hash of the files in
# the redis_app directory.
app_version = "-".join(
    [hashers.installed_packages_hash(), hashers.files_hash(Path(__file__).parent)]
)

cache_backend = RedisBackend(
    host=settings.redis_host,
    port=settings.redis_port,
    prefix="redis_app",
    app_version=app_version,
    oob_refresh=False,
)
cache_manager = CacheManager()
cache_manager.setup(cache_backend)

logger.info(f"App version: {app_version}")


@app.on_event("startup")
async def connect_db():
    await db.database.connect()
    db.create_all()


@app.on_event("shutdown")
async def disconnect_db():
    await db.database.disconnect()


@app.post("/products", response_model=Product)
async def create_product(product: Product):
    await db.create_product(product)
    await cache_manager.invalidate_tag("all-products")
    return product


@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: uuid.UUID, product: Product):
    product.id = product_id

    if not await db.product_exists(product_id):
        raise HTTPException(404, detail="Product does not exist")

    await db.update_product(product)
    await cache_manager.invalidate_tags([f"product-{product.id}", "all-products"])
    return product


@app.get("/products", response_model=List[Product])
async def list_products(rcache: ResponseCache = cache_manager.from_request()):
    if rcache.exists():
        return rcache.data

    products = await db.fetch_products()

    await asyncio.sleep(1)  # Some heavy processing...

    await rcache.set(products, tag="all-products")

    return products


@app.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: uuid.UUID, rcache: ResponseCache = cache_manager.from_request()
):
    if rcache.exists():
        return rcache.data

    product = await db.fetch_product(product_id)

    if product is None:
        raise HTTPException(404, detail="Product not found")

    await rcache.set(product, tag=f"product-{product_id}")

    return product


@app.get("/__admin/reset/all")
async def reset_all_data():
    db.clear_data()
    await cache_backend.reset()
    return {"ok": True}


@app.get("/__admin/reset/cache")
async def reset_cache():
    await cache_backend.reset()
    return {"ok": True}


@app.get("/__admin/reset/db")
async def reset_db():
    db.clear_data()
    return {"ok": True}
