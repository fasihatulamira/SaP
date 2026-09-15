"""Seed LISTMAP tables when empty. Safe to re-run (skips non-empty tables).

Uses the configured PostgreSQL / Supabase connection from DATABASE_URL or DB_*.
"""
import sys

from dotenv import load_dotenv

load_dotenv()

import database  # noqa: E402  — after dotenv

LANDUSE_SEED_DATA = [
    (1, "HUTAN"),
    (2, "PERTANIAN"),
    (3, "PDG.TERNAK & RUMPUT"),
    (4, "PERBANDARAN"),
    (5, "KAW.DIBERSIHKAN"),
    (6, "TIDAK DIUSAHAKAN"),
    (7, "PAYA"),
    (8, "PERLOMBONGAN"),
    (9, "AIR"),
    (10, "KAW.DIBERSIKAN"),
    (11, "KAW.PERBANDARAN"),
    (12, "LAIN-LAIN"),
    (13, "TIDAK DI USAHAKAN"),
]

TOPOGRAPHY_SEED_DATA = [
    ("AP24", "MERLIMAU", "1:50000", 2017),
    ("AP25", "JASIN", "1:50000", 2017),
    ("AP26", "MELAKA", "1:50000", 2018),
    ("BN12", "KLANG", "1:50000", 2019),
    ("BN13", "SHAH ALAM", "1:50000", 2019),
    ("CN01", "IPOH", "1:50000", 2016),
    ("DN05", "GEORGE TOWN", "1:50000", 2020),
    ("EN08", "KUANTAN", "1:50000", 2018),
]

DTED_SEED_DATA = [
    ("n02_e101", 1),
    ("n02_e102", 1),
    ("n03_e101", 2),
    ("n03_e102", 2),
    ("n04_e100", 1),
    ("n04_e101", 2),
    ("n05_e101", 3),
]

SJUNG_SEED_DATA = [
    ("SJ01", "SUNGAI BULOH", "1:25000"),
    ("SJ02", "RAWANG", "1:25000"),
]


def _count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row = cursor.fetchone()
    return row[0] if row else 0


def populate_database():
    database.ensure_core_tables()
    with database.get_db_cursor(commit=True) as cursor:
        if _count(cursor, "landused") == 0:
            cursor.executemany(
                "INSERT INTO landused (landused_id, category) VALUES (%s, %s)",
                LANDUSE_SEED_DATA,
            )
            print(f"Inserted {len(LANDUSE_SEED_DATA)} landused rows.")
        else:
            print("landused already has data — skip.")

        if _count(cursor, "topography") == 0:
            cursor.executemany(
                'INSERT INTO topography ("sheetNum", "sheetName", "sheetScale", release_year) '
                "VALUES (%s, %s, %s, %s)",
                TOPOGRAPHY_SEED_DATA,
            )
            print(f"Inserted {len(TOPOGRAPHY_SEED_DATA)} topography rows.")
        else:
            print("topography already has data — skip.")

        if _count(cursor, "dted") == 0:
            cursor.executemany(
                "INSERT INTO dted (id_name, level) VALUES (%s, %s)",
                DTED_SEED_DATA,
            )
            print(f"Inserted {len(DTED_SEED_DATA)} dted rows.")
        else:
            print("dted already has data — skip.")

        if _count(cursor, "sjung") == 0:
            cursor.executemany(
                'INSERT INTO sjung ("sheetNum", "sheetName", "sheetScale") VALUES (%s, %s, %s)',
                SJUNG_SEED_DATA,
            )
            print(f"Inserted {len(SJUNG_SEED_DATA)} sjung rows.")
        else:
            print("sjung already has data — skip.")

    print("Seed complete.")


if __name__ == "__main__":
    try:
        populate_database()
    except Exception as exc:
        print(f"Database population error: {exc}", file=sys.stderr)
        sys.exit(1)
