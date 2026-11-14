import os
from fastapi.testclient import TestClient
import mobile_server

client = TestClient(mobile_server.app)

def test_securemonie_android_pwa_and_banking(monkeypatch):
    test_db = "temp_securemonie.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    monkeypatch.setattr(mobile_server, "DB_PATH", test_db)

    # 1. Verify Android PWA manifest & 192x192 PNG icon
    manifest = client.get("/manifest.json")
    assert manifest.status_code == 200
    assert manifest.json()["short_name"] == "Securemonie"
    assert client.get("/icon-192.png").content.startswith(b"\x89PNG")

    # 2. Register two users & test PIN-protected top-up + P2P transfer
    u1 = client.post("/api/register", json={"full_name": "Esosa", "email": "esosa@sm.ng", "password": "Password1", "pin": "1234"}).json()
    u2 = client.post("/api/register", json={"full_name": "Ada", "email": "ada@sm.ng", "password": "Password1", "pin": "5678"}).json()
    h1 = {"Authorization": f"Bearer {u1['token']}"}
    h2 = {"Authorization": f"Bearer {u2['token']}"}

    assert client.post("/api/deposit", headers=h1, json={"amount": 20000, "pin": "1234"}).status_code == 200
    assert client.post("/api/transfer", headers=h1, json={"recipient_account": u2["account_number"], "amount": 5000, "pin": "1234"}).status_code == 200
    assert client.get("/api/wallet", headers=h2).json()["wallet_ngn"] == 5000.0

    # 3. Test SecureVault save + 30-day interest & PDF receipt
    assert client.post("/api/vault", headers=h1, json={"action": "save", "amount": 10000, "pin": "1234"}).status_code == 200
    assert client.post("/api/vault", headers=h1, json={"action": "interest", "pin": "1234"}).status_code == 200
    assert client.get("/api/statement/pdf", headers=h1).content.startswith(b"%PDF")

    if os.path.exists(test_db):
        os.remove(test_db)
