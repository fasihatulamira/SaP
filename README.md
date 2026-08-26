# SaP LISTMAP

Web dashboard for browsing cartography datasets (topography, land use, DTED, Sjung), selecting records, and exporting a printable PDF report.

## Requirements

- Python 3.10+
- MySQL 8+ with the `listmap` database

## Setup

1. Clone the repository and create a virtual environment (recommended).

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create the database and tables:

   ```bash
   mysql -u root -p < schema.sql
   ```

4. Copy `.env.example` to `.env` and set your credentials:

   ```bash
   copy .env.example .env
   ```

5. (Optional) Seed land use categories if the table is empty:

   ```bash
   python populate_data.py
   ```

6. Run the application:

   **Development:**
   ```bash
   python app.py
   ```

   **Production (Waitress WSGI server):**
   ```bash
   python run_production.py
   ```

7. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) and sign in with your configured credentials.

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | `development` or `production` | `development` |
| `SECRET_KEY` | Flask session signing key | — |
| `DB_HOST` | MySQL host | `localhost` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | MySQL user | — |
| `DB_PASSWORD` | MySQL password | — |
| `DB_NAME` | Database name | — |
| `FLASK_HOST` | Bind address | `127.0.0.1` |
| `FLASK_PORT` | Bind port | `5000` |
| `FLASK_DEBUG` | Enable Flask debug mode | `False` |
| `AUTH_ENABLED` | Enable login protection | `True` |
| `AUTH_USERNAME` | Login username | `admin` |
| `AUTH_PASSWORD` | Login password | — |
| `RATE_LIMIT_ENABLED` | Enable API rate limiting | `True` |
| `RATE_LIMIT_DEFAULT` | Default request limit | `120 per minute` |
| `SESSION_LIFETIME_MINUTES` | Login session timeout | `30` |

**Auth notes:**
- Login is required when `AUTH_ENABLED=True` and at least one auth password is set in `.env`.
- Set `AUTH_ENABLED=False` to disable login (local dev only).
- Change auth passwords before any shared or production deployment.

**Production checklist:**
- Set `APP_ENV=production`
- Set `FLASK_DEBUG=False`
- Set a strong `SECRET_KEY` and `AUTH_PASSWORD`
- Run with `python run_production.py` (not `flask run`)

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/login` | Login page |
| `POST` | `/logout` | End session |
| `GET` | `/` | Dashboard UI (auth required) |
| `GET` | `/api/filters` | Release years and DTED levels |
| `GET` | `/api/records/<category>` | Paginated records for one category |

All API routes return `401` when not authenticated.

## Tests

```bash
pip install -r requirements.txt
pytest
```

## User roles

| Role | Access |
|------|--------|
| **admin** | Full dashboard, exports, audit log viewer with document view/edit/delete |
| **user** | Browse, select, export (Excel/PDF/print) — no audit log |

Configure in `.env`:

```env
AUTH_ADMIN_USERNAME=admin
AUTH_ADMIN_PASSWORD=your-admin-password
AUTH_USER_USERNAME=user
AUTH_USER_PASSWORD=your-user-password
```

## Docker (one-command deploy)

```bash
docker compose up --build
```

App: http://localhost:5000  
Default Docker credentials (change in `.env.docker`):

- Admin: `admin` / `admin123`
- User: `user` / `user123`

## Upgrading an existing database

If you installed before audit logging was added:

```bash
mysql -u root -p listmap < migrations/001_audit_log.sql
```

If you need archived export/print documents in the audit log:

```bash
mysql -u root -p listmap < migrations/003_audit_document.sql
```

## Production deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Waitress, nginx HTTPS, and Windows service setup.

## CI

GitHub Actions runs `pytest` on push/PR to `main` (see `.github/workflows/ci.yml`).

### Categories

`topography`, `dted`, `landused`, `sjungu`

### Query parameters for `/api/records/<category>`

| Parameter | Applies to | Description |
|-----------|------------|-------------|
| `page` | All | Page number (default: `1`) |
| `limit` | All | Rows per page (default: `8`, max: `100`) |
| `search` | All | Text search filter |
| `year` | topography | Filter by release year |
| `level` | dted | Filter by DTED level |

### Example response

```json
{
  "items": [{ "sheetNum": "AP24", "sheetName": "MERLIMAU", "sheetScale": "1:50000", "release_year": 2017 }],
  "total": 23,
  "page": 1,
  "limit": 8,
  "total_pages": 3
}
```
