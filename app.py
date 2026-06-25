import logging
from datetime import timedelta

from flask import Flask, jsonify, render_template, request, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import database
from audit import VALID_ACTIONS, log_event
from auth import admin_required, get_current_user, login_required, register_auth_routes
from config import Config
from export_xlsx import build_export_workbook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

API_ERROR_MESSAGE = "An internal error occurred. Please try again later."
VALID_CATEGORIES = ("topography", "dted", "landused", "sjungu")

app = Flask(__name__)
app.config.from_object(Config)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=Config.SESSION_LIFETIME_MINUTES)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[Config.RATE_LIMIT_DEFAULT] if Config.RATE_LIMIT_ENABLED else [],
    storage_uri="memory://",
)

register_auth_routes(app)

try:
    database.ensure_audit_log_table()
except Exception:
    logger.exception("Failed to ensure audit_log table exists")


@limiter.request_filter
def _skip_rate_limit_for_static():
    return request.endpoint == "static"


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
    except Exception:
        logger.exception("Failed to fetch records for category: %s", category)
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
        if not log_event(action, report_ref=report_ref, item_count=item_count, details=details):
            return jsonify({"error": API_ERROR_MESSAGE}), 500
        return jsonify({"ok": True})
    except ValueError:
        return jsonify({"error": "Invalid audit action."}), 400
    except Exception:
        logger.exception("Failed to create audit entry")
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
    report_title = data.get("report_title", "SaP LISTMAP DATA SPECIFICATION REPORT")

    try:
        buffer = build_export_workbook(report_title, report_ref, selections)
        log_event(
            "export_xlsx",
            report_ref=report_ref,
            item_count=item_count,
            details={"report_title": report_title},
        )
        filename = f"SaP_ListMap_Export_{report_ref or 'report'}.xlsx"
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        logger.exception("Failed to generate Excel export")
        return jsonify({"error": API_ERROR_MESSAGE}), 500


if __name__ == "__main__":
    if Config.APP_ENV == "production":
        logger.warning("Use 'python run_production.py' for production deployments.")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
