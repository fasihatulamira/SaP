import logging
from datetime import datetime, timedelta, timezone
from io import BytesIO

from flask import Flask, jsonify, render_template, request, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mysql.connector import errors as mysql_errors

import database
from database import (
    create_dted_record,
    create_landused_record,
    create_sjungu_record,
    create_topography_record,
    delete_dted_record,
    delete_landused_record,
    delete_sjungu_record,
    delete_topography_record,
    update_dted_record,
    update_landused_record,
    update_sjungu_record,
    update_topography_record,
)
from audit import VALID_ACTIONS, log_event
from auth import admin_required, get_current_user, login_required, register_auth_routes
from config import Config
from export_docx import build_export_docx
from export_filenames import build_export_filename
from export_xlsx import build_export_workbook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

API_ERROR_MESSAGE = "An internal error occurred. Please try again later."
VALID_CATEGORIES = ("topography", "dted", "landused", "sjungu")
DOCUMENT_ACTIONS = frozenset({"export_xlsx", "export_docx", "export_pdf", "print"})
MAX_AUDIT_DOCUMENT_BYTES = 15 * 1024 * 1024
ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

app = Flask(__name__)
app.config.from_object(Config)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=Config.SESSION_LIFETIME_MINUTES)
app.config["MAX_CONTENT_LENGTH"] = MAX_AUDIT_DOCUMENT_BYTES + (1 * 1024 * 1024)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[Config.RATE_LIMIT_DEFAULT] if Config.RATE_LIMIT_ENABLED else [],
    storage_uri="memory://",
)

register_auth_routes(app)

# Do not block startup on a cold/sleeping managed DB (Render + Aiven free tiers).
# Tables are ensured lazily on the first authenticated data request.


@limiter.request_filter
def _skip_rate_limit_for_static():
    return request.endpoint == "static"


@app.route("/api/health", methods=["GET"])
@limiter.exempt
def health():
    """Public health + DB connectivity check (no secrets)."""
    info = database.db_status()
    try:
        with database.get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        info["db"] = "ok"
        return jsonify(info), 200
    except Exception as exc:
        info["db"] = "error"
        info["db_error"] = str(exc)[:300]
        return jsonify(info), 503


def _parse_pagination():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        limit = min(database.MAX_LIMIT, max(1, int(request.args.get("limit", database.DEFAULT_LIMIT))))
    except (TypeError, ValueError):
        limit = database.DEFAULT_LIMIT
    return page, limit


def _selection_item_count(payload):
    return sum(len(payload.get(cat) or []) for cat in VALID_CATEGORIES)


def _safe_filename(name, fallback="document"):
    cleaned = "".join(ch for ch in str(name or fallback) if ch.isalnum() or ch in ("-", "_", ".", " ")).strip()
    return cleaned or fallback


def _resolve_document_mime(uploaded, form_mime=""):
    mime_type = ((uploaded.mimetype if uploaded is not None else "") or "").strip() or (form_mime or "").strip()
    if mime_type in ALLOWED_DOCUMENT_MIME_TYPES:
        return mime_type
    name = ((uploaded.filename if uploaded is not None else "") or "").lower()
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if name.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return mime_type


def _validate_document_payload(file_data, mime_type):
    if not file_data:
        return "Document file is empty.", 400
    if len(file_data) > MAX_AUDIT_DOCUMENT_BYTES:
        return "Document exceeds maximum allowed size.", 413
    if mime_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        return "Unsupported document type.", 400
    return None, None


def _store_audit_document(audit_id, filename, mime_type, file_data):
    if not audit_id or not file_data:
        return False
    error, _status = _validate_document_payload(file_data, mime_type)
    if error:
        logger.warning("Rejected audit document for audit_id=%s: %s", audit_id, error)
        return False
    database.insert_audit_document(
        audit_id=audit_id,
        filename=_safe_filename(filename),
        mime_type=mime_type,
        file_data=file_data,
    )
    return True


@app.route("/")
@login_required
def index():
    """Renders the main dashboard page."""
    user = get_current_user()
    return render_template(
        "index.html",
        auth_enabled=Config.is_auth_required(),
        user_role=user["role"] if user else "admin",
        username=user["username"] if user else "",
    )


@app.route("/api/me", methods=["GET"])
@login_required
def get_me():
    """Return current user info and role."""
    user = get_current_user()
    if not user:
        return jsonify({"username": "guest", "role": "admin"})
    return jsonify(user)


@app.route("/api/filters", methods=["GET"])
@login_required
@limiter.limit("60 per minute")
def get_filters():
    """Returns lists of active release years and levels for filter dropdowns."""
    try:
        database.ensure_schema_ready()
        filters = database.get_filter_options()
        return jsonify(filters)
    except Exception:
        logger.exception("Failed to fetch filter options")
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/records/<category>", methods=["GET"])
@login_required
@limiter.limit("120 per minute")
def get_category_records(category):
    """Returns paginated, filtered records for a single category."""
    if category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category."}), 400

    try:
        database.ensure_schema_ready()
        page, limit = _parse_pagination()

        if category == "topography":
            topo_year = request.args.get("year") or None
            if topo_year == "":
                topo_year = None
            result = database.get_topography_data(
                search_query=request.args.get("search") or None,
                release_year=topo_year,
                page=page,
                limit=limit,
            )
        elif category == "dted":
            dted_level = request.args.get("level") or None
            if dted_level == "":
                dted_level = None
            else:
                try:
                    dted_level = int(dted_level) if dted_level is not None else None
                except ValueError:
                    dted_level = None
            result = database.get_dted_data(
                search_query=request.args.get("search") or None,
                level=dted_level,
                page=page,
                limit=limit,
            )
        elif category == "landused":
            result = database.get_landused_data(
                search_query=request.args.get("search") or None,
                page=page,
                limit=limit,
            )
        else:
            result = database.get_sjungu_data(
                search_query=request.args.get("search") or None,
                page=page,
                limit=limit,
            )

        return jsonify(result)
    except Exception as exc:
        logger.exception("Failed to fetch records for category: %s", category)
        return jsonify({
            "error": "Database unavailable. If using Aiven free MySQL, power it on and retry.",
            "detail": str(exc)[:200],
        }), 503


@app.route("/api/records/<category>", methods=["POST"])
@admin_required
@limiter.limit("60 per minute")
def create_category_record(category):
    """Create a new record in the given category (admin only)."""
    if category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category."}), 400

    data = request.get_json(silent=True) or {}

    try:
        if category == "topography":
            create_topography_record(
                data.get("sheetNum"),
                data.get("sheetName"),
                data.get("sheetScale"),
                data.get("release_year"),
            )
            record = {
                "sheetNum": str(data.get("sheetNum", "")).strip(),
                "sheetName": str(data.get("sheetName", "")).strip(),
                "sheetScale": str(data.get("sheetScale", "")).strip(),
                "release_year": int(data.get("release_year")),
            }
        elif category == "dted":
            create_dted_record(data.get("id_name"), data.get("level"))
            record = {
                "id_name": str(data.get("id_name", "")).strip(),
                "level": int(data.get("level")),
            }
        elif category == "landused":
            landused_id = create_landused_record(data.get("category"), data.get("landused_id"))
            record = {
                "landused_id": landused_id,
                "category": str(data.get("category", "")).strip(),
            }
        else:
            create_sjungu_record(
                data.get("sheetNum"),
                data.get("sheetName"),
                data.get("sheetScale"),
            )
            record = {
                "sheetNum": str(data.get("sheetNum", "")).strip(),
                "sheetName": str(data.get("sheetName", "")).strip(),
                "sheetScale": str(data.get("sheetScale", "")).strip(),
            }
        return jsonify({"ok": True, "record": record}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except mysql_errors.IntegrityError:
        return jsonify({"error": "A record with that identifier already exists."}), 409
    except Exception:
        logger.exception("Failed to create record for category: %s", category)
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/records/<category>/<path:record_id>", methods=["PUT"])
@admin_required
@limiter.limit("60 per minute")
def update_category_record(category, record_id):
    """Update an existing record (admin only)."""
    if category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category."}), 400

    data = request.get_json(silent=True) or {}

    try:
        updated = False
        if category == "topography":
            updated = update_topography_record(
                record_id,
                data.get("sheetName"),
                data.get("sheetScale"),
                data.get("release_year"),
            )
            record = {
                "sheetNum": record_id,
                "sheetName": str(data.get("sheetName", "")).strip(),
                "sheetScale": str(data.get("sheetScale", "")).strip(),
                "release_year": int(data.get("release_year")),
            }
        elif category == "dted":
            updated = update_dted_record(record_id, data.get("level"))
            record = {"id_name": record_id, "level": int(data.get("level"))}
        elif category == "landused":
            updated = update_landused_record(record_id, data.get("category"))
            record = {
                "landused_id": int(record_id),
                "category": str(data.get("category", "")).strip(),
            }
        else:
            updated = update_sjungu_record(
                record_id,
                data.get("sheetName"),
                data.get("sheetScale"),
            )
            record = {
                "sheetNum": record_id,
                "sheetName": str(data.get("sheetName", "")).strip(),
                "sheetScale": str(data.get("sheetScale", "")).strip(),
            }

        if not updated:
            return jsonify({"error": "Record not found."}), 404
        return jsonify({"ok": True, "record": record})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Failed to update record for category: %s", category)
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/records/<category>/<path:record_id>", methods=["DELETE"])
@admin_required
@limiter.limit("60 per minute")
def delete_category_record(category, record_id):
    """Delete a record (admin only)."""
    if category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category."}), 400

    try:
        if category == "topography":
            deleted = delete_topography_record(record_id)
        elif category == "dted":
            deleted = delete_dted_record(record_id)
        elif category == "landused":
            deleted = delete_landused_record(record_id)
        else:
            deleted = delete_sjungu_record(record_id)

        if not deleted:
            return jsonify({"error": "Record not found."}), 404
        return jsonify({"ok": True})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Failed to delete record for category: %s", category)
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/audit", methods=["GET"])
@admin_required
@limiter.limit("30 per minute")
def list_audit_logs():
    """Return recent audit log entries (admin only)."""
    try:
        limit = request.args.get("limit", 50)
        logs = database.get_audit_logs(limit=limit)
        return jsonify({"items": logs})
    except Exception:
        logger.exception("Failed to fetch audit logs")
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/audit", methods=["POST"])
@login_required
@limiter.limit("60 per minute")
def create_audit_entry():
    """Record a client-side export or action in the audit log."""
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    if action not in VALID_ACTIONS:
        return jsonify({"error": "Invalid audit action."}), 400

    report_ref = data.get("report_ref")
    item_count = int(data.get("item_count") or 0)
    details = data.get("details")

    try:
        audit_id = log_event(action, report_ref=report_ref, item_count=item_count, details=details)
        if not audit_id:
            return jsonify({"error": API_ERROR_MESSAGE}), 500
        return jsonify({"ok": True, "id": audit_id})
    except ValueError:
        return jsonify({"error": "Invalid audit action."}), 400
    except Exception:
        logger.exception("Failed to create audit entry")
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/audit/document", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def create_audit_with_document():
    """Record an export/print action and archive the generated document."""
    action = request.form.get("action", "")
    if action not in DOCUMENT_ACTIONS:
        return jsonify({"error": "Invalid audit action for document archive."}), 400

    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "Document file is required."}), 400

    mime_type = _resolve_document_mime(uploaded, request.form.get("mime_type", ""))
    file_data = uploaded.read()
    error, status = _validate_document_payload(file_data, mime_type)
    if error:
        return jsonify({"error": error}), status

    report_ref = request.form.get("report_ref") or None
    try:
        item_count = int(request.form.get("item_count") or 0)
    except (TypeError, ValueError):
        item_count = 0

    report_title = (request.form.get("report_title") or "").strip()
    filename = _safe_filename(
        request.form.get("filename") or uploaded.filename,
        fallback=build_export_filename(report_title, ALLOWED_DOCUMENT_MIME_TYPES[mime_type].lstrip(".")),
    )

    details = {
        "report_title": report_title or None,
        "filename": filename,
        "mime_type": mime_type,
        "document_available": True,
    }
    details = {k: v for k, v in details.items() if v is not None}

    try:
        audit_id = log_event(action, report_ref=report_ref, item_count=item_count, details=details)
        if not audit_id:
            return jsonify({"error": API_ERROR_MESSAGE}), 500
        if not _store_audit_document(audit_id, filename, mime_type, file_data):
            return jsonify({"error": API_ERROR_MESSAGE}), 500
        return jsonify({"ok": True, "id": audit_id})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Failed to create audit entry with document")
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/audit/<int:audit_id>/document", methods=["GET"])
@admin_required
@limiter.limit("30 per minute")
def download_audit_document(audit_id):
    """Return the archived document for an audit entry (admin only)."""
    try:
        doc = database.get_audit_document(audit_id)
        if not doc:
            return jsonify({"error": "Document not found."}), 404

        mime_type = doc["mime_type"]
        as_attachment = mime_type != "application/pdf"
        return send_file(
            BytesIO(doc["file_data"]),
            mimetype=mime_type,
            as_attachment=as_attachment,
            download_name=doc["filename"],
        )
    except Exception:
        logger.exception("Failed to fetch audit document for id=%s", audit_id)
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/audit/<int:audit_id>/document", methods=["PUT"])
@admin_required
@limiter.limit("20 per minute")
def replace_audit_document(audit_id):
    """Replace or rename the archived document for an audit entry (admin only)."""
    uploaded = request.files.get("file")
    has_file = uploaded is not None and bool(uploaded.filename)
    requested_name = (request.form.get("filename") or "").strip()

    if not has_file and not requested_name:
        return jsonify({"error": "A replacement file or new filename is required."}), 400

    try:
        existing = database.get_audit_document(audit_id)
        if not existing:
            return jsonify({"error": "Document not found."}), 404

        mime_type = existing["mime_type"]
        file_data = None
        if has_file:
            mime_type = _resolve_document_mime(uploaded, request.form.get("mime_type", ""))
            file_data = uploaded.read()
            error, status = _validate_document_payload(file_data, mime_type)
            if error:
                return jsonify({"error": error}), status

        filename = _safe_filename(
            requested_name or (uploaded.filename if has_file else existing["filename"]),
            fallback=existing["filename"],
        )
        updated = database.update_audit_document(
            audit_id,
            filename=filename,
            mime_type=mime_type if has_file else None,
            file_data=file_data,
        )
        if not updated:
            return jsonify({"error": "Document not found."}), 404

        user = get_current_user() or {}
        details_update = {
            "filename": filename,
            "mime_type": mime_type,
            "document_available": True,
            "replaced_by": user.get("username") or "admin",
            "replaced_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        database.patch_audit_log_details(audit_id, details_update)
        return jsonify({"ok": True, "id": audit_id, "filename": filename})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Failed to replace audit document for id=%s", audit_id)
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/audit/<int:audit_id>", methods=["DELETE"])
@admin_required
@limiter.limit("30 per minute")
def delete_audit_entry(audit_id):
    """Delete an audit log entry and its archived document (admin only)."""
    try:
        deleted = database.delete_audit_log(audit_id)
        if not deleted:
            return jsonify({"error": "Audit entry not found."}), 404
        return jsonify({"ok": True})
    except Exception:
        logger.exception("Failed to delete audit entry for id=%s", audit_id)
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/export/xlsx", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def export_xlsx():
    """Generate a formatted Excel workbook from selected records."""
    data = request.get_json(silent=True) or {}
    selections = {cat: data.get(cat) or [] for cat in VALID_CATEGORIES}
    item_count = _selection_item_count(selections)

    if item_count == 0:
        return jsonify({"error": "No records selected for export."}), 400

    report_ref = data.get("report_ref")
    report_title = data.get("report_title", "EKSESAIS")

    try:
        buffer = build_export_workbook(report_title, report_ref, selections)
        file_data = buffer.getvalue()
        filename = build_export_filename(report_title, "xlsx")
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        audit_id = log_event(
            "export_xlsx",
            report_ref=report_ref,
            item_count=item_count,
            details={
                "report_title": report_title,
                "filename": filename,
                "mime_type": mime_type,
                "document_available": True,
            },
        )
        if audit_id:
            _store_audit_document(audit_id, filename, mime_type, file_data)
        return send_file(
            BytesIO(file_data),
            as_attachment=True,
            download_name=filename,
            mimetype=mime_type,
        )
    except Exception:
        logger.exception("Failed to generate Excel export")
        return jsonify({"error": API_ERROR_MESSAGE}), 500


@app.route("/api/export/docx", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def export_docx():
    """Generate a Word (.docx) KEMBARAN I document from selected records."""
    data = request.get_json(silent=True) or {}
    selections = {cat: data.get(cat) or [] for cat in VALID_CATEGORIES}
    item_count = _selection_item_count(selections)

    if item_count == 0:
        return jsonify({"error": "No records selected for export."}), 400

    report_ref = data.get("report_ref")
    report_title = data.get("report_title", "EKSESAIS")

    try:
        buffer = build_export_docx(report_title, report_ref, selections)
        file_data = buffer.getvalue()
        filename = build_export_filename(report_title, "docx")
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        audit_id = log_event(
            "export_docx",
            report_ref=report_ref,
            item_count=item_count,
            details={
                "report_title": report_title,
                "filename": filename,
                "mime_type": mime_type,
                "document_available": True,
            },
        )
        if audit_id:
            _store_audit_document(audit_id, filename, mime_type, file_data)
        return send_file(
            BytesIO(file_data),
            as_attachment=True,
            download_name=filename,
            mimetype=mime_type,
        )
    except Exception:
        logger.exception("Failed to generate Word export")
        return jsonify({"error": API_ERROR_MESSAGE}), 500


if __name__ == "__main__":
    if Config.APP_ENV == "production":
        logger.warning("Use 'python run_production.py' for production deployments.")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
