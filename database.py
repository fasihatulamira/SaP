import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

try:
    # Use connection pool for Flask web application efficiency
    db_pool = pooling.MySQLConnectionPool(
        pool_name="listmap_pool",
        pool_size=5,
        **db_config
    )
except Exception as e:
    print("Error initializing connection pool, falling back to direct connections:", e)
    db_pool = None

def get_connection():
    if db_pool:
        return db_pool.get_connection()
    return mysql.connector.connect(**db_config)

def get_topography_data(search_query=None, release_year=None):
    """
    Fetches records from topography table.
    Filters by search_query (matching sheetNum or sheetName) and release_year if provided.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT sheetNum, sheetName, sheetScale, release_year FROM topography WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (sheetNum LIKE %s OR sheetName LIKE %s)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
        
    if release_year:
        query += " AND release_year = %s"
        params.append(release_year)
        
    query += " ORDER BY sheetNum ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_dted_data(search_query=None, level=None):
    """
    Fetches records from dted table.
    Filters by search_query (matching id_name) and level if provided.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT id_name, level FROM dted WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND id_name LIKE %s"
        params.append(f"%{search_query}%")
        
    if level is not None:
        query += " AND level = %s"
        params.append(level)
        
    query += " ORDER BY id_name ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_landused_data(search_query=None):
    """
    Fetches records from landused table.
    Filters by search_query (matching category) if provided.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT landused_id, category FROM landused WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND category LIKE %s"
        params.append(f"%{search_query}%")
        
    query += " ORDER BY landused_id ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_filter_options():
    """
    Returns unique values from the database to populate frontend dropdown filters dynamically.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get distinct release years
    cursor.execute("SELECT DISTINCT release_year FROM topography ORDER BY release_year DESC")
    years = [row[0] for row in cursor.fetchall() if row[0] is not None]
    
    # Get distinct DTED levels
    cursor.execute("SELECT DISTINCT level FROM dted ORDER BY level ASC")
    levels = [row[0] for row in cursor.fetchall() if row[0] is not None]
    
    cursor.close()
    conn.close()
    
    return {
        "release_years": years,
        "dted_levels": levels
    }
