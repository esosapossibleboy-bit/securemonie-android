import os
from fastapi.testclient import TestClient
import mobile_server

client = TestClient(mobile_server.app)

def test_securemonie_6digit_passcode_and_cards(monkeypatch):
    test_db = "temp_securemonie.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    monkeypatch.setattr(mobile_server, "DB_PATH", test_db)

    # 1. Register Personal Tier 1 account with 6-digit login passcode (246810) & 4-digit PIN (1234)
    u1 = client.post("/api/register", json={
        "full_name": "Esosa Edoleyi",
        "phone": "08012345447",
        "email": "esosa@securemonie.ng",
        "account_type": "Personal",
        "password": "246810",
        "pin": "1234",
    }).json()
    assert u1["kyc_tier"] == 1
    assert u1["phone"] == "08012345447"

    # 2. Quick-unlock login using phone + 6-digit passcode
    login_res = client.post("/api/login", json={"identifier": "08012345447", "password": "246810"})
    assert login_res.status_code == 200
    h1 = {"Authorization": f"Bearer {login_res.json()['token']}"}

    # 3. Top up N100,000, upgrade KYC Tier 2, send N60,000 to GTBank, and issue/fund a USD Virtual Card
    assert client.post("/api/deposit", headers=h1, json={"amount": 100000, "pin": "1234"}).status_code == 200
    assert client.post("/api/settings", headers=h1, json={"setting": "kyc", "new_value": "12345678901", "password": "246810"}).status_code == 200
    assert client.post("/api/transfer", headers=h1, json={"recipient_account": "0123456789", "bank_name": "GTBank", "amount": 60000, "pin": "1234"}).status_code == 200

    card = client.post("/api/cards", headers=h1, json={"currency": "USD"}).json()
    assert client.post(f"/api/cards/{card['id']}/fund", headers=h1, json={"amount": 16000, "pin": "1234"}).status_code == 200
    assert client.post(f"/api/cards/{card['id']}/reveal", headers=h1, json={"pin": "1234"}).status_code == 200
    assert client.get("/api/statement/pdf", headers=h1).content.startswith(b"%PDF")

    if os.path.exists(test_db):
        os.remove(test_db)
