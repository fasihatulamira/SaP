import json
import os
from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DEFAULT_LIMIT = 10
MAX_LIMIT = 100

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

try:
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

@contextmanager
def get_db_cursor(dictionary=False, commit=False):
    """Yield a cursor and always close cursor + connection."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def _clamp_pagination(page, limit):
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1
    try:
        limit = min(MAX_LIMIT, max(1, int(limit)))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT
    return page, limit

def _paginated_result(items, total, page, limit):
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": max(1, (total + limit - 1) // limit) if total else 1,
    }

def get_topography_data(search_query=None, release_year=None, page=1, limit=DEFAULT_LIMIT):
    """
    Fetches paginated records from topography table.
    Filters by search_query (sheetNum or sheetName) and release_year if provided.
    """
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += " AND (sheetNum LIKE %s OR sheetName LIKE %s)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")

    if release_year:
        where += " AND release_year = %s"
        params.append(release_year)

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM topography WHERE 1=1{where}", params)
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * limit
        cursor.execute(
            f"SELECT sheetNum, sheetName, sheetScale, release_year "
            f"FROM topography WHERE 1=1{where} ORDER BY sheetNum ASC LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        rows = cursor.fetchall()

    return _paginated_result(rows, total, page, limit)

def get_dted_data(search_query=None, level=None, page=1, limit=DEFAULT_LIMIT):
    """
    Fetches paginated records from dted table.
    Filters by search_query (id_name) and level if provided.
    """
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += " AND id_name LIKE %s"
        params.append(f"%{search_query}%")

    if level is not None:
        where += " AND level = %s"
        params.append(level)

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM dted WHERE 1=1{where}", params)
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * limit
        cursor.execute(
            f"SELECT id_name, level FROM dted WHERE 1=1{where} "
            f"ORDER BY id_name ASC LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        rows = cursor.fetchall()

    return _paginated_result(rows, total, page, limit)

def get_landused_data(search_query=None, page=1, limit=DEFAULT_LIMIT):
    """
    Fetches paginated records from landused table.
    Filters by search_query (category) if provided.
    """
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += " AND category LIKE %s"
        params.append(f"%{search_query}%")

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM landused WHERE 1=1{where}", params)
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * limit
        cursor.execute(
            f"SELECT landused_id, category FROM landused WHERE 1=1{where} "
            f"ORDER BY landused_id ASC LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        rows = cursor.fetchall()

    return _paginated_result(rows, total, page, limit)

def get_sjungu_data(search_query=None, page=1, limit=DEFAULT_LIMIT):
    """
    Fetches paginated records from sjung table.
    Filters by search_query (sheetNum or sheetName) if provided.
    """
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += " AND (sheetNum LIKE %s OR sheetName LIKE %s)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM sjung WHERE 1=1{where}", params)
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * limit
        cursor.execute(
            f"SELECT sheetNum, sheetName, sheetScale FROM sjung WHERE 1=1{where} "
            f"ORDER BY sheetNum ASC LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        rows = cursor.fetchall()

    return _paginated_result(rows, total, page, limit)

def get_filter_options():
    """
    Returns unique values from the database to populate frontend dropdown filters dynamically.
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT release_year FROM topography ORDER BY release_year DESC")
        years = [row[0] for row in cursor.fetchall() if row[0] is not None]

        cursor.execute("SELECT DISTINCT level FROM dted ORDER BY level ASC")
        levels = [row[0] for row in cursor.fetchall() if row[0] is not None]

    return {
        "release_years": years,
        "dted_levels": levels
    }


def ensure_audit_log_table():
    """Create audit_log table when missing (safe for existing databases)."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
              id          INT          NOT NULL AUTO_INCREMENT,
              username    VARCHAR(100) NOT NULL,
              role        VARCHAR(20)  NOT NULL,
              action      VARCHAR(50)  NOT NULL,
              report_ref  VARCHAR(50)  NULL,
              item_count  INT          NOT NULL DEFAULT 0,
              details     JSON         NULL,
              created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (id),
              INDEX idx_audit_created (created_at DESC),
              INDEX idx_audit_username (username),
              INDEX idx_audit_action (action)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """
        )


def insert_audit_log(username, role, action, report_ref=None, item_count=0, details=None):
    """Insert a row into the audit_log table."""
    details_json = json.dumps(details) if details is not None else None
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO audit_log (username, role, action, report_ref, item_count, details)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (username, role, action, report_ref, item_count, details_json),
        )


def get_audit_logs(limit=50):
    """Return recent audit log entries (newest first), excluding sign-in/sign-out."""
    limit = min(max(1, int(limit)), 200)
    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT id, username, role, action, report_ref, item_count, details, created_at
            FROM audit_log
            WHERE action NOT IN ('login', 'logout')
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
    for row in rows:
        if isinstance(row.get("details"), str):
            try:
                row["details"] = json.loads(row["details"])
            except json.JSONDecodeError:
                pass
        if row.get("created_at") is not None:
            row["created_at"] = row["created_at"].isoformat(sep=" ", timespec="seconds")
    return rows
