# Runtime Validation Report

**Generated**: 2026-10-10
**Target**: `E:\kyc-aml-intelligence`

## Summary

| Step | Status | Exit Code | Details |
|------|--------|-----------|---------|
| Startup | PASS | 0 | Uvicorn started on `127.0.0.1:8001`; `/api/v1/health` returned degraded model status. |
| Integration Tests | PASS | 0 | `pytest -q runtime_validation`: 4 passed. |
| Backend Regression | PASS | 0 | Focused AML/API/migration/adapter suite: 15 passed, 36 warnings. |
| Frontend Type Check | PASS | 0 | `pnpm exec tsc --noEmit`. |
| Frontend Build | PASS | 0 | `pnpm --config.node-linker=hoisted build`. |
| Browser E2E | PARTIAL | n/a | Customer flow and analyst alert actions exercised manually in Chromium; no automated Playwright spec was committed. |

**Overall**: NEEDS_SIGNOFF

## Evidence

- Health: `{"status":"degraded","models":{"gnn":"unavailable","xgboost":"unavailable"}}`
- Fresh backend process loaded persisted data: 5 alerts and 16 feedback records remained available.
- Customer browser flow used server-returned customer, account, and transaction IDs; KYC completed; AML returned HTTP 503 without creating a fabricated assessment.
- Analyst browser flow displayed real alert IDs and linked customer IDs, persisted feedback, updated alert status, created a SAR draft, and moved SAR review status to `IN_REVIEW`.
- SAR validation remained `NEEDS_REVIEW`; no unsupported successful validation was claimed.

## Environment and Known Gaps

- Docker was not available, so validation used the copied SQLite runtime database.
- Node.js and Chromium were available. The production frontend ran on `http://127.0.0.1:3000`.
- GNN and XGBoost artifacts/runtimes remain unavailable. AML analysis therefore returns a truthful unavailable response.
- The optional FinCEN embedding dependency was changed to lazy-load so it cannot prevent API startup; SAR retrieval still reports unavailable if that runtime cannot load.
- Legacy landing, cases, and admin views still contain demonstration/mock content and require a separate cleanup.
- Demo authentication does not persist the backend customer ID across browser sessions.
- The browser validation was manual and did not cover every legacy/mock screen.

## Remaining Blockers

1. Provide and register real GNN/XGBoost inference adapters and artifacts before enabling successful AML assessments.
2. Replace or clearly isolate remaining legacy mock-driven screens.
3. Add committed Playwright specs for the customer and analyst journeys if repeatable browser regression evidence is required.
