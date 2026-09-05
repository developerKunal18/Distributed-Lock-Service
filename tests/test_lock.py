import app as app_module

class FakeRedis:
    def __init__(self):
        self.data = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    def eval(self, _script, _numkeys, key, token):
        if self.data.get(key) == token:
            del self.data[key]
            return 1
        return 0

    def ping(self):
        return True

def setup_function():
    app_module.redis_client = FakeRedis()

def test_acquire_lock():
    response = app_module.app.test_client().post("/api/lock/payment")
    assert response.status_code == 201
    assert response.json["token"]

def test_second_owner_cannot_acquire_same_lock():
    client = app_module.app.test_client()
    assert client.post("/api/lock/payment").status_code == 201
    assert client.post("/api/lock/payment").status_code == 409

def test_only_owner_can_release():
    client = app_module.app.test_client()
    acquired = client.post("/api/lock/payment")
    token = acquired.json["token"]
    wrong = client.delete("/api/lock/payment", headers={"Authorization": "Bearer wrong"})
    assert wrong.status_code == 403
    released = client.delete(
        "/api/lock/payment",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert released.status_code == 200
    assert released.json["released"] is True

def test_release_requires_token():
    response = app_module.app.test_client().delete("/api/lock/payment")
    assert response.status_code == 401

def test_health():
    response = app_module.app.test_client().get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
