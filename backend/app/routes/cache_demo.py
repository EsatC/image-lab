"""
Redis cache demo routes.
Used to demonstrate caching for the 12-factor cloud project.
"""
import json
import os
import time

from flask import Blueprint, jsonify
from redis import Redis
from redis.exceptions import RedisError

cache_bp = Blueprint("cache_demo", __name__)


def get_redis_client():
    redis_url = os.environ.get("REDIS_URL")

    if not redis_url:
        return None

    return Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


@cache_bp.get("/cache-demo")
def cache_demo():
    """
    First request: MISS, writes data to Redis.
    Next requests within 60 seconds: HIT, reads data from Redis.
    """
    redis_client = get_redis_client()

    if redis_client is None:
        return jsonify({
            "cache": "disabled",
            "message": "REDIS_URL is not configured"
        }), 503

    cache_key = "imagelab:cache-demo"

    try:
        cached_value = redis_client.get(cache_key)

        if cached_value:
            data = json.loads(cached_value)
            data["cache"] = "HIT"
            data["served_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            return jsonify(data)

        data = {
            "message": "Redis cache is working",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ttl_seconds": 60
        }

        redis_client.setex(cache_key, 60, json.dumps(data))

        data["cache"] = "MISS"
        return jsonify(data)

    except RedisError as exc:
        return jsonify({
            "cache": "error",
            "message": str(exc)
        }), 500
