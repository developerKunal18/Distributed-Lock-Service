import os
import secrets
import redis
from flask import Flask, jsonify, request

app = Flask(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
LOCK_TTL_SECONDS = 30
LOCK_PREFIX = "distributed-lock:"

def lock_key(resource):
    return f"{LOCK_PREFIX}{resource}"

def acquire_lock(resource):
    token = secrets.token_urlsafe(32)
    acquired = redis_client.set(lock_key(resource), token, nx=True, ex=LOCK_TTL_SECONDS)
    return token if acquired else None

def release_lock(resource, token):
    script = '''
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    '''
    return redis_client.eval(script, 1, lock_key(resource), token) == 1

@app.get("/health")
def health():
    try:
        redis_client.ping()
        return jsonify({"status": "ok", "redis": "connected"})
    except redis.RedisError:
        return jsonify({"status": "degraded", "redis": "unavailable"}), 503

@app.post("/api/lock/<resource>")
def acquire(resource):
    token = acquire_lock(resource)
    if token is None:
        return jsonify({"error": "lock_unavailable", "resource": resource}), 409
    return jsonify({
        "resource": resource,
        "token": token,
        "expires_in": LOCK_TTL_SECONDS
    }), 201

@app.delete("/api/lock/<resource>")
def release(resource):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "lock_token_required"}), 401
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        return jsonify({"error": "lock_token_required"}), 401
    if not release_lock(resource, token):
        return jsonify({
            "error": "invalid_lock_owner",
            "message": "The lock is missing or belongs to another owner."
        }), 403
    return jsonify({"resource": resource, "released": True})

@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "resource_not_found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
