# Deploy GIS Info with Supabase (PostgreSQL)

This branch (`supabase`) uses **Supabase PostgreSQL** instead of Aiven MySQL.  
Production on `main` (`https://sap-listmap.onrender.com`) is **not** affected.

## 0. Cursor MCP (this repo)

`.cursor/mcp.json` includes the official hosted Supabase MCP:

```json
"supabase": { "url": "https://mcp.supabase.com/mcp" }
```

1. Cursor **Settings → Tools & MCP**
2. Enable **supabase**
3. Complete the browser login when Cursor prompts (grant the org that will own GIS Info)

After that, this chat can list projects, apply `supabase/migrations/20260820120000_listmap_schema.sql`, and verify tables.

**Live project (created 2026-08-20):**

| Field | Value |
|-------|--------|
| Name | `gis-info` |
| Ref | `adtftwtentpkmivszpjf` |
| Region | `ap-southeast-1` (Singapore) |
| Dashboard | https://supabase.com/dashboard/project/adtftwtentpkmivszpjf |
| API URL | https://adtftwtentpkmivszpjf.supabase.co |

Schema is already applied on this project (same 6 tables as MySQL `listmap`).

## 1. Create Supabase project

1. Sign up at [https://supabase.com](https://supabase.com) (free tier available).
2. **New project** → choose region close to Render (e.g. Singapore).
3. Save the **database password** shown once.

## 2. Apply schema (same structure as MySQL `listmap`)

**Option A — SQL Editor** (Supabase dashboard → SQL → New query):

- Paste and run `schema_postgres.sql` from this repo.

**Option B — from your PC** (after `pip install psycopg2-binary`):

```powershell
$env:DATABASE_URL="postgresql://postgres.[ref]:[password]@db.[ref].supabase.co:5432/postgres?sslmode=require"
python init_schema.py
```

Tables created (same logical layout as MySQL):

| Table | Primary key |
|-------|-------------|
| `topography` | `sheetNum` |
| `dted` | `id_name` |
| `landused` | `landused_id` (serial) |
| `sjung` | `sheetNum` |
| `audit_log` | `id` (serial) |
| `audit_document` | `id` (serial), FK → `audit_log` |

Column names `sheetNum`, `sheetName`, `sheetScale` are preserved (quoted in PostgreSQL).

## 3. Copy data from local MySQL

Your local `.env` should still point at MySQL (`listmap`). Set Supabase URL separately:

```powershell
$env:DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require"
python copy_local_to_supabase.py
```

Use `--force` to overwrite if tables already have rows.

## 4. Deploy on Render (separate URL)

1. Push branch `supabase` to GitHub.
2. Render dashboard → **New** → **Blueprint** (or add service manually).
3. Connect repo, select branch **`supabase`**.
4. Service name from `render.yaml`: **`gis-info-supabase`**  
   → URL: **`https://gis-info-supabase.onrender.com`**
5. Set env vars:
   - `DATABASE_URL` — Supabase connection URI (Session pooler recommended for Render)
   - `AUTH_ADMIN_PASSWORD`, `AUTH_USER_PASSWORD`
6. Deploy. Check **`/api/health`** → `"db":"ok"`, `"backend":"postgresql"`.

### Manual service (without Blueprint)

- **New Web Service** → repo → branch `supabase`
- Build: `pip install -r requirements.txt`
- Start: `python run_production.py`
- Health check path: `/api/health`

## 5. Connection string tips

| Setting | Value |
|---------|--------|
| Supabase URI | Project Settings → Database → **Connection string** → URI |
| Render env | `DATABASE_URL` (Render accepts `postgres://`; app normalizes to `postgresql://`) |
| SSL | Add `?sslmode=require` if not included |
| Pooler | Port **6543** (pooler) or **5432** (direct) |

## 6. Local dev on this branch

```powershell
pip install -r requirements.txt
$env:DATABASE_URL="postgresql://..."
python run_production.py
```

Keep MySQL vars in `.env` only if you run `copy_local_to_supabase.py`.

## Branch summary

| Branch | Database | Render service | URL |
|--------|----------|----------------|-----|
| `main` | Aiven MySQL | `gis-info` | `sap-listmap.onrender.com` |
| `supabase` | Supabase Postgres | `gis-info-supabase` | `gis-info-supabase.onrender.com` |
