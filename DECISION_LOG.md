# Decision Log

## 2026-08-20 — Supabase MCP connected + listmap schema applied

### Decision
Install official hosted Supabase MCP (`https://mcp.supabase.com/mcp`) for this repo, create project **gis-info** (`adtftwtentpkmivszpjf`, region `ap-southeast-1`), apply the same six-table MySQL `listmap` structure.

### QA
- MCP: **PASS** (`user-supabase` authenticated)
- Tables: topography, dted, landused, sjung, audit_log, audit_document — PKs and camelCase columns match MySQL
- RLS enabled on all six (Flask uses Postgres URI, not the public anon API)
- Cost: **$0/month** free project

### Next
Copy local MySQL rows with `copy_local_to_supabase.py` after setting `DATABASE_URL` from the Supabase dashboard.

### Copy result (2026-08-20)
GIS catalog copied into project `gis-info` (`adtftwtentpkmivszpjf`): topography 23, dted 7, landused 13, sjung 2, audit_log 33. Render: **https://gis-info-supabase.onrender.com**

### QA fix (2026-08-20) — empty tables on Supabase Render
- **Root cause:** `ensure_schema_ready()` ran `CREATE TABLE` as `gis_info_render`; role lacked `CREATE` on schema `public` → `InsufficientPrivilege` (`app.py:156`, `database.py:ensure_schema_ready`).
- **Fix:** Granted schema/table privileges on Supabase; `database.py` skips DDL when `topography` already exists. Commit `5d5cf84` on `supabase`.
- **Verify:** `/api/records/topography` → `total: 23` on live URL.

### QA fix (2026-08-20) — Generate PDF blank
- **Root cause:** html2canvas captures blank when ancestors use `backdrop-filter` (glass-card). Print/Word unaffected (different paths). Live blob ~3KB empty vs ~112KB with content after fix.
- **Fix:** Disable backdrop-filter during capture (`body.pdf-exporting`), `onclone` cleanup, full height capture; download PDF before audit archive. `static/js/app.js`, `static/css/style.css`.
- **Verify:** After Render deploy of this commit, Generate PDF shows KEMBARAN I + selected rows.

### QA fix (2026-08-20) — PDF faint card shadow border
- **Root cause:** `body.light-theme .document-frame` box-shadow beat `.document-frame.pdf-capture` specificity, so html2canvas painted a soft card edge.
- **Fix:** Stronger PDF-capture selectors + inline chrome wipe (shadow/border/filter) on frame and ancestors.
- **Verify:** Regenerated PDF has no floating card outline; only document text + table borders.

---

## 2026-08-20 — Supabase branch (PostgreSQL, separate Render URL)

### Decision
Branch `supabase` swaps Aiven MySQL for Supabase PostgreSQL while keeping the same six-table `listmap` structure (quoted camelCase columns preserved).

### Why
User wants to evaluate Supabase without disturbing production on `main` + Aiven (`sap-listmap.onrender.com`).

### Design
1. `database.py` → `psycopg2` + `DATABASE_URL` (Supabase URI).
2. `schema_postgres.sql` mirrors `schema.sql` (BYTEA for audit blobs, JSONB for details, SERIAL for auto IDs).
3. `copy_local_to_supabase.py` copies from local MySQL `.env` to Supabase.
4. `render.yaml` on this branch: service `gis-info-supabase`, branch `supabase`, env `DATABASE_URL` only.
5. Production MySQL path stays on `main`.

### Deploy target
- Branch: `supabase`
- Render service: `gis-info-supabase`
- URL: `https://gis-info-supabase.onrender.com`

---

## 2026-08-20 — AI Council QA audit of recent changes

### QA result: **PASS with notes** (automated), **PARTIAL pending** (live Render/PDF eye-check)

| Area | Result | Evidence |
|------|--------|----------|
| Automated tests | **PASS** | `pytest` → 33 passed |
| Compile | **PASS** | `app.py`, `database.py`, `export_*.py` |
| AI Council rule | **PASS** | `.cursor/rules/ai-council.mdc` alwaysApply |
| Word export + naming | **PASS** | `/api/export/docx`, `export_filenames.py`, audit action |
| Doc layout (code) | **PASS** | Header `templates/index.html:351-353`; A/B/C in `app.js`; gold `#FFD966` in CSS |
| PDF clip fix (code) | **PASS** | `setPdfCaptureMode` 794px + `body.pdf-exporting` |
| DB hardening (code) | **PASS** | Aiven auto-SSL, no pool by default, `/api/health`, lazy schema |
| Live Render DB | **PASS** | `/api/health` → `"db":"ok"`, Aiven host + SSL (`app.py:156` lazy schema) |
| Live login page | **PASS** | Playwright → `Login — GIS Info` at `/login` |
| Live PDF right edge | **PENDING user** | Regenerate after deploy of `710983e` |

### Notes
- Password was shared in chat earlier — rotate Aiven password when stable.
- **Live follow-up (2026-08-20):** Playwright MCP (`user-playwright`) re-verified health + login page; uncommitted audit artifacts: `DECISION_LOG.md`, `.cursor/mcp.json`, `package.json`, `.gitignore` (`node_modules/`).
- Playwright MCP also at project `.cursor/mcp.json`; enable in Cursor **Settings → MCP** if not already active.

---

## 2026-08-20 — AI Council Cursor rule

### Decision
Add always-on project rule `.cursor/rules/ai-council.mdc` with seats: Orchestrator, Architect, Design, QA.

### Why
User wants multi-role discussion on every prompt before execution, consistent with existing Orchestrator / Architect / QA personas plus Design for GIS Info UI/docs.

### Design
1. Short labeled council brief → Orchestrator verdict → execute → QA check.
2. Fast path for trivial asks.
3. Architectural outcomes still append to this log.

---

## 2026-08-20 — Fix stuck table loading (Aiven/Render)

### Decision
Disable DB pool by default, auto-enable TLS for Aiven hosts, lazy schema ensure, public `/api/health`, clearer 503 errors on record fetch.

### Why
Live UI stayed on loading / unable to load records — cold Aiven + pooled sockets + startup schema blocking were the likely causes.

---

## 2026-08-20 — Word export + KEMBARAN I filenames

### Decision
Add Word (.docx) export matching KEMBARAN I layout; all export downloads use `KEMBARAN I - GIS INFO {subtitle}`.

### Why
User requested Word export and consistent official naming across print/PDF/Word/Excel.

---

## 2026-08-20 — Load reliability + KEMBARAN mark + black input text

### Decision
Harden MySQL connects (retry/ping/SSL/timeouts), retry record fetches client-side, set document input text to black, add top-right **KEMBARAN I** mark.

### Why
Live site showed slow/failed "Unable to load records" (cold Aiven + flaky pooled sockets). User clarified red was only a Word edit marker — printed text should be black. Word header has right-aligned KEMBARAN I.

---

### Decision
Rebrand the app to **GIS Info** and match printable/PDF output to `KEMBARAN I - GIS INFO.docx` (Times New Roman 12pt; red `#EE0000` = editable/input data).

### Why
User wants public-facing title/URL naming as GIS Info, and export documents that follow the official Word kembaran layout.

### Design
1. UI titles (browser, header, login) → `GIS Info`.
2. Document fixed title: `SENARAI LEMBARAN DAN JENIS PETA` (black, bold, underline).
3. Editable subtitle from header input (red) — default `EKSESAIS LATIHAN TAHUN 2026`.
4. Sections/tables match Word: Raster Topography, Landused, DTED; data cells red; TOTAL row black label + red count.
5. Render public URL rename is done in Render Dashboard → Settings → Name (e.g. `gis-info`), not only in code.

---

## 2026-08-19 — External MySQL for Render (no template)

### Decision
Use a managed public MySQL (recommended: Aiven free) with the Render web service; auto-create tables on app startup; support `DB_SSL`.

### Why
Render dashboards often have no MySQL template. The deployed site had no tables because no MySQL was attached / schema never applied.

### Design
1. Document Aiven free MySQL + `DB_*` + `DB_SSL=true` on the Render service.
2. `database.ensure_core_tables()` creates topography/dted/landused/sjung/audit tables with `IF NOT EXISTS`.
3. App startup calls `ensure_core_tables()` so a correct DB connection creates schema without a manual Shell step.
4. Keep Render Private Service MySQL as a paid alternative (fork `render-examples/mysql`).

---

## 2026-08-19 — Public deploy on Render

### Decision
Target Render for public hosting: Python web service + MySQL private service; honor platform `PORT`; ship `render.yaml` + `init_schema.py`.

### Why
Repo is already on GitHub; local Docker/gh CLI unavailable. Flask + MySQL does not fit static hosts. Render connects to GitHub without a local Docker install.

### Design
1. `config.FLASK_PORT` reads `PORT` then `FLASK_PORT` (Render injects `PORT`).
2. `render.yaml` defines the free web service and required env vars (`sync: false` for secrets/DB).
3. MySQL stays a separate private service (Render MySQL template / `render-examples/mysql`) with disk at `/var/lib/mysql`.
4. One-time schema via `python init_schema.py` from Render Shell (private DB not reachable from the developer PC).

### Constraints
- Free web tier may sleep when idle.
- MySQL private service + disk typically require a paid Render plan.

---

## 2026-07-30 — Audit document history for export/print

### Decision
Archive the actual export/print document alongside audit log entries, and let admins reopen it from the Audit Log **Details** column.

### Why
Audit previously stored only metadata (`action`, `report_ref`, `item_count`, JSON `details`). Admins could see that an export happened, but could not recover the document that was exported or printed.

### Design
1. New MySQL table `audit_document` (`LONGBLOB`), 1:1 with `audit_log.id` via FK + unique `audit_id`.
2. Do **not** store file bytes inside `audit_log.details` JSON (keeps list queries fast).
3. Capture points:
   - Excel: server archives workbook bytes in `/api/export/xlsx`.
   - PDF / Print: client generates PDF blob, uploads via `POST /api/audit/document`, then downloads/prints.
4. Admin opens archived file via `GET /api/audit/<id>/document` (PDF inline, Excel attachment).
5. Audit list joins `has_document` / filename so Details can render a clickable report name.

### Constraints
- Max archived document size: 15 MB.
- Allowed MIME types: PDF and XLSX only.
- Print archive is a PDF snapshot of the preview (browser print dialog cannot be captured as a true print spool).

### Migration
- `migrations/003_audit_document.sql` (applied to local `listmap` DB on 2026-07-30).
