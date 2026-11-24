import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.core.database import Base, engine
from backend.seed import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    seed_database()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_fhir_r4_referral_bundle_export(client):
    auth_res = client.post("/api/login", json={"role": "phc"})
    token = auth_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch any existing referral
    refs = client.get("/api/referrals", headers=headers).json()
    assert len(refs) > 0
    ref_id = refs[0]["id"]

    # Export as FHIR R4 Bundle
    fhir_res = client.get(f"/api/interop/fhir/referral/{ref_id}", headers=headers)
    assert fhir_res.status_code == 200
    bundle = fhir_res.json()

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert len(bundle["entry"]) >= 4

    resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Patient" in resource_types
    assert "Organization" in resource_types
    assert "ServiceRequest" in resource_types
    assert "Encounter" in resource_types

def test_abdm_sandbox_status(client):
    auth_res = client.post("/api/login", json={"role": "admin"})
    headers = {"Authorization": f"Bearer {auth_res.json()['token']}"}

    abdm_res = client.get("/api/interop/abdm/status", headers=headers)
    assert abdm_res.status_code == 200
    data = abdm_res.json()
    assert data["status"] == "SANDBOX_READY"
    assert data["fhir_version"] == "R4"

def test_ap_facility_directory(client):
    auth_res = client.post("/api/login", json={"role": "phc"})
    headers = {"Authorization": f"Bearer {auth_res.json()['token']}"}

    fac_res = client.get("/api/interop/facilities/directory?district=NTR", headers=headers)
    assert fac_res.status_code == 200
    facs = fac_res.json()
    assert len(facs) > 0
    assert any("Vijayawada" in f["name"] for f in facs)
