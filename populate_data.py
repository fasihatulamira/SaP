"""Seed LISTMAP tables when empty. Safe to re-run (skips non-empty tables)."""
import os
import sys

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

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


def _connect():
    cfg = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }
    if not cfg["user"] or cfg["password"] is None or not cfg["database"]:
        raise SystemExit("Set DB_HOST, DB_USER, DB_PASSWORD, and DB_NAME.")
    if os.getenv("DB_SSL", "").lower() in ("true", "1", "t", "y", "yes"):
        cfg["ssl_disabled"] = False
    return mysql.connector.connect(**cfg)


def _count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]


def populate_database():
    conn = _connect()
    cursor = conn.cursor()
    try:
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
                "INSERT INTO topography (sheetNum, sheetName, sheetScale, release_year) "
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
                "INSERT INTO sjung (sheetNum, sheetName, sheetScale) VALUES (%s, %s, %s)",
                SJUNG_SEED_DATA,
            )
            print(f"Inserted {len(SJUNG_SEED_DATA)} sjung rows.")
        else:
            print("sjung already has data — skip.")

        conn.commit()
        print("Seed complete.")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        populate_database()
    except Exception as exc:
        print(f"Database population error: {exc}", file=sys.stderr)
        sys.exit(1)
