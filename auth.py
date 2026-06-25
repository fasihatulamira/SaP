import secrets
from functools import wraps

from flask import jsonify, redirect, render_template, request, session, url_for

from config import Config


def resolve_role(username, password):
    """Return role string if credentials match, else None."""
    for expected_user, (expected_pass, role) in Config.user_credentials().items():
        if secrets.compare_digest(username or "", expected_user) and secrets.compare_digest(
            password or "", expected_pass
        ):
            return role
    return None


def get_current_user():
    if not session.get("authenticated"):
        return None
    role = session.get("role", "user")
    if role == "viewer":
        role = "user"
    return {
        "username": session.get("username", ""),
        "role": role,
    }


def login_required(view):
    """Require an authenticated session when auth is enabled."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not Config.is_auth_required():
            return view(*args, **kwargs)
        if session.get("authenticated"):
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required."}), 401
        next_url = request.url if request.method == "GET" else url_for("index")
        return redirect(url_for("login", next=next_url))

    return wrapped


def admin_required(view):
    """Require admin role."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not Config.is_auth_required():
            return view(*args, **kwargs)
        if session.get("authenticated") and session.get("role") == "admin":
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Admin access required."}), 403
        return redirect(url_for("index"))

    return wrapped


def register_auth_routes(app):
    """Register login and logout routes."""

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not Config.is_auth_required():
            return redirect(url_for("index"))

        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            role = resolve_role(username, password)
            if role:
                session.clear()
                session["authenticated"] = True
                session["username"] = username
                session["role"] = role
                session.permanent = True
                next_url = request.args.get("next") or url_for("index")
                if not next_url.startswith("/") or next_url.startswith("//"):
                    next_url = url_for("index")
                return redirect(next_url)
            try:
                from audit import log_event

                log_event("login_failed", details={"username": username}, username=username, role="—")
            except Exception:
                pass
            error = "Invalid username or password."

        return render_template("login.html", error=error)

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return redirect(url_for("login"))
