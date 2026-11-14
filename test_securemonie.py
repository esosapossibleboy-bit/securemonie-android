import os
from fastapi.testclient import TestClient
import mobile_server

client = TestClient(mobile_server.app)

def test_securemonie_full_bank_security_and_features(monkeypatch):
    test_db = "temp_securemonie.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    monkeypatch.setattr(mobile_server, "DB_PATH", test_db)

    sample_selfie = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRof"

    # 1. Register Business Level 3 account with BVN, NIN, Address & Live Selfie
    u1 = client.post("/api/register", json={
        "full_name": "Esosa Edoleyi",
        "phone": "08012345447",
        "email": "esosa@securemonie.ng",
        "account_type": "Business",
        "business_name": "Esosa Global Ventures",
        "business_category": "POS & Agency Banking",
        "address": "12 Admiralty Way, Lekki, Lagos",
        "bvn": "12345678901",
        "nin": "98765432109",
        "id_type": "NIN Slip",
        "pep_status": "No",
        "revenue_source": "Business / Trading Sales",
        "password": "246810",
        "pin": "1234",
        "selfie_data": sample_selfie,
    }).json()
    assert u1["kyc_tier"] == 3

    # 2. Sign in & fund wallet with N100,000
    login_res = client.post("/api/login", json={"identifier": "08012345447", "password": "246810"}).json()
    h1 = {"Authorization": f"Bearer {login_res['token']}"}
    assert client.post("/api/deposit", headers=h1, json={"amount": 100000, "pin": "1234"}).status_code == 200

    # 3. Test Per-Transaction Transfer Cap (set cap to N20,000 -> N30,000 blocked -> N15,000 allowed)
    assert client.post("/api/settings", headers=h1, json={"setting": "single_limit", "new_value": "20000", "password": "246810"}).status_code == 200
    assert client.post("/api/transfer", headers=h1, json={"recipient_account": "0123456789", "bank_name": "GTBank", "amount": 30000, "pin": "1234"}).status_code == 400
    assert client.post("/api/transfer", headers=h1, json={"recipient_account": "0123456789", "bank_name": "GTBank", "amount": 15000, "pin": "1234"}).status_code == 200

    # 4. Test Emergency Panic Freeze (blocks outgoing transfer until unfrozen)
    assert client.post("/api/settings", headers=h1, json={"setting": "freeze", "new_value": "toggle", "password": "246810"}).status_code == 200
    assert client.post("/api/transfer", headers=h1, json={"recipient_account": "0123456789", "bank_name": "GTBank", "amount": 5000, "pin": "1234"}).status_code == 400
    assert client.post("/api/settings", headers=h1, json={"setting": "freeze", "new_value": "toggle", "password": "246810"}).status_code == 200

    # 5. Verify Security Activity Log recorded events & Sign Out All Devices revokes token
    dash = client.get("/api/wallet", headers=h1).json()
    assert len(dash["security_logs"]) >= 4
    assert client.post("/api/logout-all", headers=h1).status_code == 200
    assert client.get("/api/wallet", headers=h1).status_code == 401

    if os.path.exists(test_db):
        os.remove(test_db)
