import os
from fastapi.testclient import TestClient
import mobile_server

client = TestClient(mobile_server.app)

def test_securemonie_business_kyc_selfie_and_cards(monkeypatch):
    test_db = "temp_securemonie.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    monkeypatch.setattr(mobile_server, "DB_PATH", test_db)

    sample_selfie = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRof"

    # 1. Register Business Tier 3 account with BVN, NIN, Address, and Live Selfie
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
    assert u1["selfie_data"] == sample_selfie

    # 2. Quick-unlock login returns selfie_data & phone
    login_res = client.post("/api/login", json={"identifier": "08012345447", "password": "246810"}).json()
    assert login_res["selfie_data"] == sample_selfie
    h1 = {"Authorization": f"Bearer {login_res['token']}"}

    # 3. Verify wallet dashboard includes business name, selfie, and Tier 3 limit
    dash = client.get("/api/wallet", headers=h1).json()
    assert dash["business_name"] == "Esosa Global Ventures"
    assert dash["selfie_data"] == sample_selfie
    assert dash["daily_limit_ngn"] == 5_000_000.0

    # 4. Top up, transfer to GTBank, and issue a USD Virtual Card
    assert client.post("/api/deposit", headers=h1, json={"amount": 250000, "pin": "1234"}).status_code == 200
    assert client.post("/api/transfer", headers=h1, json={"recipient_account": "0123456789", "bank_name": "GTBank", "amount": 150000, "pin": "1234"}).status_code == 200
    card = client.post("/api/cards", headers=h1, json={"currency": "USD"}).json()
    assert client.post(f"/api/cards/{card['id']}/fund", headers=h1, json={"amount": 16000, "pin": "1234"}).status_code == 200

    if os.path.exists(test_db):
        os.remove(test_db)
