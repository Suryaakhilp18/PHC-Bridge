from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.models.referral import Referral

class FHIRAdapter:
    """
    Translates PHC Bridge referral and lifecycle records into HL7 FHIR R4 compliant resources,
    strictly aligned with Ayushman Bharat Digital Mission (ABDM) and National Digital Health blueprints.
    """

    @classmethod
    def generate_referral_bundle(cls, referral: Referral) -> Dict[str, Any]:
        patient_resource = cls.to_fhir_patient(referral.patient)
        referring_org = cls.to_fhir_organization(referral.referring_facility)
        receiving_org = cls.to_fhir_organization(referral.receiving_facility)
        practitioner = cls.to_fhir_practitioner(referral.referring_doctor)
        service_request = cls.to_fhir_service_request(referral)
        encounter = cls.to_fhir_encounter(referral)
        
        entries = [
            {"fullUrl": f"urn:uuid:{patient_resource['id']}", "resource": patient_resource},
            {"fullUrl": f"urn:uuid:{referring_org['id']}", "resource": referring_org},
            {"fullUrl": f"urn:uuid:{receiving_org['id']}", "resource": receiving_org},
            {"fullUrl": f"urn:uuid:{practitioner['id']}", "resource": practitioner},
            {"fullUrl": f"urn:uuid:{service_request['id']}", "resource": service_request},
            {"fullUrl": f"urn:uuid:{encounter['id']}", "resource": encounter}
        ]

        if referral.follow_up_tasks:
            for task in referral.follow_up_tasks:
                task_resource = cls.to_fhir_task(task)
                entries.append({"fullUrl": f"urn:uuid:{task_resource['id']}", "resource": task_resource})

        return {
            "resourceType": "Bundle",
            "id": f"bundle-referral-{referral.id}",
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
                "profile": [
                    "https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"
                ]
            },
            "identifier": {
                "system": "https://health.telangana.gov.in/phcbridge/bundle",
                "value": f"BUNDLE-{referral.id}"
            },
            "type": "document",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": entries
        }

    @staticmethod
    def to_fhir_patient(patient) -> Dict[str, Any]:
        if not patient:
            return {"resourceType": "Patient", "id": "unknown-patient"}
        return {
            "resourceType": "Patient",
            "id": patient.id,
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient"]
            },
            "identifier": [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical record number"
                            }
                        ]
                    },
                    "system": "https://health.ap.gov.in/patient-code",
                    "value": patient.patient_code
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": patient.full_name
                }
            ],
            "gender": patient.sex.lower() if patient.sex.lower() in ("male", "female", "other") else "unknown",
            "telecom": [
                {"system": "phone", "value": patient.phone or "", "use": "mobile"}
            ] if patient.phone else [],
            "address": [
                {"text": patient.address or "", "state": "Andhra Pradesh", "country": "IN"}
            ] if patient.address else []
        }

    @staticmethod
    def to_fhir_organization(facility) -> Dict[str, Any]:
        if not facility:
            return {"resourceType": "Organization", "id": "unknown-org"}
        return {
            "resourceType": "Organization",
            "id": facility.id,
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Organization"]
            },
            "identifier": [
                {
                    "system": "https://facility.abdm.gov.in/hfr-id",
                    "value": facility.hfr_id or f"IN28-{facility.name[:4].upper()}"
                }
            ],
            "name": facility.name,
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                            "code": "prov",
                            "display": facility.facility_type
                        }
                    ]
                }
            ],
            "telecom": [
                {"system": "phone", "value": facility.phone or "", "use": "work"}
            ] if facility.phone else [],
            "address": [
                {"city": facility.mandal or "", "district": facility.district, "state": facility.state, "country": "IN"}
            ]
        }

    @staticmethod
    def to_fhir_practitioner(doctor) -> Dict[str, Any]:
        if not doctor:
            return {"resourceType": "Practitioner", "id": "unknown-practitioner"}
        return {
            "resourceType": "Practitioner",
            "id": doctor.id,
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Practitioner"]
            },
            "identifier": [
                {
                    "system": "https://doctor.abdm.gov.in/hpr-id",
                    "value": f"HPR-{doctor.username.upper()}"
                }
            ],
            "name": [
                {"text": doctor.full_name}
            ]
        }

    @staticmethod
    def to_fhir_service_request(referral: Referral) -> Dict[str, Any]:
        priority_map = {
            "Emergency": "stat",
            "Urgent": "urgent",
            "Routine": "routine"
        }
        status_map = {
            "Referred": "active",
            "Acknowledged": "active",
            "In Consultation": "active",
            "Completed": "completed",
            "Back-Referred": "completed",
            "Cancelled": "revoked"
        }
        return {
            "resourceType": "ServiceRequest",
            "id": f"sr-{referral.id}",
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/ServiceRequest"]
            },
            "identifier": [
                {
                    "system": "https://health.ap.gov.in/phcbridge/referral-id",
                    "value": referral.id
                }
            ],
            "status": status_map.get(referral.status, "active"),
            "intent": "order",
            "priority": priority_map.get(referral.priority, "routine"),
            "subject": {"reference": f"urn:uuid:{referral.patient_id}"},
            "requester": {"reference": f"urn:uuid:{referral.referring_doctor_id}"},
            "performer": [{"reference": f"urn:uuid:{referral.receiving_facility_id}"}],
            "reasonCode": [
                {
                    "text": referral.reason
                }
            ],
            "authoredOn": referral.created_at.isoformat()
        }

    @staticmethod
    def to_fhir_encounter(referral: Referral) -> Dict[str, Any]:
        return {
            "resourceType": "Encounter",
            "id": f"enc-{referral.id}",
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Encounter"]
            },
            "status": "finished" if referral.status in ("Completed", "Back-Referred") else "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            },
            "subject": {"reference": f"urn:uuid:{referral.patient_id}"},
            "serviceProvider": {"reference": f"urn:uuid:{referral.referring_facility_id}"},
            "period": {
                "start": referral.created_at.isoformat()
            }
        }

    @staticmethod
    def to_fhir_task(task) -> Dict[str, Any]:
        return {
            "resourceType": "Task",
            "id": f"task-{task.id}",
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Task"]
            },
            "status": "completed" if task.status == "Completed" else "requested",
            "intent": "order",
            "for": {"reference": f"urn:uuid:{task.patient_id}"},
            "executionPeriod": {
                "end": task.due_date.isoformat() if task.due_date else None
            },
            "description": task.notes or "Follow-up review at primary healthcare level"
        }
