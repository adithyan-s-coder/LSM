# Last-Safe-Moment Engine

**Don't just predict failure. Find the last safe moment to act.**

A software-only predictive-maintenance decision-support platform. It doesn't just
flag that a machine is deteriorating — it estimates the last safe, economically
reasonable window in which to intervene, and explains why.

---

## 1. Problem

Traditional monitoring tells an engineer *"something is wrong."* Predictive
maintenance can go further: *"this machine may fail soon."* But maintenance teams
still need the harder answer: **"when should I actually act?"**

Act too early and you waste money and uptime. Act too late and you risk failure,
expensive repair, and production loss. This project estimates that middle window.

## 2. Solution

```
Machine Data → Anomaly Detection → Deterioration Analysis → Health Score
   → Critical-Time / RUL Estimation → Last-Safe-Moment Engine
   → Cost & Risk Analysis → Recommendation → Dashboard
```

The centerpiece is the **Last-Safe-Moment Engine**: it takes the raw estimated
critical-condition time and pulls it *earlier*, based on uncertainty, risk level,
and how long the maintenance itself takes — then explains the reasoning in plain
language, never as a bare "AI says maintenance required."

## 3. Features

- Live dashboard: health, risk, critical time, last-safe-moment window, cost of
  waiting, and a plain-language "why now" explanation
- Per-asset detail pages with sensor trend charts, failure/maintenance history
- CSV sensor-data upload with validation
- Simulation engine (Healthy / Temporary Anomaly / Gradual Deterioration /
  Rapid Deterioration / Near Failure) that generates real synthetic readings and
  re-runs the full analysis pipeline
- Anomaly detection (Isolation Forest, fit per-machine on its own history)
- Explainable health scoring, deterioration-rate (slope) analysis, RUL estimation
- Risk engine, cost engine, recommendation engine
- Maintenance scheduling/tracking, alerts, fleet-wide analytics

## 4. Technology Stack

- **Frontend:** HTML5, CSS3, vanilla JavaScript, Chart.js, Font Awesome
- **Backend:** Python 3, FastAPI, Pydantic, Uvicorn
- **Database:** MySQL (via SQLAlchemy + PyMySQL)
- **ML/analysis:** pandas, NumPy, scikit-learn (Isolation Forest), NumPy polyfit
  for trend/slope analysis

No React/Vue/Angular/TypeScript/Tailwind/Bootstrap, no PostgreSQL/MongoDB, no
IoT hardware. This is intentional per the project's scope: software-only, plain
frontend stack, MySQL only.

## 5. Architecture

```
last-safe-moment-engine/
├── backend/
│   ├── main.py                 FastAPI app entrypoint
│   ├── database.py             SQLAlchemy engine/session (MySQL via DATABASE_URL)
│   ├── models.py                ORM models mirroring database/schema.sql
│   ├── schemas.py               Pydantic request/response schemas
│   ├── auth_utils.py            bcrypt hashing + JWT session tokens
│   ├── analysis_pipeline.py     Wires the ML engines together end-to-end
│   ├── seed.py                  Demo data + user seeding script
│   ├── routers/                 One router per API area (see §9)
│   └── ml/
│       ├── anomaly_detection.py       Isolation Forest
│       ├── deterioration_analysis.py  Slope/trend analysis
│       ├── health_score.py            0–100 explainable health score
│       ├── rul_estimator.py           Critical-time / RUL projection
│       ├── last_safe_moment_engine.py Core last-safe-moment calculation
│       ├── risk_engine.py             LOW/MEDIUM/HIGH/CRITICAL
│       ├── cost_engine.py             Act now / wait / failure cost estimate
│       └── recommendation_engine.py   Plain-language reasons + action
├── frontend/                    Plain HTML/CSS/JS pages (12 pages, see §8)
├── database/schema.sql          MySQL schema (10 tables, FKs)
├── sample_data/                 Example CSVs for the Data Upload page
├── requirements.txt
└── .env.example
```

## 6. Installation

### Prerequisites
- Python 3.10+
- MySQL 8.0+ server running locally (or reachable via `DATABASE_URL`)

### Steps

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example backend/.env  # then edit DATABASE_URL / SECRET_KEY
# or simply export them in your shell:
export DATABASE_URL="mysql+pymysql://root:yourpassword@localhost/last_safe_moment"
export SECRET_KEY="a-long-random-string"

# 4. Create the MySQL database + schema
mysql -u root -p < database/schema.sql

# 5. Seed demo data (5 machines, ~100h of history each, demo login)
cd backend
python seed.py

# 6. Run the app
uvicorn main:app --reload
```

The API is now at `http://localhost:8000` and the frontend (served by the same
process) is at `http://localhost:8000/login.html`.

**Demo login:** `admin@example.com` / `admin123`

## 7. API Reference (selected)

| Method | Path                              | Purpose                          |
|--------|------------------------------------|-----------------------------------|
| POST   | `/api/auth/login`                  | Authenticate, returns a session token |
| GET    | `/api/dashboard`                   | Fleet summary + priority-asset full analysis |
| GET    | `/api/assets`                      | List all assets with latest prediction |
| GET    | `/api/assets/{id}/analysis`        | Full pipeline output for one asset |
| GET    | `/api/assets/{id}/readings`        | Recent sensor readings |
| POST   | `/api/data/upload`                 | Upload a sensor-reading CSV |
| POST   | `/api/simulation/run`              | Generate synthetic readings for a scenario, re-run analysis |
| GET    | `/api/predictions`                 | Latest prediction per asset |
| GET    | `/api/intervention-windows`        | All active last-safe-moment windows, sorted by urgency |
| GET/POST | `/api/maintenance`               | List / schedule maintenance |
| GET    | `/api/alerts`                      | Alerts feed |
| GET    | `/api/analytics`                   | Fleet-wide aggregates for charts |

Interactive docs: `http://localhost:8000/docs` (Swagger UI, auto-generated by FastAPI).

## 8. Frontend Pages

`login`, `dashboard`, `assets`, `asset-detail`, `data` (upload),
`predictions`, `intervention-windows`, `maintenance`, `alerts`, `analytics`,
`simulation`, `settings` — all plain HTML/CSS/JS, sharing `js/api.js` for all
backend calls and `js/auth.js` for the session-guarded app shell (sidebar/topbar).

## 9. ML Approach — and its honesty limits

Every engine here is intentionally simple and explainable, per the project's
core requirement: **no black-box claims, no guaranteed predictions.**

- **Anomaly detection:** scikit-learn `IsolationForest`, fit fresh on each
  machine's own recent history (needs ≥10 readings; otherwise reports "normal"
  rather than guessing).
- **Deterioration analysis:** ordinary-least-squares slope of each sensor and
  of the health score, in units/hour — a transparent, inspectable number.
- **Health score:** weighted blend of how far each sensor sits outside its
  normal band, plus a trend penalty. 0–100, with Excellent/Good/Warning/Poor/
  Critical bands.
- **Critical time / RUL:** linear projection of the current health slope
  against a configurable critical-health threshold — always returned with an
  uncertainty range and a confidence percentage, never as a single hard number.
- **Last-Safe-Moment Engine:** deliberately pulls the recommended window
  *earlier* than the raw critical-time estimate, to account for the time the
  maintenance itself takes and a risk/uncertainty-scaled safety margin — and
  logs why in plain language.
- **Cost/Risk engines:** simple rule-based combinations of the above, with
  cost figures clearly framed as **demonstration estimates**, not real invoices.

All predictions surfaced in the UI are labeled as estimates ("Estimated
critical condition," "Confidence 84%," etc.) — never as guarantees.

## 10. Simulation

The Simulation page is the best way to see the whole pipeline move in real
time: pick a machine and a scenario (Healthy / Temporary Anomaly / Gradual
Deterioration / Rapid Deterioration / Near Failure), choose a duration and
severity, and run it. The backend generates real synthetic sensor readings
with drift/noise appropriate to that scenario, stores them, and re-runs the
*entire* analysis pipeline — so health, risk, and the intervention window
genuinely change based on the new data, not a hardcoded label swap.

## 11. Demo Credentials

```
Email:    admin@example.com
Password: admin123
```
These are clearly demo-only credentials, seeded by `seed.py`. Do not reuse
them, or this authentication scheme, in a real deployment.

## 12. Limitations

- Authentication is intentionally simple (bcrypt + a single-secret signed
  session token) — appropriate for an MVP/demo, not hardened for production
  (no refresh tokens, rate limiting, or MFA).
- Per-machine threshold and cost-model editing (`asset_thresholds`,
  `cost_models` tables) exists in the schema and is used by the pipeline, but
  the Settings page UI does not yet wire per-machine edits back to the API —
  it's a demo form. The values it shows are illustrative defaults.
- Health scoring and RUL estimation use simple, transparent statistical
  models by design (per the project's honesty requirement) rather than deep
  learning — they are appropriate for an explainable MVP, not validated
  against real industrial failure data.
- All cost figures (₹5,000 routine maintenance, ₹2.8L emergency repair, etc.)
  are configurable demonstration defaults, not sourced from any real
  maintenance contract.
- Single-tenant demo: there is no multi-organization data isolation.

## 13. Future Improvements

- Per-machine threshold/cost editing wired fully into Settings
- Real-time streaming ingestion (would reintroduce the IoT layer this MVP
  deliberately excludes)
- More advanced RUL models (e.g. survival analysis, gradient-boosted
  regressors) with proper backtesting against historical failures
- Role-based access control and audit logging
- Automated maintenance-window scheduling that accounts for shift/crew
  availability

---

*All predictions, costs, and risk levels shown in this application are
estimates based on available demo data and configured assumptions. They are
not guarantees of machine behavior, failure timing, or financial outcomes.*
