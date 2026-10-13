# KYC-AML Intelligence Platform — Frontend

React + Vite + JavaScript (JSX) + Tailwind CSS client for the existing FastAPI backend.
Two role-based portals (`customer`, `analyst`) share one codebase. The backend is **not** modified.

## Quick start

```bash
cd frontend
cp .env.example .env          # then edit VITE_API_BASE_URL if your API is hosted elsewhere
npm install
npm run dev                   # http://localhost:3000
```

`.env` (never committed):

```
VITE_API_BASE_URL=http://127.0.0.1:8000     # or your hosted API URL, no trailing slash
```

The URL is read in exactly one place: `src/api/client.js` (`import.meta.env.VITE_API_BASE_URL`).
Restart `npm run dev` after changing `.env`.

Other commands: `npm run build` (production bundle in `dist/`), `npm run preview` (serves it on port 3000).

## CORS (important)

The dev server is pinned to **port 3000** (`strictPort`), which matches the backend's existing allowlist
(`http://localhost:3000`, `http://127.0.0.1:3000`). Open the app at `http://localhost:3000` or `http://127.0.0.1:3000`.

If you deploy this frontend, or use another port such as Vite's default 5173, add that exact origin to the
backend's CORS `allow_origins`, e.g.:

```python
allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://your-frontend-domain"]
```

A browser CORS failure shows up in the UI as "Cannot reach the API…".

## Workflows and route map

| Route | Who | Purpose |
|---|---|---|
| `/login`, `/register` | public | Customer sign-in and registration (role is never user-chosen) |
| `/analyst/login` | public | Analyst sign-in (no public analyst registration) |
| `/customer/dashboard` | customer | Welcome, KYC + onboarding status, balances, recent transactions, latest risk level |
| `/customer/kyc` | customer | KYC submission (form generated from the backend `KYCSubmit` schema) |
| `/customer/accounts`, `/customer/transactions` | customer | Own accounts / transactions with search + filters |
| `/customer/risk` | customer | Risk level and status only (no analyst data) |
| `/customer/profile` | customer | Own details, sign out |
| `/analyst/dashboard` | analyst | Counts, risk-level and alert-status charts, recent alerts and cases |
| `/analyst/customers`, `/analyst/customers/:id` | analyst | Directory, search/filter; KYC, accounts, transactions, assessments |
| `/analyst/alerts`, `/analyst/alerts/:id` | analyst | Filter, edit, change status, feedback |
| `/analyst/cases`, `/analyst/cases/:id` | analyst | List, details, status update, analyst feedback |
| `/analyst/assessments` | analyst | Full risk breakdown per customer or by assessment ID |
| `/analyst/aml` | analyst | Run AML analysis, score a transaction, model health |
| `/analyst/sar` | analyst | SAR preview, drafts, review status (always labelled draft) |
| `/analyst/feedback` | analyst | Feedback and feedback datasets |
| `/access-denied` | any signed-in | Shown when the role doesn't match a route |

After login, `GET /api/v1/auth/me` supplies the role; users are sent to `/customer/*` or `/analyst/*` accordingly.

## How forms stay honest: schema-driven requests

I did not have your Pydantic schemas (`RegisterRequest`, `KYCSubmit`, case/alert/SAR request bodies, etc.),
and the brief says not to invent fields. FastAPI publishes every request schema at `/openapi.json`, so
`src/components/forms/SchemaForm.jsx` reads the real schema for each endpoint and renders the form from it:
field types, required flags, enums (e.g. the allowed SAR review statuses and case statuses), min/max and patterns.
422 responses are mapped back to the matching fields.

Fallbacks, if `/openapi.json` is disabled on the server:
- Login and register fall back to `email`/`password` and `full_name`/`email`/`password` (marked "not verified" in the UI).
- Every other form falls back to a raw JSON body editor with a visible warning.

Session-controlled values (e.g. `customer_id` on the KYC form) are forced from `/auth/me` and sent only if the schema defines that field.

## Security notes

**The frontend is not a security boundary.** Route guards and hidden links only improve the experience.
The backend must authorise every request independently.

Things to verify on the backend (I cannot confirm them from the frontend):
1. **Ownership checks** on `GET /api/v1/customers/{id}`, `/kyc/latest`, `/accounts`, `/transactions`, `/assessments`,
   `POST /customers/{id}/kyc`, `/api/v1/accounts/{id}/transactions` and `/api/v1/assessments/{id}`: a customer token must only
   read/write its own `customer_id`. If these only check "is logged in", any customer can read another customer's data by changing an ID.
2. **Role enforcement** (`require_analyst`) on `/api/v1/customers` (list/create), `/api/v1/alerts*`, `/api/v1/feedback*`,
   `/api/v1/sar-drafts*`, `/api/v1/cases/{id}/sar`, `/api/v1/aml/score-transaction`, `/api/v1/transactions/import`,
   `/api/v1/assessments` (create), `/api/v1/customers/{id}/aml-analysis`.
3. **`POST /cases`** may still be unprotected. The UI deliberately does not call it.
4. **Customer-safe assessment responses:** the customer risk page only *renders* risk level and status, but if the API returns
   scores, typology or risk factors to a customer token, they are still visible in the browser's network tab. Return a reduced
   schema for customers.
5. Legacy/demo endpoints (`/test/*`, `/triage`, `/aml/{case_id}`, `/triage/{case_id}`) are not used. Check their auth before production.

### Token storage trade-off

The API returns a bearer token, so the client must keep it somewhere JavaScript can read. Any such storage is exposed to XSS.
This app keeps only the token (never the password, never the user object) in `sessionStorage`: scoped to one tab and cleared on tab close.
The role is always re-read from `/auth/me`, so editing storage cannot change it. `localStorage` would persist across restarts but widens exposure.
The stronger design is an `HttpOnly; Secure; SameSite` cookie issued by the backend, which needs a backend change. Everything token-related lives in `src/auth/tokenStore.js` and `src/api/client.js`.

Error handling: 401 on a protected call clears the session and returns to login; 403 shows "Access denied"; 400/404/409/422/500/503 show the
FastAPI `detail` message. `fallback_completed` / `unavailable` results are shown with warning banners and never styled as success.

## Backend assumptions to verify

- `GET /api/v1/auth/me` returns `id`, `email`, `role`, `customer_id`; login returns `access_token`.
- List endpoints return an array (an envelope with `items`/`results`/`data` also works).
- `POST /cases/{id}/sar` = SAR **preview**; `POST /api/v1/cases/{id}/sar` = **create draft** from case; `GET /api/v1/cases/{id}/sar` = fetch drafts. Swap in `src/services/sarService.js` / `caseService.js` if your semantics differ.
- Case schema is not specified: case tables/details render whatever fields the API returns (`case_id` or `id` used as the identifier).
- "Open alerts" counts alerts whose `status` is `open`; "High-priority cases" counts cases whose `priority` (or `severity`/`risk_level`) contains high/critical/urgent. No risk thresholds are invented: risk levels are shown as supplied.
- No global assessments endpoint exists, so dashboard risk charts sample the first 25 customers (stated on screen).

## Endpoint integration status

Integrated (calls made from the UI):
`POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `GET /api/v1/health`,
`GET|POST /api/v1/customers`, `GET /api/v1/customers/{id}`, `POST|GET .../kyc`, `GET .../kyc/latest`, `POST .../aml-analysis`,
`GET|POST .../accounts`, `GET .../transactions`, `GET .../assessments`, `POST /api/v1/accounts` (service only),
`GET|POST /api/v1/accounts/{id}/transactions`, `POST /api/v1/transactions/import`, `POST /api/v1/assessments`, `GET /api/v1/assessments/{id}`,
all six alert endpoints, `GET /cases`, `GET /cases/{id}`, `PATCH /cases/{id}/status`, `POST /cases/{id}/feedback`, `GET /cases/feedback/dataset`,
`POST /cases/{id}/sar`, `POST|GET /api/v1/cases/{id}/sar`, `POST /api/v1/sar-drafts`, `GET /api/v1/sar-drafts/{id}`, `PATCH /api/v1/sar-drafts/{id}/status`,
`GET /api/v1/feedback`, `GET /api/v1/feedback/dataset`, `POST /api/v1/aml/score-transaction`, `GET /health` (service only).

Deliberately not integrated: `POST /cases` (authorization unconfirmed), `/test/*`, `/triage`, `/aml/{case_id}`, `/triage/{case_id}` (internal/demo).
`POST /api/v1/transactions/import` is only usable if it accepts JSON; a multipart/file contract shows an "unsupported" notice.

## Source map and data flow

```
Page component → useAsync(loader) → services/*.js → api/client.js (axios + bearer interceptor)
                                                   → utils/errors.js (ApiError: status, message, fieldErrors)
Page component → SchemaForm → useOperationSchema → api/openapi.js (/openapi.json) → validated payload → services/*.js
```

- `src/api/client.js` — single axios instance, `VITE_API_BASE_URL`, bearer header, 401 event.
- `src/api/openapi.js` — OpenAPI loader and request-schema reader.
- `src/auth/` — `AuthProvider` (session restore via `/auth/me`, login, logout), `ProtectedRoute`, `RoleRoute`, `tokenStore`.
- `src/services/` — one module per backend area; no Axios calls in pages.
- `src/components/common/` — design system: `StatCard`, `StatusBadge`, `RiskBadge`, `DataTable`, `AutoTable`, `SearchInput`, `FilterBar`, `LoadingState`, `EmptyState`, `ErrorState`, `ConfirmDialog`, `PageHeader`, `Modal`, `Tabs`, `DetailList`.
- `src/components/layout/` — `AppLayout`, `Sidebar`, `Topbar`.
- `src/components/forms/SchemaForm.jsx` — generated forms; `CustomerPicker.jsx` — analyst customer selector.
- `src/components/charts/` — Recharts donut and bar charts.
- `src/pages/customer/*`, `src/pages/analyst/*`, `src/pages/auth/*` — screens.

## Testing checklist

1. `npm run dev`, open `http://localhost:3000`. The top-right pill (analyst portal) shows API health.
2. Register at `/register`: a 409 shows a duplicate-account message; success redirects to `/login`.
3. Sign in as that customer: you land on `/customer/dashboard`. Visiting `/analyst/alerts` redirects to `/access-denied`.
4. Sign in on `/analyst/login` with a provisioned analyst: you land on `/analyst/dashboard`.
5. Delete the token in DevTools → Application → Session Storage and reload: you return to `/login`.
6. Edit the stored token to garbage: the next call returns 401 and the session is cleared.
7. Customer network tab: no calls to `/api/v1/customers` (list), `/api/v1/alerts`, `/cases`, `/api/v1/feedback`, or any SAR path.
8. Security check (needs two customers): with customer A's token, `GET /api/v1/customers/<B's id>` should return 403/404. If it returns data, the backend lacks ownership enforcement.
