# FastAPI-Caching

Cache library for FastAPI with tag based invalidation

## Features

- Automatic response cache fetching using FastAPI dependencies
- Fine-grained control over when to return and set the cache
- Ability to invalidate cached objects based on a concept of associated tags. See [examples/redis_app](/examples/redis_app) for an example.

## Installation

With in-memory support only:
```bash
pip install fastapi-caching
```

NOTE: In-memory backend is only recommended when your app is only run as a single instance.

With redis support (through the [aioredis](https://aioredis.readthedocs.io/) library):
```bash
pip install fastapi-caching[redis]
```

## Usage examples

Examples on how to use [can be found here](/examples).


## Changelog

### v0.1.2, 2020-08-16

- Feature: Support lazy setup of cache manager

### v0.2.0, 2020-08-16

- Breaking change: Revert to requiring `backend` to be passed to CacheManager
- Feature: Support lazy configuration of the caching backend
