"""
Copy LISTMAP rows from your local MySQL (.env) to a remote DB (Aiven / Render).

Usage (PowerShell), from the project folder:

  $env:REMOTE_DB_HOST="your-aiven-host"
  $env:REMOTE_DB_PORT="12345"
  $env:REMOTE_DB_USER="avnadmin"
  $env:REMOTE_DB_PASSWORD="..."
  $env:REMOTE_DB_NAME="defaultdb"
  $env:REMOTE_DB_SSL="true"
  python copy_local_to_remote.py

Does not print passwords. Skips tables that already have remote rows unless --force.
"""
import argparse
import os
import sys

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

TABLES = {
    "topography": ("sheetNum, sheetName, sheetScale, release_year", "%s, %s, %s, %s"),
    "dted": ("id_name, level", "%s, %s"),
    "landused": ("landused_id, category", "%s, %s"),
    "sjung": ("sheetNum, sheetName, sheetScale", "%s, %s, %s"),
}


def _connect(prefix=""):
    """prefix '' uses DB_*; prefix 'REMOTE_' uses REMOTE_DB_*."""
    p = prefix
    host_key = f"{p}DB_HOST" if p else "DB_HOST"
    cfg = {
        "host": os.getenv(host_key, "localhost" if not p else None),
        "port": int(os.getenv(f"{p}DB_PORT", "3306")),
        "user": os.getenv(f"{p}DB_USER"),
        "password": os.getenv(f"{p}DB_PASSWORD"),
        "database": os.getenv(f"{p}DB_NAME"),
    }
    if not all([cfg["host"], cfg["user"], cfg["password"] is not None, cfg["database"]]):
        raise SystemExit(f"Missing connection settings for prefix {p!r}")
    ssl_key = f"{p}DB_SSL" if p else "DB_SSL"
    if os.getenv(ssl_key, "").lower() in ("true", "1", "t", "y", "yes"):
        cfg["ssl_disabled"] = False
    return mysql.connector.connect(**cfg)


def main():
    parser = argparse.ArgumentParser(description="Copy local LISTMAP data to remote MySQL")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace remote rows even when the remote table is not empty",
    )
    args = parser.parse_args()

    local = _connect("")
    remote = _connect("REMOTE_")
    lcur = local.cursor()
    rcur = remote.cursor()

    try:
        for table, (cols, placeholders) in TABLES.items():
            lcur.execute(f"SELECT {cols} FROM {table}")
            rows = lcur.fetchall()
            rcur.execute(f"SELECT COUNT(*) FROM {table}")
            remote_count = rcur.fetchone()[0]

            if remote_count and not args.force:
                print(f"{table}: remote has {remote_count} rows — skip (use --force to replace)")
                continue

            if args.force and remote_count:
                rcur.execute(f"DELETE FROM {table}")
                print(f"{table}: cleared {remote_count} remote rows")

            if not rows:
                print(f"{table}: local empty — nothing to copy")
                continue

            rcur.executemany(
                f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                rows,
            )
            print(f"{table}: copied {len(rows)} rows")

        remote.commit()
        print("Done.")
    finally:
        lcur.close()
        rcur.close()
        local.close()
        remote.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Copy failed: {exc}", file=sys.stderr)
        sys.exit(1)
