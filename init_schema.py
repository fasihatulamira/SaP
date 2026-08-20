"""Apply core tables to the configured PostgreSQL database (one-time / upgrade)."""
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")

import database  # noqa: E402  — after dotenv


def main():
    try:
        database.ensure_core_tables()
    except Exception as exc:
        print(f"Schema apply failed: {exc}", file=sys.stderr)
        print(
            "Check DATABASE_URL or DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME "
            "(set DB_SSL=true or use ?sslmode=require for Supabase).",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"Schema OK on {database.db_config.get('host')}:{database.db_config.get('port')} "
        f"database={database.db_config.get('database')}"
    )


if __name__ == "__main__":
    main()
