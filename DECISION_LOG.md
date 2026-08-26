# Decision Log

## 2026-08-26 — Hide landused ID in selection table

### Decision
Remove **Landused ID** from the landused selection table. Sequential IDs still appear only on the document/export after selection order.

### Why
Catalog IDs no longer drive the report; showing them in the picker was confusing.

---

## 2026-08-26 — Header stay centered; data cells left-aligned

### Decision
Landused CATEGORY and DTED IDENTIFICATION NAME **headers** stay centered; only **item** (data) cells are left-aligned.

### Why
User wanted title row centered and body text left-aligned for readability.

---

## 2026-08-26 — Landused IDs follow selection order + left-align names

### Decision
Landused **LANDUSED ID** on the document/export is the selection sequence (1, 2, 3…), not the stored catalog ID. Landused **CATEGORY** and DTED **IDENTIFICATION NAME** data cells are left-aligned (headers remain centered).

### Why
Admins pick categories in report order (e.g. air → pertanian → hutan) and want those positions as the IDs. Name columns were centered and harder to read.

### Design
1. Client keeps landused Map insertion order (click order); `getSelectedSorted("landused")` assigns `landused_id = index + 1`.
2. Word/Excel also number landused IDs as `idx + 1` in payload order.
3. CSS/Word/Excel left-align the category / identification-name column only.

---

## 2026-08-26 — Admin edit/delete for archived audit documents

### Decision
Admins can **view**, **edit**, and **delete** archived export/print documents from the Audit Log page. Edit replaces or renames the stored file in place. Delete removes the audit log row and its document.

### Why
Admins could previously only reopen the archived file. They needed a way to correct a bad archive (wrong file / name) and to remove documents that should not stay in history.

### Design
1. `PUT /api/audit/<id>/document` (admin): rename and/or replace PDF/XLSX/DOCX (same 15 MB + MIME rules as archive).
2. `DELETE /api/audit/<id>` (admin): delete `audit_log` row after deleting `audit_document` (works even if FK cascade is missing).
3. Audit Log **Details** column: the document name still **views**; labeled **Edit** and **Delete** buttons sit beside it (not a separate Actions column, which was easy to miss / clip).
4. Edit uses a nested modal (filename + optional file). Delete uses a confirm dialog.
5. Replacements record `replaced_by` + `replaced_at` in `audit_log.details` so the mutation is visible in the remaining entry.

### Constraints
- User role remains 403 on list/view/edit/delete of archived documents.
- Mutating the audit archive is an explicit product choice; the original export event timestamp is kept.

### QA
Pass (`python -m pytest` — 44 tests).
- Admin-only PUT/DELETE; user 403 covered in `tests/test_roles_audit.py`.
- Postgres BYTEA writes use `psycopg2.Binary` on this branch (`database.py` `update_audit_document`).

---

## 2026-08-21 — Category rename + KEMBARAN column widths + subtitle

### Decision
UI tabs: Topography→**Topo Raster**, Land Used→**Landused**, Sjung→**Topo**. Default subtitle → **EKSESAIS**. Document/PDF/Word table columns match official KEMBARAN I sample proportions.

### Why
User alignment with company naming and official kembaran layout (SHEET NAME wider; NUM. narrow).

---

## 2026-08-21 — Print shadow + Generate PDF TOTAL gap

### Decision
Tighten print/PDF chrome stripping and stop html2pdf from avoiding every `<tr>` (which opened gaps before TOTAL).

### Why
User compared Generate PDF vs Print→Save as PDF: Generate had TOTAL row visually detached; Print still showed a faint card shadow.

### Fix
- Print: beat `body.light-theme .document-frame` specificity; zero shadow/border on `.preview-panel`; `body.is-printing` class around `window.print()`.
- Generate PDF: `pagebreak.mode = ["css"]` without `avoid: tr`; force collapsed table borders in `.pdf-capture`.

### QA
Pending live eye-check after deploy on main + supabase.

---

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
