# Decision Log

## 2026-08-19 — GIS Info branding + KEMBARAN I document format

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
