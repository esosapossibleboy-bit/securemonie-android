import os
from fastapi.testclient import TestClient
import mobile_server

client = TestClient(mobile_server.app)

def test_securemonie_moniepoint_features(monkeypatch):
    test_db = "temp_securemonie.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    monkeypatch.setattr(mobile_server, "DB_PATH", test_db)

    # 1. Verify Royal Indigo & Gold Android PWA manifest & 192x192 PNG icon
    manifest = client.get("/manifest.json")
    assert manifest.status_code == 200
    assert manifest.json()["theme_color"] == "#4f46e5"
    assert client.get("/icon-192.png").content.startswith(b"\x89PNG")

    # 2. Register Personal Tier 1 account (08012345678) & login via phone number
    u1 = client.post("/api/register", json={
        "full_name": "Esosa Edoleyi",
        "phone": "08012345678",
        "email": "esosa@securemonie.ng",
        "account_type": "Personal",
        "password": "Password1",
        "pin": "1234",
    }).json()
    assert u1["kyc_tier"] == 1

    login_res = client.post("/api/login", json={"identifier": "08012345678", "password": "Password1"})
    assert login_res.status_code == 200
    h1 = {"Authorization": f"Bearer {login_res.json()['token']}"}

    # 3. Top-up N100,000; Tier 1 limit blocks N60,000 transfer until BVN/NIN upgrade to Tier 2
    assert client.post("/api/deposit", headers=h1, json={"amount": 100000, "pin": "1234"}).status_code == 200
    over = client.post("/api/transfer", headers=h1, json={"recipient_account": "0123456789", "bank_name": "GTBank", "amount": 60000, "pin": "1234"})
    assert over.status_code == 400

    up = client.post("/api/settings", headers=h1, json={"setting": "kyc", "new_value": "12345678901", "password": "Password1"})
    assert up.status_code == 200

    # 4. Now N60,000 interbank transfer to GTBank + Airtime purchase + PDF statement succeed
    ok = client.post("/api/transfer", headers=h1, json={"recipient_account": "0123456789", "bank_name": "GTBank", "amount": 60000, "pin": "1234"})
    assert ok.status_code == 200
    assert client.post("/api/bills", headers=h1, json={"service": "MTN Airtime", "target": "08012345678", "amount": 2000, "pin": "1234"}).status_code == 200
    assert client.get("/api/statement/pdf", headers=h1).content.startswith(b"%PDF")

    if os.path.exists(test_db):
        os.remove(test_db)
