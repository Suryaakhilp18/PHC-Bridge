from typing import Dict, Any, List
from datetime import datetime, timezone
from backend.core.config import settings

class ABDMAdapter:
    """
    ABDM (Ayushman Bharat Digital Mission) sandbox adapter interface.
    Prepares bridge HIP (Health Information Provider) and HIU (Health Information User)
    metadata according to official NHA Gateway specifications.
    """

    GATEWAY_SANDBOX_URL = "https://dev.abdm.gov.in/gateway"
    
    @classmethod
    def get_bridge_configuration(cls) -> Dict[str, Any]:
        return {
            "status": "SANDBOX_READY",
            "bridge_id": "AP_PHC_BRIDGE_01",
            "client_id": "SBX_AP_PHC_BRIDGE",
            "gateway_url": cls.GATEWAY_SANDBOX_URL,
            "supported_services": [
                "ABHA_VERIFICATION",
                "HEALTH_FACILITY_REGISTRY_LOOKUP",
                "CONSENT_REQUEST_HIP",
                "DATA_FLOW_HIU"
            ],
            "fhir_version": "R4",
            "hl7_india_profile": "NRCeS NDHM FHIR R4 v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "regulatory_compliance_note": "Awaiting final state sandbox key exchange; offline & local mock gateway active."
        }

    @classmethod
    def build_consent_request_payload(cls, patient_abha_id: str, referral_id: str) -> Dict[str, Any]:
        return {
            "consent": {
                "purpose": {
                    "text": "Continuity of Care and Referral Coordination",
                    "code": "CAREMGT"
                },
                "patient": {
                    "id": patient_abha_id
                },
                "hiu": {
                    "id": "AP_PHC_BRIDGE_HIU"
                },
                "requester": {
                    "name": "Medical Officer, PHC",
                    "identifier": {
                        "type": "REGNO",
                        "value": "AP-DPHFW-REF"
                    }
                },
                "hiTypes": ["DiagnosticReport", "Prescription", "DischargeSummary", "OPConsultation"],
                "permission": {
                    "accessMode": "VIEW",
                    "dateRange": {
                        "from": datetime.now(timezone.utc).isoformat(),
                        "to": datetime.now(timezone.utc).isoformat()
                    },
                    "dataEraseAt": datetime.now(timezone.utc).isoformat(),
                    "frequency": {
                        "unit": "HOUR",
                        "value": 1,
                        "repeats": 0
                    }
                }
            }
        }
