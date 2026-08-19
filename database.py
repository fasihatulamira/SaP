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


def _require_non_empty_str(value, field_name):
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} is required.")
    return str(value).strip()


def _require_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid integer.")


def create_topography_record(sheet_num, sheet_name, sheet_scale, release_year):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    sheet_name = _require_non_empty_str(sheet_name, "sheetName")
    sheet_scale = _require_non_empty_str(sheet_scale, "sheetScale")
    release_year = _require_int(release_year, "release_year")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO topography (sheetNum, sheetName, sheetScale, release_year) VALUES (%s, %s, %s, %s)",
            (sheet_num, sheet_name, sheet_scale, release_year),
        )


def update_topography_record(sheet_num, sheet_name, sheet_scale, release_year):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    sheet_name = _require_non_empty_str(sheet_name, "sheetName")
    sheet_scale = _require_non_empty_str(sheet_scale, "sheetScale")
    release_year = _require_int(release_year, "release_year")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE topography SET sheetName=%s, sheetScale=%s, release_year=%s WHERE sheetNum=%s",
            (sheet_name, sheet_scale, release_year, sheet_num),
        )
        return cursor.rowcount > 0


def delete_topography_record(sheet_num):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM topography WHERE sheetNum=%s", (sheet_num,))
        return cursor.rowcount > 0


def create_dted_record(id_name, level):
    id_name = _require_non_empty_str(id_name, "id_name")
    level = _require_int(level, "level")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO dted (id_name, level) VALUES (%s, %s)",
            (id_name, level),
        )


def update_dted_record(id_name, level):
    id_name = _require_non_empty_str(id_name, "id_name")
    level = _require_int(level, "level")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE dted SET level=%s WHERE id_name=%s",
            (level, id_name),
        )
        return cursor.rowcount > 0


def delete_dted_record(id_name):
    id_name = _require_non_empty_str(id_name, "id_name")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM dted WHERE id_name=%s", (id_name,))
        return cursor.rowcount > 0


def create_landused_record(category, landused_id=None):
    category = _require_non_empty_str(category, "category")
    with get_db_cursor(commit=True) as cursor:
        if landused_id is not None and str(landused_id).strip() != "":
            landused_id = _require_int(landused_id, "landused_id")
            cursor.execute(
                "INSERT INTO landused (landused_id, category) VALUES (%s, %s)",
                (landused_id, category),
            )
            return landused_id
        cursor.execute(
            "INSERT INTO landused (category) VALUES (%s)",
            (category,),
        )
        return cursor.lastrowid


def update_landused_record(landused_id, category):
    landused_id = _require_int(landused_id, "landused_id")
    category = _require_non_empty_str(category, "category")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE landused SET category=%s WHERE landused_id=%s",
            (category, landused_id),
        )
        return cursor.rowcount > 0


def delete_landused_record(landused_id):
    landused_id = _require_int(landused_id, "landused_id")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM landused WHERE landused_id=%s", (landused_id,))
        return cursor.rowcount > 0


def create_sjungu_record(sheet_num, sheet_name, sheet_scale):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    sheet_name = _require_non_empty_str(sheet_name, "sheetName")
    sheet_scale = _require_non_empty_str(sheet_scale, "sheetScale")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO sjung (sheetNum, sheetName, sheetScale) VALUES (%s, %s, %s)",
            (sheet_num, sheet_name, sheet_scale),
        )


def update_sjungu_record(sheet_num, sheet_name, sheet_scale):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    sheet_name = _require_non_empty_str(sheet_name, "sheetName")
    sheet_scale = _require_non_empty_str(sheet_scale, "sheetScale")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE sjung SET sheetName=%s, sheetScale=%s WHERE sheetNum=%s",
            (sheet_name, sheet_scale, sheet_num),
        )
        return cursor.rowcount > 0


def delete_sjungu_record(sheet_num):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM sjung WHERE sheetNum=%s", (sheet_num,))
        return cursor.rowcount > 0


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


def ensure_audit_document_table():
    """Create audit_document table when missing (safe for existing databases)."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_document (
              id           INT          NOT NULL AUTO_INCREMENT,
              audit_id     INT          NOT NULL,
              filename     VARCHAR(255) NOT NULL,
              mime_type    VARCHAR(100) NOT NULL,
              file_size    INT          NOT NULL,
              file_data    LONGBLOB     NOT NULL,
              created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (id),
              UNIQUE KEY uq_audit_document_audit_id (audit_id),
              CONSTRAINT fk_audit_document_audit
                FOREIGN KEY (audit_id) REFERENCES audit_log(id)
                ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """
        )


def insert_audit_log(username, role, action, report_ref=None, item_count=0, details=None):
    """Insert a row into the audit_log table and return its id."""
    details_json = json.dumps(details) if details is not None else None
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO audit_log (username, role, action, report_ref, item_count, details)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (username, role, action, report_ref, item_count, details_json),
        )
        return cursor.lastrowid


def insert_audit_document(audit_id, filename, mime_type, file_data):
    """Store an archived document linked to an audit_log row."""
    audit_id = int(audit_id)
    filename = _require_non_empty_str(filename, "filename")
    mime_type = _require_non_empty_str(mime_type, "mime_type")
    if file_data is None:
        raise ValueError("file_data is required.")
    file_size = len(file_data)
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO audit_document (audit_id, filename, mime_type, file_size, file_data)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (audit_id, filename, mime_type, file_size, file_data),
        )
        return cursor.lastrowid


def get_audit_document(audit_id):
    """Return archived document metadata + bytes for an audit entry, or None."""
    audit_id = int(audit_id)
    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT id, audit_id, filename, mime_type, file_size, file_data, created_at
            FROM audit_document
            WHERE audit_id = %s
            """,
            (audit_id,),
        )
        row = cursor.fetchone()
    if not row:
        return None
    if row.get("created_at") is not None:
        row["created_at"] = row["created_at"].isoformat(sep=" ", timespec="seconds")
    return row


def get_audit_logs(limit=50):
    """Return recent audit log entries (newest first), excluding sign-in/sign-out."""
    limit = min(max(1, int(limit)), 200)
    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
              a.id, a.username, a.role, a.action, a.report_ref, a.item_count,
              a.details, a.created_at,
              (d.id IS NOT NULL) AS has_document,
              d.filename AS document_filename,
              d.mime_type AS document_mime_type
            FROM audit_log a
            LEFT JOIN audit_document d ON d.audit_id = a.id
            WHERE a.action NOT IN ('login', 'logout')
            ORDER BY a.created_at DESC
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
        row["has_document"] = bool(row.get("has_document"))
    return rows
