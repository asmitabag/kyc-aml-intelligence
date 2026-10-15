# KYC–AML Intelligence

An explainable, graph-aware platform that brings identity verification (KYC), transaction monitoring (AML), alert triage and suspicious activity report (SAR) drafting into one analyst workflow.

> **Status:** academic prototype. It is not certified for production use, and every SAR draft must be reviewed by a qualified analyst. Nothing is filed with any authority.

**Authors:** K. Suhail, Asmita Bag, Sounak Maity, Saloni Simlote
School of Computer Science and Engineering, Vellore Institute of Technology, Chennai

---

## What it does

The platform is built from four modules that share one FastAPI back end and one database.

| Module | What it does | Where |
|---|---|---|
| **1. Browser-side KYC** | Camera wizard that scans an Indian ID (PAN, Aadhaar, passport, driving licence), reads it with OCR, matches the document photo to the live face, checks blink and head-turn liveness cues, and produces a transparent 100-point score. The document image stays in the browser. | `frontend/frontend/src/pages/customer/kyc/` |
| **2. Graph AML** | **AccountGNN** scores each customer from the account–transaction graph (two-layer bidirectional message passing, mean‖max pooling over the customer's accounts). XGBoost scores individual transactions. | `services/model_adapters/`, `services/aml_runtime.py` |
| **3. Explainable triage** | Fuses KYC and AML risk (0.4 / 0.6), assigns priority, uses KYC–AML disagreement as uncertainty to defer cases to analysts, and explains decisions with SHAP / TreeSHAP and integrated-gradients explanation subgraphs. | `services/xai/` |
| **4. SAR drafting** | Retrieves FinCEN guidance (MiniLM + FAISS), drafts a narrative with Gemini 2.5 Flash (or a deterministic template when no API key is set), and runs an evidence validator over the draft. | `services/sar/` |

Model adapters always return an explicit `available`, `unavailable` or `error` status. The API never invents a score when a model file is missing.

## Results at a glance

Results on the synthetic, typology-injected benchmark (3,000 customers, 124,220 transactions, 7 laundering typologies). Values are mean ± s.d. over 5 seeds.

| Model (customer level) | ROC-AUC | PR-AUC | F1 |
|---|---|---|---|
| **AccountGNN** | **0.956 ± 0.022** | **0.843 ± 0.048** | **0.800 ± 0.040** |
| XGBoost + 1-hop neighbour features | 0.910 ± 0.015 | 0.544 ± 0.096 | 0.513 ± 0.090 |
| AccountGNN without message passing | 0.809 ± 0.009 | 0.412 ± 0.079 | 0.401 ± 0.067 |

Triage and explanation results:

- **Calibration:** isotonic calibration lowers the expected calibration error from 0.030 to 0.015.
- **Deferral:** the default rule (τ = 0.2) sends 87% of suspicious customers to an analyst and closes 74% of all cases automatically.
- **Explanations:** edges selected by integrated gradients are 5.7× enriched for true laundering transactions.

These numbers come from synthetic data and are not evidence of real-world performance. The full results are in the accompanying manuscript.

---

## Repository layout

```
apps/api_gateway/        FastAPI app (main.py), database setup, migrations
services/
  aml_runtime.py         AML orchestration: builds the customer graph, calls AccountGNN, creates assessments/alerts
  model_adapters/        AccountGNN model + adapter, XGBoost adapters, risk fusion, runtime contracts
  xai/                   triage, SHAP explainer, uncertainty, calibration (ECE), selective prediction
  sar/                   FinCEN ingestion, embeddings, FAISS retriever, Gemini generator, validator
  cases/                 SQLAlchemy models, service layer, analyst feedback
  auth/                  password hashing, JWT tokens, role checks
  kyc/preprocessing/     MIDV document-mask and tampering-generation scripts
shared/schemas/          Pydantic schemas (KYC, AML, triage, case, SAR)
frontend/frontend/       React + Vite + Tailwind customer and analyst portals
data/                    small synthetic dataset and feature/label scripts
scripts/                 model verification, GNN inspection, demo seeding
tests/                   pytest suite (41 tests)
runtime_validation/      end-to-end runtime checks
third_party/             face-anti-spoofing (MiniFASNet) utilities
```

---

## Getting started

### Prerequisites

- Python 3.10+ (tested on 3.13)
- Node.js 18+ (tested on 22)

### 1. Back end

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install sqlalchemy xgboost shap pyjwt python-dotenv faiss-cpu pypdf "pydantic[email]"
# optional, for LLM drafting and semantic retrieval:
pip install google-genai sentence-transformers
```

`requirements.txt` does not list every package the code imports. The second `pip install` line covers the gaps.

Create a `.env` file in the repository root, or export the variables in your shell:

| Variable | Required | Purpose |
|---|---|---|
| `JWT_SECRET_KEY` | **yes** | At least 32 characters. Login returns HTTP 500 without it. |
| `AML_ACCOUNT_GNN_ENABLED` | no | Set to `true` to load AccountGNN from `artifacts/account_gnn_v1/`. |
| `GEMINI_API_KEY` | no | Enables LLM SAR drafting and explanations. Without it, a template is used. |
| `GEMINI_MODEL` | no | Defaults to `gemini-2.5-flash`. |

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Start the API:

```bash
uvicorn apps.api_gateway.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API docs are at http://127.0.0.1:8000/docs, and the health check is at `GET /api/v1/health`.

### 2. Front end

```bash
cd frontend/frontend
cp .env.example .env               # VITE_API_BASE_URL=http://127.0.0.1:8000
npm install
npm run dev                        # http://localhost:3000
```

The dev server is pinned to port **3000** because that is the origin the back end's CORS allowlist accepts. If you change the port, add the new origin to `allow_origins` in `apps/api_gateway/main.py`.

The KYC camera needs a secure context, so use `localhost`, `127.0.0.1` or HTTPS. The face models are served from `public/models/`.

### 3. Create an analyst account

Self-registration creates **customer** accounts only. To create an analyst, run this once from the repository root:

```python
from apps.api_gateway.database import SessionLocal, Base, engine
from services.cases import models
from services.auth.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
db.add(models.User(email="analyst@example.com", password_hash=hash_password("ChangeMe123"),
                   role="analyst", customer_id=None, is_active=True))
db.commit()
```

Then sign in at http://localhost:3000/analyst/login.

---

## Model artefacts

Trained weights are not committed (`artifacts/` is in `.gitignore`). The adapters look for:

| Model | Path |
|---|---|
| AccountGNN | `artifacts/account_gnn_v1/account_gnn.pt` and `metadata.json` |
| Transaction XGBoost (v2) | `artifacts/aml_xgboost_v2/transaction_xgboost_pipeline.joblib` and `feature_schema.json` |
| Transaction XGBoost (IBM AML) | `artifacts/aml_xgboost/xgboost_aml.joblib` and `feature_schema.json` |
| FinCEN retrieval index | `data/fincen/index/fincen.index` and `metadata.json` |

If an artefact is missing, the API reports that model as `unavailable`, and AML analysis returns an explicit unavailable response rather than a score.

To build the FinCEN index, put the guidance PDFs in `data/fincen/source_documents/` and run:

```bash
python -m services.sar.ingest && python -m services.sar.embeddings && python -m services.sar.vector_store
```

### Known serving issue (fixed in the reproducibility package)

In the original code, `services/aml_runtime.py` built the GNN input from only the customer's own outgoing transactions. AccountGNN's degree features therefore differed from training, and live scores collapsed to about 0.

`serving_fix.patch` in the reproducibility package fixes this. It builds the exact two-hop receptive field and pools only over the customer's own accounts. With the patch applied, live scores match offline scores (Spearman 0.974), and all 41 tests still pass.

---

## Reproducing the paper's experiments

`reproducibility_package.zip` contains the scripts, results and the serving patch. Run the scripts in this order:

```bash
python scripts/gen_benchmark.py 42 data      # synthetic benchmark
python scripts/exp_tx.py data results        # transaction-level models
python scripts/exp_gnn.py data results       # AccountGNN + baselines, 5 seeds (writes artifacts/account_gnn_v1)
python scripts/fix_mlp.py                    # MLP baseline with minority oversampling
python scripts/exp_xai.py                    # KYC simulation, fusion, calibration, deferral, SHAP, SAR validator
python scripts/explain_gnn.py                # integrated-gradients fidelity
python scripts/fig_explain.py                # explanation figure + per-typology recall
python scripts/figures.py                    # remaining figures
```

The scripts contain absolute paths from the original run. Edit the path constants at the top of each file before running.

## Tests

```bash
pytest -q tests                  # 41 tests: schemas, adapters, orchestration, triage, SHAP, SAR, auth, API workflow
pytest -q runtime_validation     # end-to-end runtime checks
```

---

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register`, `/api/v1/auth/login` | Customer registration and login (JWT) |
| POST | `/api/v1/customers/{id}/kyc` | Submit KYC result and signals |
| POST | `/api/v1/customers/{id}/aml-analysis` | Run AccountGNN for a customer; creates an assessment and, above 0.8, an alert |
| POST | `/api/v1/aml/score-transaction` | Score one transaction with XGBoost |
| GET/PATCH | `/api/v1/alerts`, `/api/v1/alerts/{id}` | Alert queue and status updates |
| POST | `/api/v1/alerts/{id}/feedback` | Record an analyst decision |
| GET/POST | `/cases`, `/cases/{id}/sar` | Cases and SAR generation (analyst only) |
| POST/PATCH | `/api/v1/sar-drafts`, `/api/v1/sar-drafts/{id}/status` | Save and review SAR drafts |

The full route list is in `endpoints.txt`, or at `/docs` while the server is running.

---

## Limitations

- AML results come from a **synthetic** benchmark. Performance on real bank data has not been measured.
- The KYC score is computed **in the browser**. The server should recompute it from validated signals before trusting it.
- The face-distance thresholds (0.38 / 0.55 / 0.65) have not been calibrated on a biometric test set. Blink and head-turn cues do not stop replay or deepfake attacks.
- The tamper and deepfake fields sent by the camera flow are heuristic proxies, not detector outputs. The SegFormer tamper model and the MiniFASNet anti-spoofing check were separate experiments and are not wired into this code.
- The SAR validator checks structured fields only. Unsupported amounts or counterparties in free text are **not** detected.
- With the serving patch, a single API analysis currently takes a few seconds, because the two-hop receptive field is large.
- The client sends a document fingerprint that is an unsalted SHA-256 hash of the document type and ID number. Use a server-side HMAC with a secret key before handling real identifiers.

## Data and privacy

No real customer data is included. Never commit real identity documents, selfies, credentials or `.env` files. Full Aadhaar numbers are sensitive, so mask or minimise them wherever possible.

## Citation

If you use this work, please cite the accompanying manuscript:

> K. Suhail, A. Bag, S. Maity, S. Simlote, "An explainable, graph-aware KYC–AML intelligence framework integrating browser-side identity verification, account-level graph neural networks, uncertainty-aware triage and evidence-grounded SAR drafting," manuscript in preparation, 2026.
