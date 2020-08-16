import uuid

import sqlalchemy as sa
from databases import Database

from . import db_types
from .settings import get_settings

db_uri = get_settings().db_uri

database = Database(db_uri)
metadata = sa.MetaData()

product_tbl = sa.Table(
    "product",
    metadata,
    sa.Column("id", db_types.Uuid, primary_key=True),
    sa.Column("name", sa.Text),
    sa.Column("description", sa.Text),
    sa.Column("created_at", sa.DateTime),
)


def create_all():
    metadata.create_all(bind=sa.create_engine(db_uri))


def clear_data():
    engine = sa.create_engine(db_uri)
    for tbl in metadata.tables.values():
        engine.execute(tbl.delete())


async def create_product(product):
    await database.execute(product_tbl.insert().values(product.dict()))


async def update_product(product):
    values = product.dict()
    await database.execute(
        product_tbl.update().values(values).where(product_tbl.c.id == product.id)
    )


async def fetch_products():
    return await database.fetch_all(product_tbl.select())


async def product_exists(product_id: uuid.UUID) -> bool:
    val = await database.fetch_val(
        sa.select([product_tbl.c.id]).where(product_tbl.c.id == product_id).limit(1)
    )
    return val is not None


async def fetch_product(product_id: uuid.UUID):
    return await database.fetch_one(
        product_tbl.select().where(product_tbl.c.id == product_id)
    )
