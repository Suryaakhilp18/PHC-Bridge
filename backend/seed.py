import uuid
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal, engine, Base
from backend.core.security import hash_password
from backend.models.facility import Facility
from backend.models.user import User
from backend.models.patient import Patient
from backend.models.referral import Referral, ReferralEvent, ConsultationOutcome, BackReferral
from backend.models.followup import FollowUpTask
from backend.models.notification import Notification
from backend.models.audit import AuditEvent

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded with AP data
        ap_fac = db.query(Facility).filter(Facility.state == "Andhra Pradesh").first()
        if ap_fac:
            return

        print("Seeding Andhra Pradesh Public Healthcare Reference Network...")
        
        # 1. Authoritative AP Healthcare Hierarchy across NTR, Guntur, and Visakhapatnam Districts
        facilities = [
            # NTR District (Vijayawada)
            Facility(name="Vijayawada Government General Hospital", facility_type="Teaching Hospital", district="NTR", mandal="Vijayawada Urban", state="Andhra Pradesh", hfr_id="IN28001001", phone="0866-2571234"),
            Facility(name="Patamata Primary Health Centre", facility_type="PHC", district="NTR", mandal="Vijayawada East", state="Andhra Pradesh", hfr_id="IN28001002", phone="0866-2485601"),
            Facility(name="Ibrahimpatnam Community Health Centre", facility_type="CHC", district="NTR", mandal="Ibrahimpatnam", state="Andhra Pradesh", hfr_id="IN28001003", phone="0866-2812300"),
            Facility(name="Kondapalli Ayushman Arogya Mandir", facility_type="Sub-Centre / AAM", district="NTR", mandal="Ibrahimpatnam", state="Andhra Pradesh", hfr_id="IN28001004", phone="0866-2812301"),
            
            # Guntur District
            Facility(name="Guntur District Hospital", facility_type="District Hospital", district="Guntur", mandal="Guntur Urban", state="Andhra Pradesh", hfr_id="IN28002001", phone="0863-2234567"),
            Facility(name="Mangalagiri Area Hospital", facility_type="Area Hospital", district="Guntur", mandal="Mangalagiri", state="Andhra Pradesh", hfr_id="IN28002002", phone="0863-2345678"),
            Facility(name="Tenali Community Health Centre", facility_type="CHC", district="Guntur", mandal="Tenali", state="Andhra Pradesh", hfr_id="IN28002003", phone="08644-223400"),
            Facility(name="Kothuru Primary Health Centre", facility_type="PHC", district="Guntur", mandal="Kothuru", state="Andhra Pradesh", hfr_id="IN28002004", phone="0863-2456700"),

            # Visakhapatnam District
            Facility(name="King George Hospital (KGH)", facility_type="Teaching Hospital", district="Visakhapatnam", mandal="Visakhapatnam Urban", state="Andhra Pradesh", hfr_id="IN28003001", phone="0891-2564891"),
            Facility(name="Bheemunipatnam Area Hospital", facility_type="Area Hospital", district="Visakhapatnam", mandal="Bheemili", state="Andhra Pradesh", hfr_id="IN28003002", phone="08933-224500"),
        ]
        db.add_all(facilities)
        db.commit()

        # Query back saved facilities
        ggh = db.query(Facility).filter(Facility.hfr_id == "IN28001001").first()
        phc_patamata = db.query(Facility).filter(Facility.hfr_id == "IN28001002").first()
        chc_ibrahimpatnam = db.query(Facility).filter(Facility.hfr_id == "IN28001003").first()
        guntur_dh = db.query(Facility).filter(Facility.hfr_id == "IN28002001").first()
        mangalagiri_ah = db.query(Facility).filter(Facility.hfr_id == "IN28002002").first()

        # 2. Multi-tier Governance Users
        users = [
            User(
                username="state_admin",
                email="director.health@ap.gov.in",
                full_name="Dr. S. Lakshmi, IAS",
                hashed_password=hash_password("demo123"),
                role="state_admin",
                district="Statewide",
                facility_id=ggh.id
            ),
            User(
                username="district_admin",
                email="dho.ntr@ap.gov.in",
                full_name="Dr. K. Venkat Rao",
                hashed_password=hash_password("demo123"),
                role="district_admin",
                district="NTR",
                facility_id=ggh.id
            ),
            User(
                username="phc",
                email="mo.patamata@ap.gov.in",
                full_name="Dr. Meera Rao",
                hashed_password=hash_password("demo123"),
                role="phc",
                district="NTR",
                facility_id=phc_patamata.id
            ),
            User(
                username="hospital",
                email="specialist.ggh@ap.gov.in",
                full_name="Dr. Arjun Kumar",
                hashed_password=hash_password("demo123"),
                role="hospital",
                district="NTR",
                facility_id=ggh.id
            ),
            User(
                username="cho",
                email="cho.kondapalli@ap.gov.in",
                full_name="Sravani",
                hashed_password=hash_password("demo123"),
                role="cho",
                district="NTR",
                facility_id=phc_patamata.id
            ),
            User(
                username="admin",
                email="admin.phcbridge@ap.gov.in",
                full_name="System Administrator",
                hashed_password=hash_password("demo123"),
                role="admin",
                district="Statewide",
                facility_id=ggh.id
            ),
        ]
        db.add_all(users)
        db.commit()

        u_phc = db.query(User).filter(User.username == "phc").first()
        u_hosp = db.query(User).filter(User.username == "hospital").first()
        u_cho = db.query(User).filter(User.username == "cho").first()

        # 3. Synthetic Patient Registry
        patients = [
            Patient(patient_code="AP-SYN-1001", full_name="Ananya Devi", age=34, sex="Female", phone="9876543210", address="H.No 4-12, Patamata, Vijayawada", registered_phc_id=phc_patamata.id),
            Patient(patient_code="AP-SYN-1002", full_name="Ravi Teja", age=52, sex="Male", phone="9876543211", address="Plot 89, Kondapalli Village, Ibrahimpatnam", registered_phc_id=phc_patamata.id),
            Patient(patient_code="AP-SYN-1003", full_name="Fatima Begum", age=27, sex="Female", phone="9876543212", address="Old Guntur Ward 5, Guntur", registered_phc_id=guntur_dh.id),
            Patient(patient_code="AP-SYN-1004", full_name="Rajesh Sharma", age=61, sex="Male", phone="9876543213", address="Main Bazaar, Mangalagiri", registered_phc_id=mangalagiri_ah.id),
            Patient(patient_code="AP-SYN-1005", full_name="Sunitha Reddy", age=44, sex="Female", phone="9876543214", address="Near Bus Stand, Tenali", registered_phc_id=chc_ibrahimpatnam.id),
        ]
        db.add_all(patients)
        db.commit()

        # 4. Referrals with SLA Targets
        now = datetime.now(timezone.utc)
        
        # Referral 1: Urgent - Acknowledged
        r1 = Referral(
            id="AP-2026-00124",
            patient_id=patients[0].id,
            referring_facility_id=phc_patamata.id,
            receiving_facility_id=ggh.id,
            referring_doctor_id=u_phc.id,
            reason="Persistent acute epigastric pain with vomiting and tachycardia. Suspected acute pancreatitis or severe peptic ulceration.",
            priority="Urgent",
            sla_hours=4.0,
            status="Acknowledged",
            created_at=now - timedelta(hours=5),
            acknowledged_at=now - timedelta(hours=3)
        )
        db.add(r1)
        db.commit()

        e1_1 = ReferralEvent(referral_id=r1.id, actor_id=u_phc.id, actor_name=u_phc.full_name, actor_role="phc", action="Referral Created", details=f"Initiated at {phc_patamata.name} directed to {ggh.name}", created_at=now - timedelta(hours=5))
        e1_2 = ReferralEvent(referral_id=r1.id, actor_id=u_hosp.id, actor_name=u_hosp.full_name, actor_role="hospital", action="Hospital Acknowledged", details="Triage desk at Vijayawada GGH scanned optical QR slip and confirmed handoff", created_at=now - timedelta(hours=3))
        db.add_all([e1_1, e1_2])

        # Referral 2: Emergency - Dispatched (Awaiting Triage, SLA Breach Watch)
        r2 = Referral(
            id="AP-2026-00123",
            patient_id=patients[1].id,
            referring_facility_id=phc_patamata.id,
            receiving_facility_id=ggh.id,
            referring_doctor_id=u_phc.id,
            reason="Acute onset left hemiparesis and facial asymmetry. Window period 90 mins. Suspected ischemic stroke. Urgent CT Brain requested.",
            priority="Emergency",
            sla_hours=1.0,
            status="Referred",
            created_at=now - timedelta(minutes=45)
        )
        db.add(r2)
        db.commit()

        e2_1 = ReferralEvent(referral_id=r2.id, actor_id=u_phc.id, actor_name=u_phc.full_name, actor_role="phc", action="Referral Created", details="Emergency fast-track stroke alert dispatched", created_at=now - timedelta(minutes=45))
        db.add(e2_1)

        # Referral 3: Completed with Closed-Loop Back-Referral to PHC
        r3 = Referral(
            id="AP-2026-00122",
            patient_id=patients[2].id,
            referring_facility_id=phc_patamata.id,
            receiving_facility_id=ggh.id,
            referring_doctor_id=u_phc.id,
            reason="High-risk pregnancy (G2P1L1, 28 weeks with gestational hypertension 150/96 mmHg). Specialist obstetric evaluation.",
            priority="Urgent",
            sla_hours=4.0,
            status="Back-Referred",
            created_at=now - timedelta(days=3),
            acknowledged_at=now - timedelta(days=2, hours=20),
            completed_at=now - timedelta(days=2, hours=8)
        )
        db.add(r3)
        db.commit()

        out3 = ConsultationOutcome(
            referral_id=r3.id,
            doctor_id=u_hosp.id,
            doctor_name=u_hosp.full_name,
            outcome_notes="Obstetric ultrasound normal. Fetal Doppler reassuring. Initiated Labetalol 100mg BD. Discharged with strict home BP monitoring.",
            diagnosis_category="Obstetrics & Gynaecology",
            back_referral_recommended=True,
            created_at=now - timedelta(days=2, hours=8)
        )
        br3 = BackReferral(
            referral_id=r3.id,
            origin_hospital_id=ggh.id,
            target_phc_id=phc_patamata.id,
            clinical_summary="Gestational hypertension controlled on Labetalol. Needs weekly antenatal BP & proteinuria check at PHC.",
            follow_up_instructions="Weekly ANC clinic visit at Patamata PHC. Check for headache, blurring of vision, or epigastric discomfort.",
            follow_up_date=date.today() + timedelta(days=4),
            status="Active",
            created_at=now - timedelta(days=2, hours=8)
        )
        fu3 = FollowUpTask(
            referral_id=r3.id,
            patient_id=patients[2].id,
            assigned_to_id=u_cho.id,
            assigned_to_name=u_cho.full_name,
            facility_id=phc_patamata.id,
            due_date=date.today() + timedelta(days=4),
            status="Assigned",
            notes="Weekly antenatal BP tracking and compliance check for Labetalol 100mg."
        )
        db.add_all([out3, br3, fu3])

        # Referral 4: Completed with Overdue Follow-up Task
        r4 = Referral(
            id="AP-2026-00120",
            patient_id=patients[3].id,
            referring_facility_id=mangalagiri_ah.id,
            receiving_facility_id=guntur_dh.id,
            referring_doctor_id=u_phc.id,
            reason="Uncontrolled Type 2 Diabetes Mellitus with HbA1c 10.4% and peripheral neuropathy.",
            priority="Routine",
            sla_hours=24.0,
            status="Completed",
            created_at=now - timedelta(days=16),
            acknowledged_at=now - timedelta(days=15),
            completed_at=now - timedelta(days=14)
        )
        db.add(r4)
        db.commit()

        fu4 = FollowUpTask(
            referral_id=r4.id,
            patient_id=patients[3].id,
            assigned_to_id=u_cho.id,
            assigned_to_name=u_cho.full_name,
            facility_id=mangalagiri_ah.id,
            due_date=date.today() - timedelta(days=2),  # 2 days overdue
            status="Overdue",
            notes="Fasting blood sugar check and foot sensation examination."
        )
        db.add(fu4)

        # 5. In-App Notifications
        n1 = Notification(
            title="Emergency Referral Dispatched",
            message=f"Stroke alert for {patients[1].full_name} referred from Patamata PHC to Vijayawada GGH. 1-hour SLA active.",
            target_role="hospital",
            facility_id=ggh.id,
            notification_type="urgent",
            link_url=f"/referrals/{r2.id}"
        )
        n2 = Notification(
            title="Follow-up Overdue",
            message=f"Patient {patients[3].full_name} has a diabetes review that is 2 days overdue.",
            target_role="cho",
            facility_id=mangalagiri_ah.id,
            notification_type="warning",
            link_url="/follow-ups"
        )
        db.add_all([n1, n2])

        db.add(AuditEvent(actor="AP Health System", role="state_admin", action="Registry Seeded", details="Andhra Pradesh public health institutional topology populated", created_at=now))
        db.commit()
        print("Database seeded with Andhra Pradesh healthcare facilities and synthetic patients.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
