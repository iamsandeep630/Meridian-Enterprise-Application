# SOP-ENG-004: Multi-File Architectural Defect Estimation & SLA Guidelines

**Confluence Space:** Engineering Standard Operating Procedures (ENG-SOP)
**Document ID:** SOP-ENG-004 | **Category:** Technical Estimation & SLA Standards
**Last Updated:** 2026-09-30 | **Author:** IT Architecture & Support Engineering

## 1. Overview & Purpose
This Standard Operating Procedure (SOP) governs technical effort calculation, cross-file impact analysis, and customer SLA communication when an enterprise application failure is caused by an architectural defect spanning multiple system layers (e.g. database schema, backend computation APIs, and frontend views).

## 2. Classification of Multi-File Architectural Defects
A defect is classified as an **Architectural Multi-File Defect** when resolving it requires coordinated changes across two or more independent architectural boundaries:
1. **Data Persistence Layer:** Altering database models, table schemas, adding foreign keys, migration scripts, or data backfilling.
2. **Business Logic & API Layer:** Refactoring core computation services, currency conversion engines, tax calculation logic, or API contracts.
3. **User Interface / Presentation Layer:** Updating templates, client-side validation, error boundaries, or report generation views.

### Example Defect: Currency Tax Aggregation Error
* **Symptom:** Application crashes when attempting to aggregate line-item taxes across multi-currency invoices (USD, EUR, GBP) without an exchange rate normalization schema.
* **Impacted Layers:**
  - `backend/database/models.py`: Requires adding multi-currency exchange rate and normalized tax columns to `Invoice` and `Product` models.
  - `backend/routers/enterprise.py`: Requires implementing exchange rate lookup and multi-currency tax aggregation computation algorithms.
  - `frontend/templates/employee_portal.html`: Requires updating the tax reconciliation reporting interface, currency pickers, and exception handling.

## 3. Standard Estimation & Effort Benchmark Matrix
For architectural defects requiring schema migration, calculation engine refactoring, and UI updates, the standard engineering estimate is strictly calculated as follows:

| Phase | Scope of Work | Standard Benchmark |
| :--- | :--- | :---: |
| **Phase 1: Database Migration** | Schema definition updates (`models.py`), migration generation, historical data backfill script, rollback validation. | **1 Business Day** |
| **Phase 2: Backend Calculation** | Implementing currency exchange lookup service, updating tax aggregation logic, unit tests in `enterprise.py`. | **1 Business Day** |
| **Phase 3: Frontend Reporting** | Tax reconciliation view enhancements, currency selection, error boundaries in `employee_portal.html`. | **1 Business Day** |
| **Phase 4: QA & Deployment** | End-to-end integration testing, financial accuracy regression, staging sign-off, and production deployment. | **1 Business Day** |
| **TOTAL ESTIMATED TIMELINE** | **Comprehensive Multi-File Resolution** | **4 Business Days** |

## 4. Support Engineer (L2/L3) Decision & Communication Protocol
1. **Tool-Assisted Discovery:** The Support Engineer invokes the Code Analysis Agent (SmartFix) to trace affected files in the repository and compute the baseline effort.
2. **Engineer Decision & Validation:** The Support Engineer (Alex Turner) reviews the agent's findings, validates that the 4-day benchmark aligns with current sprint capacity, and personally confirms the timeline.
3. **Direct Customer ETA Communication:** The Support Engineer personally notifies the reporting employee (Maya) via the live chat session with the official 4 business day ETA and explanation of the multi-file scope.
4. **Jira Lifecycle Management:** 
   - The Jira ticket MUST remain **OPEN** in status `In Progress` / `L2 Confirmed`.
   - The ticket must NOT be closed until the development team completes deployment and the fix is verified in production.
