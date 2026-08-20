import json
import os
import time
from contextlib import contextmanager

import psycopg2
from psycopg2 import Error as PGError
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DEFAULT_LIMIT = 10
MAX_LIMIT = 100
_CONNECT_RETRIES = 4
_CONNECT_RETRY_SLEEP_SEC = 2.0
_schema_ready = False


def _env_truthy(name, default=""):
    return os.getenv(name, default).lower() in ("true", "1", "t", "y", "yes")


def _normalize_database_url(url):
    if not url:
        return url
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def _build_db_config():
    """Build psycopg2 connection kwargs from DATABASE_URL or DB_* env vars."""
    database_url = _normalize_database_url(
        os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    )
    if database_url:
        return {
            "dsn": database_url,
            "host": None,
            "port": None,
            "database": None,
            "user_set": True,
            "password_set": True,
            "ssl": "sslmode=" in database_url.lower() or "supabase" in database_url.lower(),
        }

    host = (os.getenv("DB_HOST") or "localhost").strip()
    auto_ssl = "supabase.co" in host.lower() or _env_truthy("DB_SSL")
    return {
        "dsn": None,
        "host": host,
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME", "postgres"),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "60")),
        "sslmode": "require" if auto_ssl else "prefer",
        "user_set": bool(os.getenv("DB_USER")),
        "password_set": os.getenv("DB_PASSWORD") is not None and os.getenv("DB_PASSWORD") != "",
        "ssl": auto_ssl,
    }


db_config = _build_db_config()


def db_status():
    """Safe connection diagnostics for health checks (no secrets)."""
    return {
        "backend": "postgresql",
        "host": db_config.get("host") or "(DATABASE_URL)",
        "port": db_config.get("port"),
        "database": db_config.get("database") or "(from DATABASE_URL)",
        "user_set": db_config.get("user_set"),
        "password_set": db_config.get("password_set"),
        "ssl": db_config.get("ssl"),
        "schema_ready": _schema_ready,
    }


def get_connection():
    """Return a live PostgreSQL connection, retrying for cold managed DBs."""
    last_error = None
    for attempt in range(1, _CONNECT_RETRIES + 1):
        try:
            if db_config.get("dsn"):
                conn = psycopg2.connect(db_config["dsn"])
            else:
                conn = psycopg2.connect(
                    host=db_config["host"],
                    port=db_config["port"],
                    user=db_config["user"],
                    password=db_config["password"],
                    dbname=db_config["database"],
                    connect_timeout=db_config["connect_timeout"],
                    sslmode=db_config["sslmode"],
                )
            conn.autocommit = False
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return conn
        except Exception as exc:
            last_error = exc
            print(f"DB connect attempt {attempt}/{_CONNECT_RETRIES} failed: {exc}")
            if attempt < _CONNECT_RETRIES:
                time.sleep(_CONNECT_RETRY_SLEEP_SEC * attempt)
    raise PGError(f"Unable to connect to PostgreSQL after {_CONNECT_RETRIES} attempts: {last_error}")


@contextmanager
def get_db_cursor(dictionary=False, commit=False):
    """Yield a cursor and always close cursor + connection."""
    conn = get_connection()
    cursor_factory = RealDictCursor if dictionary else None
    cursor = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            cursor.close()
        finally:
            conn.close()


def _core_tables_present():
    """True when the primary LISTMAP table already exists (managed Supabase)."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'topography'
            LIMIT 1
            """
        )
        return cursor.fetchone() is not None


def ensure_schema_ready():
    """Create tables once per process; safe to call on every request."""
    global _schema_ready
    if _schema_ready:
        return
    if _core_tables_present():
        _schema_ready = True
        return
    try:
        ensure_core_tables()
    except Exception as exc:
        # Managed Postgres roles (e.g. Supabase app user) may lack CREATE on public.
        if _core_tables_present():
            _schema_ready = True
            return
        raise exc
    _schema_ready = True


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
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += ' AND ("sheetNum" ILIKE %s OR "sheetName" ILIKE %s)'
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if release_year:
        where += " AND release_year = %s"
        params.append(release_year)

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM topography WHERE 1=1{where}", params)
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * limit
        cursor.execute(
            f'SELECT "sheetNum", "sheetName", "sheetScale", release_year '
            f"FROM topography WHERE 1=1{where} ORDER BY \"sheetNum\" ASC LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        rows = cursor.fetchall()

    return _paginated_result(rows, total, page, limit)


def get_dted_data(search_query=None, level=None, page=1, limit=DEFAULT_LIMIT):
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += " AND id_name ILIKE %s"
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
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += " AND category ILIKE %s"
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
    page, limit = _clamp_pagination(page, limit)
    where = ""
    params = []

    if search_query:
        where += ' AND ("sheetNum" ILIKE %s OR "sheetName" ILIKE %s)'
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM sjung WHERE 1=1{where}", params)
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * limit
        cursor.execute(
            f'SELECT "sheetNum", "sheetName", "sheetScale" FROM sjung WHERE 1=1{where} '
            f'ORDER BY "sheetNum" ASC LIMIT %s OFFSET %s',
            params + [limit, offset],
        )
        rows = cursor.fetchall()

    return _paginated_result(rows, total, page, limit)


def get_filter_options():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT release_year FROM topography ORDER BY release_year DESC")
        years = [row[0] for row in cursor.fetchall() if row[0] is not None]

        cursor.execute("SELECT DISTINCT level FROM dted ORDER BY level ASC")
        levels = [row[0] for row in cursor.fetchall() if row[0] is not None]

    return {
        "release_years": years,
        "dted_levels": levels,
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
            'INSERT INTO topography ("sheetNum", "sheetName", "sheetScale", release_year) '
            "VALUES (%s, %s, %s, %s)",
            (sheet_num, sheet_name, sheet_scale, release_year),
        )


def update_topography_record(sheet_num, sheet_name, sheet_scale, release_year):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    sheet_name = _require_non_empty_str(sheet_name, "sheetName")
    sheet_scale = _require_non_empty_str(sheet_scale, "sheetScale")
    release_year = _require_int(release_year, "release_year")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            'UPDATE topography SET "sheetName"=%s, "sheetScale"=%s, release_year=%s WHERE "sheetNum"=%s',
            (sheet_name, sheet_scale, release_year, sheet_num),
        )
        return cursor.rowcount > 0


def delete_topography_record(sheet_num):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute('DELETE FROM topography WHERE "sheetNum"=%s', (sheet_num,))
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
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('landused', 'landused_id'), "
                "GREATEST((SELECT MAX(landused_id) FROM landused), 1))"
            )
            return landused_id
        cursor.execute(
            "INSERT INTO landused (category) VALUES (%s) RETURNING landused_id",
            (category,),
        )
        return cursor.fetchone()[0]


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
            'INSERT INTO sjung ("sheetNum", "sheetName", "sheetScale") VALUES (%s, %s, %s)',
            (sheet_num, sheet_name, sheet_scale),
        )


def update_sjungu_record(sheet_num, sheet_name, sheet_scale):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    sheet_name = _require_non_empty_str(sheet_name, "sheetName")
    sheet_scale = _require_non_empty_str(sheet_scale, "sheetScale")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            'UPDATE sjung SET "sheetName"=%s, "sheetScale"=%s WHERE "sheetNum"=%s',
            (sheet_name, sheet_scale, sheet_num),
        )
        return cursor.rowcount > 0


def delete_sjungu_record(sheet_num):
    sheet_num = _require_non_empty_str(sheet_num, "sheetNum")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute('DELETE FROM sjung WHERE "sheetNum"=%s', (sheet_num,))
        return cursor.rowcount > 0


def ensure_core_tables():
    """Create all LISTMAP tables when missing (safe for Supabase / managed Postgres)."""
    statements = (
        """
        CREATE TABLE IF NOT EXISTS topography (
          "sheetNum"     VARCHAR(45)  NOT NULL,
          "sheetName"    VARCHAR(255) NOT NULL,
          "sheetScale"   VARCHAR(45)  NOT NULL,
          release_year   INT          NOT NULL,
          PRIMARY KEY ("sheetNum")
        )
        """,
        'CREATE INDEX IF NOT EXISTS idx_topography_release_year ON topography (release_year)',
        'CREATE INDEX IF NOT EXISTS idx_topography_sheet_name ON topography ("sheetName")',
        """
        CREATE TABLE IF NOT EXISTS dted (
          id_name VARCHAR(255) NOT NULL,
          level   INT          NOT NULL,
          PRIMARY KEY (id_name)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_dted_level ON dted (level)",
        """
        CREATE TABLE IF NOT EXISTS landused (
          landused_id SERIAL PRIMARY KEY,
          category    VARCHAR(255) NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_landused_category ON landused (category)",
        """
        CREATE TABLE IF NOT EXISTS sjung (
          "sheetNum"   VARCHAR(255) NOT NULL,
          "sheetName"  VARCHAR(45)  NOT NULL,
          "sheetScale" VARCHAR(45)  NOT NULL,
          PRIMARY KEY ("sheetNum")
        )
        """,
        'CREATE INDEX IF NOT EXISTS idx_sjung_sheet_name ON sjung ("sheetName")',
    )
    with get_db_cursor(commit=True) as cursor:
        for sql in statements:
            cursor.execute(sql)
    ensure_audit_log_table()
    ensure_audit_document_table()


def ensure_audit_log_table():
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
              id          SERIAL PRIMARY KEY,
              username    VARCHAR(100) NOT NULL,
              role        VARCHAR(20)  NOT NULL,
              action      VARCHAR(50)  NOT NULL,
              report_ref  VARCHAR(50)  NULL,
              item_count  INT          NOT NULL DEFAULT 0,
              details     JSONB        NULL,
              created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log (created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_log (username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log (action)"
        )


def ensure_audit_document_table():
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_document (
              id           SERIAL PRIMARY KEY,
              audit_id     INT          NOT NULL,
              filename     VARCHAR(255) NOT NULL,
              mime_type    VARCHAR(100) NOT NULL,
              file_size    INT          NOT NULL,
              file_data    BYTEA        NOT NULL,
              created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uq_audit_document_audit_id UNIQUE (audit_id),
              CONSTRAINT fk_audit_document_audit
                FOREIGN KEY (audit_id) REFERENCES audit_log(id)
                ON DELETE CASCADE
            )
            """
        )


def insert_audit_log(username, role, action, report_ref=None, item_count=0, details=None):
    details_json = json.dumps(details) if details is not None else None
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO audit_log (username, role, action, report_ref, item_count, details)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (username, role, action, report_ref, item_count, details_json),
        )
        return cursor.fetchone()[0]


def insert_audit_document(audit_id, filename, mime_type, file_data):
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
            RETURNING id
            """,
            (audit_id, filename, mime_type, file_size, psycopg2.Binary(file_data)),
        )
        return cursor.fetchone()[0]


def get_audit_document(audit_id):
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
    if isinstance(row.get("file_data"), memoryview):
        row["file_data"] = bytes(row["file_data"])
    if row.get("created_at") is not None:
        row["created_at"] = row["created_at"].isoformat(sep=" ", timespec="seconds")
    return row


def get_audit_logs(limit=50):
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
