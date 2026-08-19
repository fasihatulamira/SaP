import json
import logging

import database
from auth import get_current_user

logger = logging.getLogger(__name__)

VALID_ACTIONS = (
    "login_failed",
    "create_report",
    "export_xlsx",
    "export_pdf",
    "print",
    "clear_selection",
)


def log_event(action, report_ref=None, item_count=0, details=None, username=None, role=None):
    """Record an audit log entry for the current user.

    Returns the new audit_log id on success, or False on failure.
    """
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid audit action: {action}")

    user = get_current_user() or {"username": username or "system", "role": role or "system"}
    if username:
        user = {**user, "username": username}
    if role:
        user = {**user, "role": role}

    try:
        audit_id = database.insert_audit_log(
            username=user["username"],
            role=user["role"],
            action=action,
            report_ref=report_ref,
            item_count=item_count,
            details=details,
        )
        return audit_id
    except Exception:
        logger.exception("Failed to write audit log for action=%s", action)
        return False
