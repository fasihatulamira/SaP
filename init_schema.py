"""Apply schema.sql to the configured MySQL database (one-time / upgrade)."""
import os
import sys

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def main():
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "listmap")

    if not user or password is None:
        print("Set DB_USER and DB_PASSWORD (and usually DB_HOST / DB_NAME).", file=sys.stderr)
        sys.exit(1)

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        sql = f.read()

    # Connect without a default DB so CREATE DATABASE works
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        allow_local_infile=True,
    )
    try:
        cursor = conn.cursor()
        for result in cursor.execute(sql, multi=True):
            if result.with_rows:
                result.fetchall()
        conn.commit()
        print(f"Schema applied on {host}:{port} (database={database}).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
