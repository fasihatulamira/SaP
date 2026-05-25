import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        
        # Check if landused table is empty
        cursor.execute("SELECT COUNT(*) FROM landused")
        cnt = cursor.fetchone()[0]
        
        if cnt == 0:
            print("landused table is empty. Populating mock categories...")
            mock_landuse = [
                (1, "Agriculture (Paddy, Palm Oil, Rubber)"),
                (2, "Primary & Secondary Forest (Jungle, Reserves)"),
                (3, "Residential Zone (Terraces, Apartments, Villages)"),
                (4, "Commercial & Retail (Malls, Business Districts)"),
                (5, "Industrial Area (Factories, Warehouses, Logistical Centers)"),
                (6, "Water Bodies (Rivers, Lakes, Wetland, Reservoirs)"),
                (7, "Recreational Parks (Open Spaces, Sports Complex, Gardens)"),
                (8, "Infrastructure & Utilities (Substations, Treatment Plants)")
            ]
            
            cursor.executemany(
                "INSERT INTO landused (landused_id, category) VALUES (%s, %s)",
                mock_landuse
            )
            conn.commit()
            print(f"Successfully inserted {len(mock_landuse)} records into landused table.")
        else:
            print(f"landused table already contains {cnt} records. Skipping population.")
            
        conn.close()
    except Exception as e:
        print("Database population error:", e)

if __name__ == "__main__":
    populate_database()
