import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.core.database import Base, engine
from backend.seed import seed_database
from backend.services.qr_service import QRService

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    seed_database()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["service"] == "PHC Bridge Platform"

def test_login_flow(client):
    # Test legacy instant role login
    res = client.post("/api/login", json={"role": "phc"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["user"]["role"] == "phc"
    
    # Test formal credentials login
    res2 = client.post("/api/auth/login", json={"username": "phc", "password": "demo123"})
    assert res2.status_code == 200
    assert "access_token" in res2.json()

def test_referrals_and_qr_scanning(client):
    # 1. Login as PHC
    auth_res = client.post("/api/login", json={"role": "phc"})
    token = auth_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List referrals
    ref_list = client.get("/api/referrals", headers=headers)
    assert ref_list.status_code == 200
    assert len(ref_list.json()) > 0
    first_ref = ref_list.json()[0]

    # 3. Create a new referral
    new_ref_payload = {
        "patient_name": "Test Patient",
        "age": 45,
        "sex": "Male",
        "patient_code": "SYN-TEST-99",
        "phone": "9999888877",
        "source_phc": "Lakshmi Nagar PHC",
        "destination": "District General Hospital",
        "reason": "Persistent acute fever and productive cough for 10 days.",
        "priority": "Urgent"
    }
    create_res = client.post("/api/referrals", json=new_ref_payload, headers=headers)
    assert create_res.status_code == 200
    created_ref = create_res.json()
    assert created_ref["status"] == "Referred"
    ref_id = created_ref["id"]

    # 4. QR Verification
    qr_payload = QRService.generate_qr_payload(ref_id)
    verified_id = QRService.verify_qr_payload(qr_payload)
    assert verified_id == ref_id

    # 5. Hospital login and QR scan
    hosp_res = client.post("/api/login", json={"role": "hospital"})
    hosp_headers = {"Authorization": f"Bearer {hosp_res.json()['token']}"}
    
    scan_res = client.post("/api/referrals/scan-qr", json=qr_payload, headers=hosp_headers)
    assert scan_res.status_code == 200
    assert scan_res.json()["id"] == ref_id

    # 6. Acknowledge referral
    ack_res = client.post(f"/api/referrals/{ref_id}/acknowledge", headers=hosp_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "Acknowledged"

    # 7. Record outcome with back-referral
    outcome_payload = {
        "outcome_notes": "Chest X-ray shows lower lobe infiltration. Prescribed oral Azithromycin and Amoxicillin.",
        "diagnosis_category": "Pulmonology",
        "back_referral": True,
        "follow_up_date": "2026-12-05",
        "follow_up_instructions": "Review lung sounds and sputum report at PHC in 10 days."
    }
    out_res = client.post(f"/api/referrals/{ref_id}/outcome", json=outcome_payload, headers=hosp_headers)
    assert out_res.status_code == 200
    assert out_res.json()["status"] == "Back-Referred"
    assert out_res.json()["back_referral"] is True

def test_ai_modules(client):
    auth_res = client.post("/api/login", json={"role": "phc"})
    headers = {"Authorization": f"Bearer {auth_res.json()['token']}"}

    # Quality check
    qc = client.post("/api/ai/quality-check", json={
        "reason": "Chest pain with severe shortness of breath radiating to left arm",
        "priority": "Routine",
        "destination": "District General Hospital",
        "age": 58,
        "sex": "Male"
    }, headers=headers)
    assert qc.status_code == 200
    assert len(qc.json()["recommendations"]) > 0

    # Operations Query
    op = client.post("/api/ai/operations-query", json={
        "query": "How many referrals are awaiting hospital acknowledgement?"
    }, headers=headers)
    assert op.status_code == 200
    assert "awaiting" in op.json()["answer"].lower()

    # Translation
    tr = client.post("/api/ai/translate", json={
        "text": "Review at PHC as advised by the hospital team.",
        "target_language": "telugu"
    }, headers=headers)
    assert tr.status_code == 200
    assert tr.json()["target_language"] == "Telugu"
    assert len(tr.json()["translated_text"]) > 0

def test_offline_sync(client):
    import uuid
    auth_res = client.post("/api/login", json={"role": "phc"})
    headers = {"Authorization": f"Bearer {auth_res.json()['token']}"}

    test_off_id = f"PHC-2026-OFF-{uuid.uuid4().hex[:6].upper()}"
    items = [
        {
            "id": test_off_id,
            "patient_name": "Offline Patient 1",
            "age": 29,
            "sex": "Female",
            "patient_code": f"SYN-OFF-{uuid.uuid4().hex[:4].upper()}",
            "reason": "Routine antenatal checkup required.",
            "priority": "Routine",
            "destination": "District General Hospital"
        }
    ]
    sync_res = client.post("/api/sync", json=items, headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["synced"] >= 1
