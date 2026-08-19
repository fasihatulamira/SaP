# SaP LISTMAP — Production Deployment Guide

## Deploy on Render (public URL)

Requires a GitHub push of this repo (already at `fasihatulamira/SaP`).

### A. MySQL (private service)

1. Open [https://dashboard.render.com](https://dashboard.render.com) and sign in with GitHub.
2. **New → Private Service** (or use the [MySQL template](https://render.com/templates/mysql)).
3. Use image/repo: [render-examples/mysql](https://github.com/render-examples/mysql) (MySQL 8).
4. Environment:

   | Key | Value |
   |-----|--------|
   | `MYSQL_DATABASE` | `listmap` |
   | `MYSQL_USER` | `listmap` |
   | `MYSQL_PASSWORD` | *(strong password)* |
   | `MYSQL_ROOT_PASSWORD` | *(strong password)* |

5. Under **Disk**: mount path `/var/lib/mysql`, size ≥ 1 GB.
6. After deploy, copy the **internal hostname** (looks like `sap-mysql-xxxx` — use port `3306`).

### B. Web service

1. **New → Blueprint** and select this repo (uses `render.yaml`), **or** **New → Web Service** → `SaP`.
2. If manual Web Service:
   - **Runtime:** Python 3
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `python run_production.py`
3. Set environment variables (Blueprint prompts for `sync: false` ones):

   | Key | Value |
   |-----|--------|
   | `APP_ENV` | `production` |
   | `FLASK_HOST` | `0.0.0.0` |
   | `FLASK_DEBUG` | `False` |
   | `SECRET_KEY` | *(auto or long random string)* |
   | `DB_HOST` | *(MySQL internal hostname from A)* |
   | `DB_PORT` | `3306` |
   | `DB_USER` | `listmap` (or root) |
   | `DB_PASSWORD` | *(same as MySQL)* |
   | `DB_NAME` | `listmap` |
   | `AUTH_ENABLED` | `True` |
   | `AUTH_ADMIN_USERNAME` | `admin` |
   | `AUTH_ADMIN_PASSWORD` | *(strong password)* |
   | `AUTH_USER_USERNAME` | `user` |
   | `AUTH_USER_PASSWORD` | *(strong password)* |

4. Deploy. Public URL: `https://sap-listmap.onrender.com` (or the name Render assigns).

### C. Apply database schema (once)

From your PC (with network access to MySQL — only works if MySQL is reachable; private Render MySQL is **not** reachable from your PC):

Use **Render Shell** on the web service after deploy:

```bash
python init_schema.py
```

Or open a one-off job / shell with the same env vars and run that command. `init_schema.py` runs `schema.sql` via MySQL connector.

### Notes

- Free web services **sleep** after idle time; first request after sleep can take ~30–60s.
- MySQL private service and disks are usually **paid** on Render — check current pricing.
- Never use the Docker demo passwords (`admin123`) on a public site.

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
