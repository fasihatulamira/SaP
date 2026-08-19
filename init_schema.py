"""Apply core tables to the configured MySQL database (one-time / upgrade)."""
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
            "Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME "
            "(set DB_SSL=true for Aiven / other managed MySQL).",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"Schema OK on {database.db_config.get('host')}:{database.db_config.get('port')} "
        f"database={database.db_config.get('database')}"
    )


if __name__ == "__main__":
    main()
