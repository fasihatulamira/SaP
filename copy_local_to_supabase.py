"""
Copy LISTMAP rows from local MySQL (.env) to Supabase / PostgreSQL (DATABASE_URL).

Usage (PowerShell), from the project folder:

  $env:DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
  python copy_local_to_supabase.py

Optional: --force to overwrite tables that already have rows.
Does not print passwords.
"""
import argparse
import os
import sys

import mysql.connector
import psycopg2
from dotenv import load_dotenv

load_dotenv()

GIS_TABLES = {
    "topography": (
        '"sheetNum", "sheetName", "sheetScale", release_year',
        "sheetNum, sheetName, sheetScale, release_year",
        "%s, %s, %s, %s",
    ),
    "dted": (
        "id_name, level",
        "id_name, level",
        "%s, %s",
    ),
    "landused": (
        "landused_id, category",
        "landused_id, category",
        "%s, %s",
    ),
    "sjung": (
        '"sheetNum", "sheetName", "sheetScale"',
        "sheetNum, sheetName, sheetScale",
        "%s, %s, %s",
    ),
}

SERIAL_TABLES = ("landused", "audit_log", "audit_document")


def _mysql_connect():
    cfg = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }
    if not all([cfg["user"], cfg["password"] is not None, cfg["database"]]):
        raise SystemExit("Set DB_HOST, DB_USER, DB_PASSWORD, DB_NAME for local MySQL.")
    if os.getenv("DB_SSL", "").lower() in ("true", "1", "t", "y", "yes"):
        cfg["ssl_disabled"] = False
    return mysql.connector.connect(**cfg)


def _pg_connect():
    url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if not url:
        raise SystemExit("Set DATABASE_URL (Supabase connection string).")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return psycopg2.connect(url)


def _count(cur, table, quoted=False):
    name = f'"{table}"' if quoted else table
    cur.execute(f"SELECT COUNT(*) FROM {name}")
    return cur.fetchone()[0]


def _copy_table(mysql_cur, pg_cur, table, pg_cols, mysql_cols, placeholders, force):
    pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
    remote_count = pg_cur.fetchone()[0]
    if remote_count and not force:
        print(f"  skip {table} ({remote_count} rows already on Supabase; use --force)")
        return 0

    pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY")

    mysql_cur.execute(f"SELECT {mysql_cols} FROM {table}")
    rows = mysql_cur.fetchall()
    if not rows:
        print(f"  {table}: 0 rows")
        return 0

    insert_sql = f"INSERT INTO {table} ({pg_cols}) VALUES ({placeholders})"
    for row in rows:
        pg_cur.execute(insert_sql, row)
    print(f"  {table}: copied {len(rows)} rows")
    return len(rows)


def _copy_audit_log(mysql_cur, pg_cur, force):
    pg_cur.execute("SELECT COUNT(*) FROM audit_log")
    if pg_cur.fetchone()[0] and not force:
        print("  skip audit_log (rows exist; use --force)")
        return False
    pg_cur.execute("TRUNCATE TABLE audit_document RESTART IDENTITY CASCADE")
    pg_cur.execute("TRUNCATE TABLE audit_log RESTART IDENTITY CASCADE")

    mysql_cur.execute(
        "SELECT id, username, role, action, report_ref, item_count, details, created_at "
        "FROM audit_log"
    )
    rows = mysql_cur.fetchall()
    for row in rows:
        details = row[6]
        if details is not None and not isinstance(details, str):
            import json

            details = json.dumps(details)
        pg_cur.execute(
            """
            INSERT INTO audit_log (id, username, role, action, report_ref, item_count, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            """,
            (row[0], row[1], row[2], row[3], row[4], row[5], details, row[7]),
        )
    print(f"  audit_log: copied {len(rows)} rows")
    return True


def _copy_audit_document(mysql_cur, pg_cur):
    mysql_cur.execute(
        "SELECT id, audit_id, filename, mime_type, file_size, file_data, created_at "
        "FROM audit_document"
    )
    rows = mysql_cur.fetchall()
    for row in rows:
        pg_cur.execute(
            """
            INSERT INTO audit_document (id, audit_id, filename, mime_type, file_size, file_data, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (row[0], row[1], row[2], row[3], row[4], psycopg2.Binary(row[5]), row[6]),
        )
    print(f"  audit_document: copied {len(rows)} rows")


def _reset_sequences(pg_cur):
    for table, column in (
        ("landused", "landused_id"),
        ("audit_log", "id"),
        ("audit_document", "id"),
    ):
        pg_cur.execute(
            f"""
            SELECT setval(
              pg_get_serial_sequence('{table}', '{column}'),
              GREATEST(COALESCE((SELECT MAX({column}) FROM {table}), 1), 1)
            )
            """
        )


def main():
    parser = argparse.ArgumentParser(description="Copy local MySQL listmap data to Supabase.")
    parser.add_argument("--force", action="store_true", help="Overwrite remote tables that already have rows")
    args = parser.parse_args()

    mysql_conn = _mysql_connect()
    pg_conn = _pg_connect()
    mysql_cur = mysql_conn.cursor()
    pg_cur = pg_conn.cursor()

    try:
        import database

        database.ensure_core_tables()
        print("Supabase schema OK.")
        print("Copying GIS tables...")
        for table, (pg_cols, mysql_cols, placeholders) in GIS_TABLES.items():
            _copy_table(mysql_cur, pg_cur, table, pg_cols, mysql_cols, placeholders, args.force)

        print("Copying audit tables...")
        if _copy_audit_log(mysql_cur, pg_cur, args.force):
            _copy_audit_document(mysql_cur, pg_cur)
        _reset_sequences(pg_cur)
        pg_conn.commit()
        print("Done.")
    except Exception as exc:
        pg_conn.rollback()
        print(f"Copy failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        mysql_cur.close()
        pg_cur.close()
        mysql_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
