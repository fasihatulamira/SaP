# SaP LISTMAP — Production Deployment Guide

## Deploy on Render (public URL)

Render does **not** include a built-in MySQL product in most dashboards (the old “MySQL template” is easy to miss or unavailable). Your web app and the database are separate: you must add a MySQL host and set `DB_*` env vars.

### Recommended: free MySQL on Aiven + Render web service

**1. Create MySQL on Aiven (free tier)**

1. Sign up at [https://aiven.io/free-mysql-database](https://aiven.io/free-mysql-database) (GitHub/Google OK).
2. Create a **MySQL** service on the free plan.
3. Open **Overview / Connection information** and copy:
   - Host
   - Port (not always `3306`)
   - User
   - Password
   - Database name (often `defaultdb`)

**2. Point the Render web service at Aiven**

In Render → your web service → **Environment**, set:

| Key | Value |
|-----|--------|
| `DB_HOST` | *(Aiven host)* |
| `DB_PORT` | *(Aiven port)* |
| `DB_USER` | *(Aiven user)* |
| `DB_PASSWORD` | *(Aiven password)* |
| `DB_NAME` | `defaultdb` *(or the name Aiven shows)* |
| `DB_SSL` | `true` |
| `APP_ENV` | `production` |
| `FLASK_HOST` | `0.0.0.0` |
| `FLASK_DEBUG` | `False` |
| `SECRET_KEY` | *(long random string)* |
| `AUTH_ENABLED` | `True` |
| `AUTH_ADMIN_USERNAME` | `admin` |
| `AUTH_ADMIN_PASSWORD` | *(strong password)* |
| `AUTH_USER_USERNAME` | `user` |
| `AUTH_USER_PASSWORD` | *(strong password)* |

Save → Render redeploys. On startup the app creates tables automatically (`ensure_core_tables`).

**3. Confirm tables**

- Open the site, log in, browse categories.
- Or in Render **Shell**: `python init_schema.py`

**4. Load data (empty tables show blank lists)**

- **Demo data (fast):** Render Shell → `python populate_data.py` → refresh the site.
- **Copy your local MySQL data** (from this PC, using Aiven as remote):

  ```powershell
  $env:REMOTE_DB_HOST="..."
  $env:REMOTE_DB_PORT="..."
  $env:REMOTE_DB_USER="..."
  $env:REMOTE_DB_PASSWORD="..."
  $env:REMOTE_DB_NAME="defaultdb"
  $env:REMOTE_DB_SSL="true"
  python copy_local_to_remote.py
  ```

### Alternative: MySQL as a Render Private Service (paid disk)

No template required:

1. On GitHub: open [render-examples/mysql](https://github.com/render-examples/mysql) → **Use this template** / fork.
2. Render → **New → Private Service** → select that repo → **Docker**.
3. Env: `MYSQL_DATABASE=listmap`, `MYSQL_USER=listmap`, `MYSQL_PASSWORD=…`, `MYSQL_ROOT_PASSWORD=…`
4. **Disk**: mount path `/var/lib/mysql` (required), size ≥ 1 GB.
5. After it is live, copy the **internal hostname** (e.g. `sap-mysql-xxxx`).
6. On the web service set `DB_HOST` to that hostname, `DB_PORT=3306`, matching user/password/`DB_NAME=listmap`. Leave `DB_SSL` unset/false.

### Notes

- If the site loads but every API fails or categories stay broken, `DB_*` is wrong or still pointing at `localhost`.
- Free Render web services **sleep** when idle; first request can take ~30–60s.
- Never use Docker demo passwords (`admin123`) on a public site.

---

## Pre-deployment checklist

- [ ] Set `APP_ENV=production` in `.env`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Set a strong `SECRET_KEY` (32+ random characters)
- [ ] Set a strong `AUTH_PASSWORD`
- [ ] Run database schema: `mysql -u root -p < schema.sql` (or `python init_schema.py`)
- [ ] Install dependencies: `pip install -r requirements.txt`

## Run with Waitress (recommended)

```bash
python run_production.py
```

The app listens on `FLASK_HOST:FLASK_PORT` (default `127.0.0.1:5000`).

For LAN access, set in `.env`:

```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

## Reverse proxy with nginx (HTTPS)

Use nginx in front of Waitress for TLS termination.

**1. Run Waitress on localhost:**

```env
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

**2. Example nginx site config** (`/etc/nginx/sites-available/sap-listmap`):

```nginx
server {
    listen 443 ssl;
    server_name listmap.example.com;

    ssl_certificate     /etc/ssl/certs/listmap.crt;
    ssl_certificate_key /etc/ssl/private/listmap.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name listmap.example.com;
    return 301 https://$host$request_uri;
}
```

**3. Enable and reload:**

```bash
sudo ln -s /etc/nginx/sites-available/sap-listmap /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Windows — run as a background service

**Option A: Task Scheduler**

1. Create a task that runs at startup.
2. Action: `python C:\path\to\SaP\run_production.py`
3. Start in: `C:\path\to\SaP`

**Option B: IIS with HttpPlatformHandler**

1. Install HttpPlatformHandler.
2. Point the site to the SaP folder with a `web.config` that launches `run_production.py`.
3. Bind HTTPS in IIS Manager.

## Run tests before deploy

```bash
pip install -r requirements.txt
pytest
```

## Security notes

- Never expose the app without authentication on a public network.
- Keep MySQL credentials out of version control (`.env` is gitignored).
- Rate limiting is enabled by default (`RATE_LIMIT_ENABLED=True`).
- Sessions expire after 8 hours.
