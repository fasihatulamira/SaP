# SaP LISTMAP — Production Deployment Guide

## Pre-deployment checklist

- [ ] Set `APP_ENV=production` in `.env`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Set a strong `SECRET_KEY` (32+ random characters)
- [ ] Set a strong `AUTH_PASSWORD`
- [ ] Run database schema: `mysql -u root -p < schema.sql`
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
