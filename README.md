# MedFlow
### AI-Assisted Neonatal Hospital Referral and Transfer Coordination Platform

<p align="center">
  <strong>Connecting hospitals. Coordinating neonatal referrals. Simplifying healthcare access.</strong>
</p>

---

## 1. Project Overview

**MedFlow** is an AI-assisted neonatal hospital referral coordination platform designed to connect referring hospitals with suitable receiving hospitals.

The system helps hospital staff retrieve newborn records, identify required neonatal care facilities, find eligible receiving hospitals, coordinate referral acceptance, and securely share medical information after authorisation.

MedFlow combines artificial intelligence, hospital capability matching, geographical distance calculations, operational prediction and automated referral coordination.

**Target demonstration location:** Bengaluru, Karnataka, India.

**Project type:** Healthcare technology capstone prototype.

**Primary objective:** Simplify neonatal hospital referral coordination through a centralised and explainable digital platform.

### The problem

When a hospital needs to transfer a newborn for advanced neonatal care, staff may need to:

- Contact multiple hospitals.
- Check neonatal bed availability.
- Verify equipment and specialist availability.
- Share patient information repeatedly.
- Wait for receiving hospital confirmation.
- Track referral and transfer status manually.

These activities can create coordination difficulties and delays.

### The proposed solution

MedFlow provides a unified platform where referring hospitals can submit a referral, identify eligible hospitals, send transfer requests, receive acceptance or rejection responses, and manage authorised medical-record access.

---

## 2. Project Objectives

1. Simplify hospital-to-hospital neonatal referrals.
2. Provide a centralised newborn record retrieval mechanism.
3. Extract possible care requirements from medical notes using AI.
4. Identify hospitals that satisfy mandatory care requirements.
5. Rank eligible hospitals using geographical and operational criteria.
6. Predict hospital response delays using machine learning.
7. Automate referral offer tracking and sequential escalation.
8. Restrict complete medical-record access to authorised receiving hospitals.
9. Maintain transfer history and audit records.
10. Provide a simple and professional hospital coordination interface.

---

## 3. Core Features

| Feature | Description |
|---|---|
| Hospital authentication | Secure login for referring and receiving hospitals |
| Baby registry | Retrieve synthetic newborn records using unique baby codes |
| AI requirement extraction | Extract possible neonatal care requirements from clinical notes |
| Clinician review | Allow authorised staff to verify and confirm extracted requirements |
| Hospital matching | Identify hospitals satisfying mandatory requirements |
| Geographical matching | Calculate approximate distance between hospitals |
| Hospital ranking | Rank eligible hospitals using weighted scoring |
| ML response prediction | Predict the probability of a delayed hospital response |
| Referral management | Create and track referral requests |
| Sequential escalation | Send the next offer after rejection or expiry |
| Bed reservation | Reserve simulated capacity upon authorised acceptance |
| Secure report sharing | Grant controlled medical-record access |
| Transfer management | Track referral and transfer lifecycle |
| Audit logging | Record important user actions and sensitive information access |

---

## 4. Application Workflow

```text
             HOSPITAL LOGIN
                    |
                    v
          REFERRING HOSPITAL
                    |
                    v
           ENTER BABY CODE
                    |
                    v
        RETRIEVE BABY RECORD
                    |
                    v
          GEMINI AI EXTRACTION
                    |
                    v
          CLINICIAN REVIEW
                    |
                    v
       CONFIRM CARE REQUIREMENTS
                    |
                    v
        HOSPITAL MATCHING ENGINE
                    |
                    v
       HARD ELIGIBILITY FILTERING
                    |
                    v
        GEOGRAPHICAL DISTANCE
                    |
                    v
       WEIGHTED HOSPITAL RANKING
                    |
                    v
      OPERATIONAL RESPONSE PREDICTION
                    |
                    v
        SEND MINIMAL REFERRAL
                    |
                    v
       RECEIVING HOSPITAL DASHBOARD
                    |
              +-----+-----+
              |           |
              v           v
           DECLINE      ACCEPT
              |           |
              v           v
       NEXT HOSPITAL   BED RESERVATION
              |           |
              v           v
        NEXT OFFER    TRANSFER RECORD
              |           |
              |           v
              |     AUTHORISED REPORT
              |          ACCESS
              |           |
              |           v
              |      TRANSFER CLOSURE
              |           |
              |           v
              |     ACCESS REVOCATION
              |
              v
        NO MATCH / MANUAL
        COORDINATION REQUIRED
```

---

## 5. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React | Hospital user interface |
| Frontend tooling | Vite | Development and build tooling |
| Backend | Node.js | Application runtime |
| API framework | Express.js | REST API development |
| Database | Supabase PostgreSQL | Persistent application data |
| Authentication | Supabase Auth or existing secure auth implementation | User authentication |
| Database security | PostgreSQL RLS | Database-level access control |
| AI | Google Gemini API | Structured requirement extraction |
| ML | Python | Model training and evaluation |
| ML library | scikit-learn | Logistic Regression |
| Data processing | pandas, NumPy | Dataset processing |
| Model inference | Node.js JSON model scorer | Operational predictions |
| File storage | Supabase Storage | Private synthetic report storage |
| Geographical calculation | Haversine formula | Approximate distance calculation |
| Future geospatial support | PostGIS | Spatial database queries |

The application follows a modular monolithic architecture to keep development straightforward while separating the major application responsibilities.

---

## 6. System Architecture

```text
                    MEDFLOW FRONTEND
                          |
                          v
                   NODE.JS EXPRESS
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
     AUTH SERVICE    REFERRAL SERVICE   MATCHING SERVICE
          |               |               |
          |               v               v
          |          OFFER SERVICE    RANKING ENGINE
          |               |               |
          |               v               v
          |        TRANSFER SERVICE    DISTANCE SERVICE
          |               |
          +---------------+
                          |
                          v
                    SUPABASE CLOUD
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
      POSTGRESQL       PRIVATE FILES    AUDIT LOGS
          |
          +-------------------------------+
          |                               |
          v                               v
      GEMINI API                     ML SERVICE
   REQUIREMENT EXTRACTION        RESPONSE DELAY MODEL
```

### Architectural principles

- Keep hospital matching independent of the AI provider.
- Keep the ML model independent of clinical requirement extraction.
- Store application records in PostgreSQL.
- Use database transactions for critical referral acceptance operations.
- Apply access control on the backend and database.
- Keep medical reports in private storage.
- Make hospital capabilities configurable rather than hardcoded.

---

## 7. AI Component — Gemini API

### Purpose

Gemini analyses fictional neonatal medical notes and extracts possible care requirements into structured data.

### Example input

A synthetic newborn clinical summary may describe:

- Prematurity.
- Respiratory support.
- Current oxygen support.
- Birth weight.
- Current observations.
- Clinical notes.

### Example output

```json
{
  "required_nicu_level": "LEVEL_III",
  "required_equipment": [
    "INCUBATOR",
    "CPAP",
    "PULSE_OXIMETER",
    "INFUSION_PUMP"
  ],
  "required_specialists": [
    "NEONATOLOGIST",
    "RESPIRATORY_THERAPIST"
  ],
  "suggested_priority": "HIGH",
  "needs_clinician_review": true,
  "missing_information": []
}
```

This output is illustrative and not a clinical recommendation.

### AI workflow

1. Retrieve the synthetic newborn record.
2. Send the appropriate raw medical notes to Gemini.
3. Receive structured extraction.
4. Validate the returned JSON against the backend schema.
5. Identify missing or invalid fields.
6. Display the output for authorised clinician review.
7. Save the approved requirements.
8. Pass only approved requirements to the matching engine.

### Important AI restrictions

Gemini must not:

- Diagnose a newborn.
- Prescribe medication.
- Determine treatment.
- Independently determine clinical urgency.
- Decide whether a newborn should be transferred.
- Accept or reject a hospital referral.
- Release medical reports.

AI output must be treated as a draft requiring authorised review.

### Provider abstraction

Keep the AI integration replaceable:

```text
AIRequirementProvider
        |
        +---- GeminiProvider
        |
        +---- Future OllamaProvider
```

This allows a future transition to Ollama and Qwen without rewriting the referral workflow.

---

## 8. Hospital Matching Algorithms

MedFlow uses multiple algorithms because different parts of the application solve different problems.

### 8.1 Rule-Based Hard Eligibility Filtering

This is the primary hospital matching algorithm.

The system excludes hospitals that:

- Are inactive.
- Are the referring hospital.
- Do not satisfy the required NICU level.
- Do not have mandatory equipment.
- Do not have the required specialists.
- Do not have an available suitable bed.

Example:

```javascript
function isEligible(hospital, requirements) {
  return (
    hospital.isActive &&
    hospital.availableBeds > 0 &&
    hospital.nicuLevel >= requirements.nicuLevel &&
    requirements.equipment.every(
      item => hospital.availableEquipment.includes(item)
    ) &&
    requirements.specialists.every(
      item => hospital.availableSpecialists.includes(item)
    )
  );
}
```

This is a simplified example. The actual implementation must account for capability definitions, availability periods and the hospital's current operational capacity.

A hospital must satisfy every mandatory requirement before it can be ranked.

### 8.2 Haversine Distance Formula

The Haversine formula calculates approximate straight-line geographical distance between two locations using latitude and longitude.

\[
a=\sin^2(\Delta\phi/2)+
\cos(\phi_1)\cos(\phi_2)\sin^2(\Delta\lambda/2)
\]

\[
d=2R\arcsin(\sqrt a)
\]

Where:

- \(R\) is the Earth's approximate radius.
- \(\phi\) represents latitude.
- \(\lambda\) represents longitude.
- \(d\) is the calculated distance.

The result is geographical distance, not actual road travel time.

### 8.3 Weighted Sum Model

After filtering, rank eligible hospitals using a configurable weighted scoring model.

A starting model may use:

\[
S=w_1D+w_2O+w_3C+w_4R
\]

Where:

- \(D\): normalised distance score.
- \(O\): operational readiness.
- \(C\): preferred capability fit.
- \(R\): response reliability.
- \(w_1,w_2,w_3,w_4\): configurable weights that sum to 1.

All scores must be normalised to the same scale.

Mandatory requirements must remain hard filters and must not be compensated for by a higher ranking score.

The scoring weights are demonstration assumptions and require future operational validation.

### 8.4 Why A* Is Not the Primary Algorithm

A* is a pathfinding algorithm.

It can be useful for finding a route through a road-network graph, but it does not decide whether a hospital has the appropriate NICU, equipment, specialists or available beds.

Therefore, A* is not required for the first prototype.

A road-routing provider or road-network algorithm can be integrated later.

---

## 9. Machine Learning — Hospital Response Delay Prediction

### Objective

Predict whether an eligible receiving hospital may take more than 15 minutes to respond to a referral offer.

This is an operational prediction, not a clinical prediction.

### Model

Logistic Regression using Python and scikit-learn.

### Dataset

Input file:

`neobridge_referral_offer_delay_dataset.csv`

### Target

`slow_response_15m`

| Target | Meaning |
|---|---|
| 0 | Response within 15 minutes |
| 1 | Response takes more than 15 minutes |

### Candidate input features

```text
night
weekend
government
unit_median_min
completeness
emergency
services_count
open_load
```

These features must represent information available when the referral offer is created.

### Excluded features

Never use outcome-derived fields such as:

```text
offer_id
referral_id
responded_at
response_minutes
offer_status
slow_response_15m
```

Baby names and baby identifiers must never be model input features.

### Censored records

Offers without an observed response must not automatically be classified as fast or slow.

The initial binary classification model should use records with observed response outcomes only.

Survival analysis can be considered in a future version if modelling censored response times becomes necessary.

### Example model output

```json
{
  "slow_response_probability": 0.23,
  "prediction": "LOW_DELAY_RISK",
  "model_version": "1.0"
}
```

This is an illustrative output, not a real performance claim.

### Model integration

1. Process the training CSV.
2. Validate the dataset.
3. Remove leakage features.
4. Handle censored records.
5. Split data using referral groups.
6. Train Logistic Regression.
7. Evaluate the model.
8. Export the model artifact.
9. Integrate prediction into Node.js.
10. Use the result as an optional ranking input.

If the model is unavailable, the application must continue with a clearly documented fallback.

Synthetic training results must not be presented as real hospital performance.

---

## 10. Synthetic Newborn Dataset

MedFlow uses 30 fictional newborn records for demonstration and testing.

All patient information is synthetic.

### Main demonstration baby

| Field | Value |
|---|---|
| Baby name | Aarav Kumar |
| Baby code | 10482 |
| Date of birth | 25 August 2026 |
| Age on 31 October 2026 | 67 days |
| Birth weight | 1250 grams |
| Gestational age | 30 weeks |
| Source hospital | HOSP001 |

### Required NICU level

`LEVEL_III`

### Required equipment

```text
INCUBATOR
CPAP
PULSE_OXIMETER
INFUSION_PUMP
```

### Required specialists

```text
NEONATOLOGIST
RESPIRATORY_THERAPIST
```

### Expected priority

`HIGH`

This profile is a predefined synthetic testing reference, not an independent clinical assessment.

### Condition distribution

| Condition category | Number of babies |
|---|---:|
| Prematurity and respiratory support | 8 |
| Neonatal jaundice monitoring | 5 |
| Low birth weight | 5 |
| Infection evaluation and monitoring | 4 |
| Temperature regulation | 4 |
| General neonatal observation | 4 |
| **Total** | **30** |

### Approved equipment identifiers

```text
INCUBATOR
CPAP
VENTILATOR
PHOTOTHERAPY_UNIT
RADIANT_WARMER
INFUSION_PUMP
PULSE_OXIMETER
SUCTION_DEVICE
```

### Approved specialist identifiers

```text
NEONATOLOGIST
PEDIATRICIAN
RESPIRATORY_THERAPIST
PEDIATRIC_SURGEON
```

### NICU levels

```text
LEVEL_I
LEVEL_II
LEVEL_III
LEVEL_IV
```

### Priority values

```text
LOW
MEDIUM
HIGH
URGENT
```

All expected requirements must be stored separately from the raw medical records.

---

## 11. Bengaluru Demonstration Hospital Network

The demonstration network may include publicly identifiable Bengaluru hospitals:

1. Bangalore Baptist Hospital.
2. Chinmaya Mission Hospital.
3. Kempegowda Institute of Medical Sciences (KIMS), V.V. Puram.
4. Rainbow Children's Hospital, Electronic City.
5. Manipal Hospitals, Hebbal.
6. Aster CMI Hospital.
7. St. Martha's Hospital.

### Demonstration hospital mapping

| Hospital code | Demonstration hospital |
|---|---|
| HOSP001 | Fictional MedFlow Demo Referral Centre |
| HOSP002 | Rainbow Children's Hospital, Electronic City |
| HOSP003 | Chinmaya Mission Hospital |
| HOSP004 | KIMS Bengaluru |
| Additional codes | Other demonstration hospitals |

### Data separation

**Publicly documented information:**

- Hospital name.
- Public address.
- Published service descriptions.
- Public source URLs.

**Synthetic demonstration information:**

- Simulated bed capacity.
- Current simulated available beds.
- Equipment availability.
- Specialist availability.
- Operational readiness.
- Historical response information.

All simulated hospital data must carry the following label:

`SIMULATED_DEMO_DATA`

The use of a hospital name does not imply partnership, approval or participation in MedFlow.

Public hospital information does not establish real-time bed availability or current staff availability.

---

## 12. Database Design

MedFlow uses Supabase PostgreSQL.

### Main tables

| Table | Responsibility |
|---|---|
| `hospitals` | Hospital identity and location |
| `babies` | Fictional newborn records |
| `hospital_equipment` | Hospital equipment catalogue and availability |
| `hospital_specialists` | Specialist information and availability |
| `transfer_requests` | Main referral record |
| `transfer_attempts` | Individual hospital offers and responses |

### Supporting tables

Where implemented by the database architecture:

- `baby_expected_requirements`
- `hospital_capacity`
- `ai_requirement_extractions`
- `report_access_grants`
- `transfers`
- `audit_logs`

The supporting tables must be integrated with the existing schema rather than creating duplicate versions of core records.

### Important database principles

- Foreign-key relationships.
- Unique identifiers.
- Appropriate indexes.
- Validated status transitions.
- Transactional referral acceptance.
- Transactional bed reservation.
- Hospital-level access control.
- Row Level Security.
- Audit history.

Use PostgreSQL functions for critical multi-record operations that must be atomic.

---

## 13. Two-Stage Medical Information Sharing

MedFlow follows a minimal-disclosure approach.

### Stage 1 — Initial referral request

Before authorised acceptance, the receiving hospital receives only the minimum information required by the approved demonstration contract.

Example:

```json
{
  "baby_code": "10482",
  "baby_name": "Aarav Kumar",
  "date_of_birth": "2026-08-25",
  "age_days": 67,
  "required_nicu_level": "LEVEL_III",
  "required_equipment": [
    "INCUBATOR",
    "CPAP",
    "PULSE_OXIMETER",
    "INFUSION_PUMP"
  ],
  "required_specialists": [
    "NEONATOLOGIST",
    "RESPIRATORY_THERAPIST"
  ],
  "priority": "HIGH",
  "source_hospital_code": "HOSP001"
}
```

Do not include full medical history, detailed clinical notes, complete reports or scans in this initial request.

### Stage 2 — After authorised acceptance

The authorised receiving hospital can retrieve the permitted full synthetic record through the backend.

Potential information includes:

- Full newborn record.
- Medical history.
- Clinical notes.
- Birth information.
- Current care details.
- Synthetic report references.
- Transfer documentation.

All retrieval must be authenticated, authorised and logged.

A production system should minimise direct identifiers in initial requests wherever practical.

---

## 14. Main Demonstration Scenario

The central demonstration uses baby 10482.

### Step 1 — Source hospital

HOSP001 creates a referral for Aarav Kumar.

### Step 2 — Hospital matching

The matching engine identifies eligible hospitals.

### Step 3 — First receiving hospital

HOSP002 initially qualifies.

It receives the minimal transfer request.

### Step 4 — HOSP002 declines

Before acceptance, the available simulated NICU bed becomes unavailable.

HOSP002 declines because:

`NICU bed unavailable at confirmation time`

### Step 5 — Next receiving hospital

HOSP003 receives the next referral offer.

### Step 6 — HOSP003 accepts

An authorised hospital user accepts the offer.

The system then:

- Rechecks capacity.
- Reserves the simulated bed.
- Creates the transfer record.
- Updates the referral status.
- Notifies the referring hospital.
- Grants authorised report access.

### Step 7 — Transfer closure

When the transfer lifecycle is closed:

- Temporary report access is revoked according to policy.
- The closure is audited.
- Bed availability is not automatically restored.

An authorised hospital user must separately confirm when a bed becomes available.

---

## 15. Referral Status Management

Example offer statuses:

```text
PENDING
ACCEPTED
REJECTED
EXPIRED
CANCELLED
```

Example transfer statuses:

```text
ACCEPTED
CONFIRMED
PREPARING
IN_TRANSIT
COMPLETED
CANCELLED
```

The application must prevent invalid transitions.

Only an authorised receiving hospital may accept its own offer.

A referral must not be accepted by multiple hospitals.

Use database transactions and appropriate constraints to prevent concurrent acceptance.

If all eligible hospitals reject or expire, display a clear manual-coordination-required status.

---

## 16. Security and Privacy

Security is a fundamental part of MedFlow.

### Authentication

- Secure hospital login.
- Password hashing or managed authentication.
- Session validation.
- Rate limiting.
- Secure logout.

### Authorisation

Roles:

```text
REFERRER
RECEIVER
ADMIN
```

A receiving hospital must access only permitted records and offers associated with its hospital.

### Medical reports

- Store reports in private storage.
- Do not expose permanent public report URLs.
- Stream reports through an authorised backend endpoint.
- Check hospital and transfer permissions before retrieval.
- Record report-access events.

### Database

- Enable Row Level Security.
- Enforce authorisation in backend APIs and database policies.
- Keep administrative credentials on the server.
- Protect sensitive environment variables.

### Important

This project uses fictional patient records for demonstration.

Real healthcare deployment would require appropriate authorisation, patient privacy safeguards, legal review, healthcare institution agreements, clinical governance and independent security testing.

---

## 17. Project Structure

The following is the intended logical project organisation. Adjust directory names to match the actual repository.

```text
medflow/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── assets/
│   └── package.json
│
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── middleware/
│   │   ├── providers/
│   │   ├── database/
│   │   └── server.js
│   └── package.json
│
├── ml/
│   ├── generate_dataset.py
│   ├── train_model.py
│   ├── requirements.txt
│   └── response_delay_model.json
│
├── data/
│   ├── baby_dataset.json
│   ├── expected_requirements.json
│   ├── bengaluru_hospitals.json
│   ├── hospital_sources.json
│   └── condition_distribution.json
│
├── supabase/
│   ├── migrations/
│   └── tests/
│
├── tests/
│
├── .env.example
├── .gitignore
├── MEDFLOW_ARCHITECTURE.md
├── MEDFLOW_PROJECT_STATE.md
└── README.md
```

---

## 18. Prerequisites

Install the required development tools:

- Node.js LTS.
- npm.
- Git.
- Python 3.
- Supabase account.
- Supabase CLI.
- Google AI Studio API key for Gemini integration.

Optional:

- PostgreSQL local installation for database testing.
- VS Code or another code editor.

Check installed versions:

```bash
node --version
npm --version
python --version
git --version
```

The installed versions should satisfy the dependencies declared by the actual project.

---

## 19. Supabase Cloud Setup

MedFlow uses Supabase Cloud as the primary application database.

### Step 1 — Create a project

Open:

https://supabase.com/dashboard

Create a project named:

`MedFlow`

Save the database password securely.

### Step 2 — Get the project details

From the Supabase dashboard, obtain:

- Project URL.
- Publishable API key.
- Secret key for backend-only operations, if required by the implementation.
- Database connection details for trusted migration tools where needed.

Never expose a secret key or database password in frontend code.

### Step 3 — Inspect the database

Open the SQL Editor or use the Supabase CLI to inspect the existing public schema.

Verify whether the core tables already exist before creating new ones.

### Step 4 — Link the repository

From the project directory:

```bash
npx supabase login
npx supabase link --project-ref YOUR_PROJECT_REF
```

Use your actual project reference.

### Step 5 — Preview migrations

```bash
npx supabase db push --dry-run
```

Review the migrations before applying them.

### Step 6 — Apply migrations

```bash
npx supabase db push
```

Only apply after verifying the target project and confirming that the migrations will not destroy existing data.

### Step 7 — Insert synthetic data

Run the project's generated seed SQL using the configured seed mechanism or Supabase SQL Editor after reviewing the script.

Do not run destructive database reset commands against the live project.

### Step 8 — Verify the database

Check:

- Main tables.
- Supporting tables.
- Relationships.
- 30 baby records.
- Hospital records.
- Equipment and specialists.
- Expected requirements.
- RLS configuration.
- Migration history.

A local PostgreSQL test does not establish that the live Supabase deployment succeeded.

---

## 20. Environment Configuration

Create a `.env` file using the actual environment variable names supported by the application.

Example template:

```env
# Application
NODE_ENV=development
PORT=5000

# Supabase
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co

# Frontend-safe publishable key
VITE_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY

# Backend-only secret
SUPABASE_SECRET_KEY=YOUR_SERVER_ONLY_SECRET_KEY

# Gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=YOUR_SUPPORTED_MODEL_NAME

# Optional database connection for trusted tooling
DATABASE_URL=YOUR_POSTGRES_CONNECTION_STRING
```

Important:

- Replace placeholders with actual configuration.
- Match variable names with the implemented code.
- Never commit `.env`.
- Never place secret credentials in `VITE_` variables.
- Keep the Supabase secret key and database connection string on the server or in trusted deployment secrets.

The `.env.example` file must contain placeholder values only.

---

## 21. Installation and Running

Use the actual project package structure and scripts.

### Frontend

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

Start the development server using the configured script:

```bash
npm run dev
```

### Backend

Open another terminal:

```bash
cd backend
npm install
```

Start the backend:

```bash
npm run dev
```

The exact paths and scripts must match the actual repository's `package.json` files.

### ML dependencies

```bash
cd ml

python -m venv .venv
```

Activate the environment.

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Train the response-delay model using the training command defined by the project.

Do not assume a trained model exists until the training script has executed successfully.

---

## 22. Machine Learning Training

The initial response-delay training dataset is:

`neobridge_referral_offer_delay_dataset.csv`

Before training:

1. Validate the input CSV.
2. Check missing values.
3. Identify censored offers.
4. Confirm target distribution.
5. Remove identifiers and leakage fields.
6. Verify that all features were available at offer creation time.
7. Group observations by referral during validation.

The primary target is:

`slow_response_15m`

Use Logistic Regression.

Evaluate using:

- Accuracy.
- Precision.
- Recall.
- F1 score.
- ROC-AUC where meaningful.
- Confusion matrix.
- Baseline comparison.

Document the dataset version, training configuration, split strategy and model metrics.

The initial model is for a synthetic demonstration only.

---

## 23. Testing

Test each major system component independently and then validate the complete referral journey.

### Database

- Schema migration.
- Foreign keys.
- Unique constraints.
- Seed repeatability.
- Invalid data rejection.
- Transaction correctness.

### Authentication

- Valid login.
- Invalid login.
- Logout.
- Role restrictions.
- Cross-hospital access denial.

### Newborn registry

- Baby code 10482 retrieval.
- Unknown baby code.
- Record integrity.
- Correct age calculations.

### AI extraction

- Valid structured response.
- Invalid response.
- Missing information.
- API failure.
- Manual clinician review.

### Matching

- Insufficient NICU level.
- Missing equipment.
- Missing specialists.
- No available beds.
- Source hospital exclusion.
- Distance calculation.
- Weighted ranking.

### Referral workflow

- Offer creation.
- Rejection.
- Expiry.
- Sequential escalation.
- Acceptance.
- Duplicate acceptance prevention.
- Bed reservation.

### Secure report access

- Authorised access.
- Unauthorised access rejection.
- Expired access.
- Revoked access.
- Audit event creation.

### Complete demonstration

Execute:

```text
HOSP001
   |
   v
Baby 10482
   |
   v
AI extraction
   |
   v
Clinician review
   |
   v
Hospital matching
   |
   v
HOSP002 receives request
   |
   v
HOSP002 declines
   |
   v
HOSP003 receives request
   |
   v
HOSP003 accepts
   |
   v
Bed reservation
   |
   v
Secure report access
   |
   v
Transfer management
```

Do not claim a test passed unless it was actually executed.

---

## 24. Development Roadmap

MedFlow is developed in ten controlled steps.

| Step | Responsibility | Expected outcome |
|---|---|---|
| 1 | Project audit and architecture | Project foundation documented |
| 2 | Supabase and synthetic datasets | Database and sample data ready |
| 3 | Authentication and roles | Secure hospital login |
| 4 | Baby records and Gemini | Record retrieval and AI extraction |
| 5 | Hospital matching | Eligibility and ranking engine |
| 6 | Referral workflow | Offer, accept, decline and escalation |
| 7 | Secure reports and transfers | Controlled medical-record access |
| 8 | Frontend and UI/UX | Complete hospital interface |
| 9 | Logistic Regression | Response-delay prediction |
| 10 | Testing and delivery | Complete demonstration prototype |

Each step must be tested and documented before beginning the next step.

---

## 25. Current Project Status

**Development status:** Prototype development.

Maintain the actual step completion status in:

- `MEDFLOW_PROJECT_STATE.md`
- `MEDFLOW_IMPLEMENTATION_LOG.md`

Do not mark a feature complete simply because its source file exists.

A completed feature must be integrated and tested.

Keep separate records of:

- Implemented functionality.
- Locally tested functionality.
- Supabase Cloud deployed functionality.
- Functionality awaiting integration.
- Future production requirements.

---

## 26. Known Limitations

The initial prototype has important limitations.

### Synthetic records

All newborn records are fictional and intended for software testing.

### Hospital availability

Bed availability, equipment readiness, staff availability and operational response information are simulated.

The application does not provide real-time hospital capacity information.

### Hospital participation

The inclusion of public hospital names does not imply a partnership, agreement or participation in MedFlow.

### AI limitations

Gemini output is not a clinical decision.

All extracted requirements must be appropriately reviewed.

### ML limitations

Logistic Regression is trained and evaluated using operational demonstration data.

Its output must not be presented as a reliable real-world hospital performance prediction.

### Government integration

No live government health-record integration is currently established.

A future integration requires authorised API access and an appropriate legal and technical framework.

### Ambulance tracking

The prototype's transfer statuses are coordination states and do not represent real-time ambulance tracking.

---

## 27. Future Enhancements

Potential future capabilities include:

- Authorised health-record integrations.
- Real hospital onboarding.
- Live NICU capacity updates.
- Hospital staff scheduling integration.
- Real-time operational notifications.
- Road travel-time estimation.
- Ambulance service integration.
- Advanced geographical matching through PostGIS.
- Survival analysis for censored response data.
- Larger operational datasets.
- Model monitoring and retraining.
- Institution-level reporting and analytics.

These are future enhancements, not claims about existing functionality.

---

## 28. Demo Credentials

Document the actual seeded demonstration accounts here once they are created and tested.

| Username | Role | Hospital |
|---|---|---|
| referrer.demo | REFERRER | HOSP001 |
| rainbow.receiver | RECEIVER | HOSP002 |
| chinmaya.receiver | RECEIVER | HOSP003 |
| admin.demo | ADMIN | Demo administration |

Demo passwords must be generated and stored securely.

Never publish real deployment credentials in this README.

---

## 29. Safety and Responsible Use

MedFlow is an educational healthcare coordination prototype.

It is not a clinically validated medical system.

It must not be used to diagnose newborns, prescribe treatment, determine clinical urgency, decide transport fitness or independently select a receiving hospital for real patient care.

The final decision remains with appropriately authorised healthcare professionals.

Before real-world deployment, the system would require:

- Appropriate institutional agreements.
- Authorised healthcare-record integration.
- Patient privacy and legal review.
- Security assessment.
- Clinical governance.
- Operational validation.
- Independent testing.

All demonstration records and hospital availability information must remain clearly identified as synthetic.

---

## 30. Project Mission

MedFlow aims to demonstrate how AI-assisted information extraction, explainable hospital matching, operational prediction and secure digital coordination can support a more organised neonatal referral process.

**One platform. Connected hospitals. Explainable matching. Controlled information sharing.**

---

<p align="center">
  <strong>MedFlow — Making neonatal referral coordination simpler.</strong>
</p>
