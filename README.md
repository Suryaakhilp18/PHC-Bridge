# PHC Bridge 2.0 — AI-Powered Offline-First Care Coordination Platform

An enterprise healthcare coordination platform connecting Primary Health Centres (PHCs), District Hospitals, Community Health Officers (CHOs), and Health Administrators across the complete patient referral lifecycle.

---

## 🌟 Key Capabilities in PHC Bridge 2.0

- **Complete Care Coordination Lifecycle:**
  `Patient Registration` ➔ `Digital Referral Creation` ➔ `Tamper-Proof QR Generation` ➔ `Hospital Triage Scan` ➔ `Acknowledgment` ➔ `Specialist Outcome` ➔ `Back-Referral Established` ➔ `CHO Follow-up Closure`.
- **Offline-First PWA with IndexedDB Sync:**
  Clinicians in remote or bandwidth-constrained health sub-centres can draft and create referrals completely offline. Queued records are stored in browser IndexedDB with automatic background synchronization upon network reconnection.
- **AI Intelligence Engine:**
  - **AI Referral Quality Assistant:** Pre-submission analysis flagging missing clinical context, urgency level mismatches, and suggesting clear administrative wording.
  - **AI Patient Journey Summarizer:** Synthesizes verified timeline facts vs administrative narratives for returning patients.
  - **AI Healthcare Operations Assistant:** Conversational query engine for administrators backed by real SQL database aggregates.
  - **Multilingual Communication Aid:** Instant translation of administrative follow-up instructions into Telugu (తెలుగు) and Hindi (हिंदी).
- **Security & Role-Based Access Control (RBAC):**
  - PBKDF2-HMAC-SHA256 password security.
  - JWT tokens with 24-hour expiration and server-side invalidation.
  - Scoped role permissions (`phc`, `hospital`, `cho`, `admin`).
  - Tamper-proof HMAC-signed QR identification codes (zero unencrypted patient health information embedded in QR).
- **Printable Referral Slip & QR Slip:**
  Export and print official 80mm / A4 referral slips with scannable QR tokens for patients traveling between facilities.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+

### 2. Start the Backend API Server
```bash
# Navigate to backend directory
cd backend

# (Optional) Activate your virtual environment
# Windows: ..\.venv\Scripts\activate
# Linux/macOS: source ../.venv/bin/activate

# Start Uvicorn server with hot-reload
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

### 3. Start the Frontend Development Server
Open a second terminal window:
```bash
# Navigate to frontend directory
cd frontend

# Start Vite dev server
npm run dev
```
- Open your browser at `http://localhost:5173`

---

## 👥 Authorized Demonstration Roles

Choose any role on the sign-in screen (or log in with username and password `demo123`):

| Role | Demo User | Facility | Responsibilities |
| :--- | :--- | :--- | :--- |
| **PHC Doctor** | Dr. Meera Rao (`phc`) | Lakshmi Nagar PHC | Register patients, create referrals with AI quality review, print slips |
| **Hospital Doctor** | Dr. Arjun Kumar (`hospital`) | District General Hospital | Scan referral QR code, acknowledge handoff, record consultation outcome, trigger back-referral |
| **CHO** | Sravani (`cho`) | Lakshmi Nagar PHC | View follow-up tasks, conduct home visits, update adherence notes, mark follow-ups complete |
| **Administrator** | System Administrator (`admin`) | District Health Office | Network analytics, facility workloads, system audit log, CSV export, AI Operations Assistant |

---

## 🧪 Running the Automated Test Suite

PHC Bridge 2.0 comes with full automated unit and end-to-end integration tests:

```bash
# From the project root
python -m pytest tests/ -v
```

All 6 test suites cover:
1. `test_health_check` — Service health & API discovery
2. `test_login_flow` — JWT token generation & credentials verification
3. `test_referrals_and_qr_scanning` — Referral creation, QR signing & camera scan verification
4. `test_ai_modules` — AI Quality Review, Journey Summarizer, Operations Assistant, and Translation
5. `test_offline_sync` — IndexedDB bulk offline synchronization with duplicate protection
6. `test_complete_end_to_end_referral_journey` — Complete end-to-end multi-role lifecycle test

---

## 📶 Testing Offline Mode

1. Open the application at `http://localhost:5173`.
2. Sign in as **PHC Doctor**.
3. Open browser DevTools (`F12`), switch to the **Network** tab, and toggle the dropdown from *No throttling* to **Offline**.
4. Click **Create Referral**, enter synthetic patient information, and click **Dispatch Referral**.
5. Observe the notification: *"Saved locally in IndexedDB. Will sync automatically when connectivity returns."*
6. In DevTools, toggle Network back to **Online** (or click the **Sync Offline Queue** button in the sidebar).
7. The referral is uploaded to the central server, assigned a unique ID, and seeded into the hospital receiving queue.

---

## 🛡️ Safety & Clinical Disclaimer

**Synthetic Demo Environment:** PHC Bridge uses synthetic patient information only. It does not diagnose, prescribe, or replace clinical decision-making. Before any real-world pilot, integrate with approved health information networks (e.g. ABDM), enforce mutual TLS, encrypted storage at rest, and clinical governance audits.
