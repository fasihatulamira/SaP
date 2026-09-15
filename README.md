# SaP LISTMAP — GIS Info (`supabase` branch)

Web dashboard for browsing cartography datasets (topography, land use, DTED, Topo), selecting records, and exporting Print / PDF / Word / Excel.

This branch uses **Supabase PostgreSQL**. See [DEPLOYMENT_SUPABASE.md](DEPLOYMENT_SUPABASE.md) for live deploy.

## Requirements

- Python 3.10+
- PostgreSQL (Supabase) via `DATABASE_URL`

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy env template and set credentials:

   ```bash
   copy .env.example .env
   ```

   Set `DATABASE_URL` (Supabase URI) and auth passwords.

3. Apply schema (once):

   ```bash
   python init_schema.py
   ```

4. (Optional) Seed demo rows if tables are empty:

   ```bash
   python populate_data.py
   ```

5. Run:

   ```bash
   python app.py
   ```

   Production: `python run_production.py`

6. Open http://127.0.0.1:5000 and sign in.

## Copy from local MySQL (optional)

If you still have a local MySQL `listmap` database:

```powershell
$env:DATABASE_URL="postgresql://..."
python copy_local_to_supabase.py
```

## Tests

```bash
pytest
```

## Roles

| Role | Access |
|------|--------|
| **admin** | Full dashboard, CRUD, audit log (view/edit/delete documents) |
| **user** | Browse, select, export — no audit log |

## Live sites

| Branch | URL |
|--------|-----|
| `supabase` | https://gis-info-supabase.onrender.com |
| `main` (MySQL / Aiven) | https://sap-listmap.onrender.com |

For MySQL/`main` deployment notes see [DEPLOYMENT.md](DEPLOYMENT.md).
