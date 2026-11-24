# PHC Bridge — Offline-First Referral Coordination Prototype

A hackathon-ready web prototype for coordinating patient referrals between Primary Health Centres (PHCs) and district hospitals.

## Included
- Role-based demo access: PHC doctor, hospital doctor, community health officer, administrator
- Patient registration and digital referral creation
- Unique referral IDs and QR-code display
- Hospital acknowledgement and consultation outcome updates
- Back-referral and follow-up task workflow
- Referral timeline / audit events
- Dashboard metrics and search
- Offline referral queue in browser `localStorage`, with a manual sync action
- FastAPI backend with SQLAlchemy; SQLite works out of the box and PostgreSQL is configurable

> **Safety:** This is a demonstration prototype. It uses synthetic patient information only. It does not diagnose, prescribe, or replace clinical decisions. Do not enter real patient data. Authentication, authorization, encryption, audit integrity, clinical governance, and privacy controls require hardening before any real-world deployment.

## Requirements
- Python 3.10+
- Node.js 18+

## 1. Start the backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --reload
```

API: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

The backend defaults to SQLite (`phc_bridge.db`). To use PostgreSQL, set `DATABASE_URL`, for example:

```bash
# PowerShell
$env:DATABASE_URL="postgresql+psycopg://postgres:password@localhost:5432/phc_bridge"

# macOS/Linux
export DATABASE_URL="postgresql+psycopg://postgres:password@localhost:5432/phc_bridge"
```

## 2. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (usually http://localhost:5173).

Set `VITE_API_URL` if the backend is hosted elsewhere. By default the frontend uses `http://localhost:8000`.

## Demo roles
Choose any role on the sign-in screen. The demo does not require a password.

- **PHC Doctor:** create and send referrals
- **Hospital Doctor:** acknowledge referrals, record consultation outcomes, create back-referrals
- **Community Health Officer:** manage follow-up tasks
- **Administrator:** view all workflows and operational metrics

The app seeds a few clearly fictional demo records on first backend startup.

## Offline demonstration
1. Open the app while the backend is available.
2. Use the PHC Doctor role and create a referral.
3. If the API is unavailable, the browser stores the referral locally as `PENDING SYNC`.
4. Restore the backend and click **Sync offline queue** in the sidebar.
5. The app submits queued referrals and refreshes the dashboard.

For a reliable demo, test this flow in a browser with DevTools Network set to Offline.

## Project structure

```text
phc-bridge/
├── backend/
│   ├── app.py
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── styles.css
```

## Before any pilot
Replace demo authentication with a vetted identity provider; add granular permissions, consent and lawful-basis review, encryption in transit/at rest, secure secrets, tamper-evident audit logging, backups, retention policies, accessibility testing, threat modelling, and integration with approved health systems. Validate all workflows with clinicians and administrators.
