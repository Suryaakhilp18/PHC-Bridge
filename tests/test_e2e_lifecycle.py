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

def test_complete_end_to_end_referral_journey(client):
    # STEP 1: PHC Doctor signs in
    phc_auth = client.post("/api/auth/login", json={"username": "phc", "password": "demo123"})
    assert phc_auth.status_code == 200
    phc_token = phc_auth.json()["access_token"]
    phc_headers = {"Authorization": f"Bearer {phc_token}"}

    # STEP 2: PHC Doctor registers patient and creates digital referral
    ref_payload = {
        "patient_name": "Laxmi Narayana",
        "age": 48,
        "sex": "Male",
        "patient_code": "SYN-E2E-100",
        "phone": "9876500001",
        "source_phc": "Lakshmi Nagar PHC",
        "destination": "District General Hospital",
        "reason": "Persistent retrosternal chest discomfort on exertion with normal resting ECG.",
        "priority": "Urgent"
    }
    create_res = client.post("/api/referrals", json=ref_payload, headers=phc_headers)
    assert create_res.status_code == 200
    created_ref = create_res.json()
    ref_id = created_ref["id"]
    assert created_ref["status"] == "Referred"

    # STEP 3: Verify tamper-proof QR code generation
    qr_payload = QRService.generate_qr_payload(ref_id)
    assert qr_payload["ref"] == ref_id
    assert "sig" in qr_payload

    # STEP 4: Hospital Doctor signs in
    hosp_auth = client.post("/api/auth/login", json={"username": "hospital", "password": "demo123"})
    assert hosp_auth.status_code == 200
    hosp_token = hosp_auth.json()["access_token"]
    hosp_headers = {"Authorization": f"Bearer {hosp_token}"}

    # STEP 5: Hospital scans QR code at emergency triage desk
    scan_res = client.post("/api/referrals/scan-qr", json=qr_payload, headers=hosp_headers)
    assert scan_res.status_code == 200
    assert scan_res.json()["id"] == ref_id

    # STEP 6: Hospital acknowledges receipt
    ack_res = client.post(f"/api/referrals/{ref_id}/acknowledge", headers=hosp_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "Acknowledged"

    # STEP 7: Hospital records specialist consultation outcome & establishes Back-Referral
    outcome_payload = {
        "outcome_notes": "Treadmill stress test positive for inducible ischemia. Initiated Aspirin 75mg and Atorvastatin 20mg. Advised elective angiography.",
        "diagnosis_category": "Cardiology",
        "back_referral": True,
        "follow_up_date": "2026-12-10",
        "follow_up_instructions": "Review blood pressure, lipid profile, and medication compliance at PHC in 14 days."
    }
    outcome_res = client.post(f"/api/referrals/{ref_id}/outcome", json=outcome_payload, headers=hosp_headers)
    assert outcome_res.status_code == 200
    assert outcome_res.json()["status"] == "Back-Referred"
    assert outcome_res.json()["back_referral"] is True

    # STEP 8: Community Health Officer (CHO) signs in and reviews follow-up tasks
    cho_auth = client.post("/api/auth/login", json={"username": "cho", "password": "demo123"})
    assert cho_auth.status_code == 200
    cho_token = cho_auth.json()["access_token"]
    cho_headers = {"Authorization": f"Bearer {cho_token}"}

    followups_res = client.get("/api/followups", headers=cho_headers)
    assert followups_res.status_code == 200
    cho_tasks = followups_res.json()
    matching_tasks = [t for t in cho_tasks if t["referral_id"] == ref_id]
    assert len(matching_tasks) > 0
    task_id = matching_tasks[0]["id"]

    # STEP 9: CHO marks follow-up completed
    complete_res = client.patch(f"/api/followups/{task_id}", json={
        "status": "Completed",
        "completion_notes": "Home visit conducted. Patient compliant with Aspirin and Atorvastatin. BP 124/82 mmHg."
    }, headers=cho_headers)
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "Completed"

    # STEP 10: Health Administrator logs in and verifies complete audit trail & metrics
    admin_auth = client.post("/api/auth/login", json={"username": "admin", "password": "demo123"})
    assert admin_auth.status_code == 200
    admin_token = admin_auth.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    timeline_res = client.get(f"/api/referrals/{ref_id}/timeline", headers=admin_headers)
    assert timeline_res.status_code == 200
    events = [e["action"] for e in timeline_res.json()]
    assert "Referral Created" in events
    assert "Hospital Acknowledged" in events
    assert "Consultation Outcome Recorded" in events
    assert "Follow-up Updated" in events

    # STEP 11: AI Operations Assistant test
    ops_res = client.post("/api/ai/operations-query", json={
        "query": "How many back-referrals were established across the care network?"
    }, headers=admin_headers)
    assert ops_res.status_code == 200
    assert "back-referral" in ops_res.json()["answer"].lower()
