import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Standard Malaysian land-use categories (matches production listmap data)
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

def populate_database():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM landused")
        cnt = cursor.fetchone()[0]

        if cnt == 0:
            print("landused table is empty. Populating seed categories...")
            cursor.executemany(
                "INSERT INTO landused (landused_id, category) VALUES (%s, %s)",
                LANDUSE_SEED_DATA
            )
            conn.commit()
            print(f"Successfully inserted {len(LANDUSE_SEED_DATA)} records into landused table.")
        else:
            print(f"landused table already contains {cnt} records. Skipping population.")

        conn.close()
    except Exception as e:
        print("Database population error:", e)

if __name__ == "__main__":
    populate_database()
