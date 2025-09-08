import os

from flask_caching import Cache

cache = Cache()

REDIS_URL = os.getenv("REDIS_URL", "redis://:secret@localhost:17285/0")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": REDIS_URL
}
