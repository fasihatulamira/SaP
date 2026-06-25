#!/usr/bin/env python3
"""Generate enhanced SaP LISTMAP presentation with icons and visuals."""
import json
import subprocess
import sys

NS = 'xmlns="http://www.larkoffice.com/sml/2.0"'
ACCENT = "rgb(15, 118, 110)"
ACCENT_LIGHT = "rgb(20, 184, 166)"
ACCENT_SOFT = "rgb(204, 251, 241)"
BG_LIGHT = "rgb(252, 252, 253)"
BG_DARK = "rgb(15, 23, 42)"
TEXT_PRIMARY = "rgb(15, 23, 42)"
TEXT_BODY = "rgb(51, 65, 85)"
TEXT_MUTED = "rgb(100, 116, 139)"
CARD_BG = "rgb(255, 255, 255)"
CARD_BORDER = "rgb(226, 232, 240)"
WHITE = "rgb(255, 255, 255)"


def slide_open(bg=BG_LIGHT):
    return f'<slide {NS}><style><fill><fillColor color="{bg}"/></fill></style><data>'


def slide_close():
    return "</data></slide>"


def accent_bar():
    return f'<shape type="rect" topLeftX="0" topLeftY="0" width="10" height="540"><fill><fillColor color="{ACCENT}"/></fill></shape>'


def deco_circles():
    """Subtle background decoration."""
    return (
        f'<shape type="ellipse" topLeftX="780" topLeftY="-40" width="200" height="200">'
        f'<fill><fillColor color="{ACCENT_SOFT}"/></fill></shape>'
        f'<shape type="ellipse" topLeftX="820" topLeftY="400" width="160" height="160">'
        f'<fill><fillColor color="rgb(240, 253, 250)"/></fill></shape>'
        f'<shape type="ellipse" topLeftX="-60" topLeftY="420" width="140" height="140">'
        f'<fill><fillColor color="rgb(236, 253, 245)"/></fill></shape>'
    )


def text_box(x, y, w, h, content, text_type="body", align="left", color=TEXT_BODY, size=None, bold=False):
    size_attr = f' fontSize="{size}"' if size else ""
    color_attr = f' color="{color}"'
    bold_attr = ' bold="true"' if bold else ""
    return (
        f'<shape type="text" topLeftX="{x}" topLeftY="{y}" width="{w}" height="{h}">'
        f'<content textType="{text_type}" textAlign="{align}"{color_attr}{size_attr}{bold_attr}>'
        f"{content}</content></shape>"
    )


def rect_card(x, y, w, h, fill=CARD_BG, border=CARD_BORDER, radius_note=False):
    return (
        f'<shape type="rect" topLeftX="{x}" topLeftY="{y}" width="{w}" height="{h}">'
        f'<fill><fillColor color="{fill}"/></fill>'
        f'<border color="{border}" width="1"/></shape>'
    )


def icon(icon_type, x, y, size=32, color=ACCENT):
    return (
        f'<icon iconType="{icon_type}" topLeftX="{x}" topLeftY="{y}" width="{size}" height="{size}">'
        f'<fill><fillColor color="{color}"/></fill></icon>'
    )


def icon_badge(icon_type, x, y, badge_size=48, icon_size=28, bg=ACCENT_SOFT, ic=ACCENT):
    cx = x + (badge_size - icon_size) // 2
    cy = y + (badge_size - icon_size) // 2
    return (
        f'<shape type="ellipse" topLeftX="{x}" topLeftY="{y}" width="{badge_size}" height="{badge_size}">'
        f'<fill><fillColor color="{bg}"/></fill></shape>'
        f'{icon(icon_type, cx, cy, icon_size, ic)}'
    )


def hero_whiteboard(x, y, w, h):
    inner = """
  <circle cx="170" cy="170" r="150" fill="rgba(15,118,110,0.12)"/>
  <circle cx="170" cy="170" r="100" fill="none" stroke="rgba(94,234,212,0.45)" stroke-width="2"/>
  <circle cx="170" cy="170" r="60" fill="none" stroke="rgba(94,234,212,0.35)" stroke-width="1.5"/>
  <rect x="50" y="110" width="240" height="130" rx="8" fill="rgba(15,118,110,0.18)" stroke="rgba(94,234,212,0.55)" stroke-width="1.5"/>
  <line x1="50" y1="145" x2="290" y2="145" stroke="rgba(94,234,212,0.35)" stroke-width="1"/>
  <line x1="50" y1="175" x2="290" y2="175" stroke="rgba(94,234,212,0.35)" stroke-width="1"/>
  <line x1="50" y1="205" x2="290" y2="205" stroke="rgba(94,234,212,0.35)" stroke-width="1"/>
  <line x1="110" y1="110" x2="110" y2="240" stroke="rgba(94,234,212,0.35)" stroke-width="1"/>
  <line x1="170" y1="110" x2="170" y2="240" stroke="rgba(94,234,212,0.35)" stroke-width="1"/>
  <line x1="230" y1="110" x2="230" y2="240" stroke="rgba(94,234,212,0.35)" stroke-width="1"/>
  <circle cx="110" cy="175" r="12" fill="rgba(20,184,166,0.9)"/>
  <circle cx="170" cy="145" r="10" fill="rgba(94,234,212,0.85)"/>
  <circle cx="230" cy="195" r="13" fill="rgba(15,118,110,0.9)"/>
  <path d="M110,175 L170,145 L230,195" fill="none" stroke="rgba(94,234,212,0.65)" stroke-width="2" stroke-dasharray="6,4"/>
  <text x="170" y="290" text-anchor="middle" font-family="sans-serif" font-size="16" fill="rgba(148,163,184,0.9)">LISTMAP</text>"""
    return (
        f'<whiteboard topLeftX="{x}" topLeftY="{y}" width="{w}" height="{h}">'
        f'<svg xmlns="http://www.w3.org/2000/svg">{inner}</svg></whiteboard>'
    )


def tech_banner_whiteboard(x, y, w, h):
    inner = """
  <rect width="860" height="100" rx="12" fill="rgba(15,118,110,0.1)" stroke="rgba(15,118,110,0.25)" stroke-width="1"/>
  <circle cx="70" cy="50" r="24" fill="rgba(15,118,110,0.2)"/>
  <rect x="150" y="28" width="52" height="44" rx="6" fill="rgba(15,118,110,0.12)" stroke="rgba(15,118,110,0.35)" stroke-width="1"/>
  <rect x="230" y="28" width="52" height="44" rx="6" fill="rgba(15,118,110,0.12)" stroke="rgba(15,118,110,0.35)" stroke-width="1"/>
  <rect x="310" y="28" width="52" height="44" rx="6" fill="rgba(15,118,110,0.12)" stroke="rgba(15,118,110,0.35)" stroke-width="1"/>
  <line x1="202" y1="50" x2="230" y2="50" stroke="rgba(15,118,110,0.5)" stroke-width="2"/>
  <line x1="282" y1="50" x2="310" y2="50" stroke="rgba(15,118,110,0.5)" stroke-width="2"/>
  <text x="176" y="55" text-anchor="middle" font-family="sans-serif" font-size="11" fill="rgba(15,118,110,0.85)">UI</text>
  <text x="256" y="55" text-anchor="middle" font-family="sans-serif" font-size="11" fill="rgba(15,118,110,0.85)">API</text>
  <text x="336" y="55" text-anchor="middle" font-family="sans-serif" font-size="11" fill="rgba(15,118,110,0.85)">DB</text>
  <text x="520" y="42" font-family="sans-serif" font-size="18" font-weight="bold" fill="rgba(15,23,42,0.85)">Flask + MySQL + Docker</text>
  <text x="520" y="68" font-family="sans-serif" font-size="13" fill="rgba(100,116,139,0.9)">Full-stack cartography data platform</text>"""
    return (
        f'<whiteboard topLeftX="{x}" topLeftY="{y}" width="{w}" height="{h}">'
        f'<svg xmlns="http://www.w3.org/2000/svg">{inner}</svg></whiteboard>'
    )


def arrow_line(x1, y1, x2, y2, color=ACCENT):
    return f'<line startX="{x1}" startY="{y1}" endX="{x2}" endY="{y2}"><border color="{color}" width="2"/></line>'


def slide_header(title, subtitle=None, header_icon=None):
    parts = [accent_bar(), deco_circles()]
    if header_icon:
        parts.append(icon_badge(header_icon, 48, 28, 52, 30))
        tx = 115
    else:
        tx = 48
    parts.append(text_box(tx, 32, 800, 46, f"<p>{title}</p>", "title", "left", TEXT_PRIMARY, 34, bold=True))
    if subtitle:
        parts.append(text_box(tx, 78, 800, 28, f"<p>{subtitle}</p>", "body", "left", TEXT_MUTED, 14))
    return "".join(parts)


def slide_cover():
    parts = [
        slide_open(BG_DARK),
        f'<shape type="ellipse" topLeftX="680" topLeftY="-80" width="320" height="320">'
        f'<fill><fillColor color="rgba(15,118,110,0.15)"/></fill></shape>',
        f'<shape type="ellipse" topLeftX="-100" topLeftY="350" width="280" height="280">'
        f'<fill><fillColor color="rgba(20,184,166,0.1)"/></fill></shape>',
        f'<shape type="rect" topLeftX="0" topLeftY="476" width="960" height="6">'
        f'<fill><fillColor color="{ACCENT_LIGHT}"/></fill></shape>',
        icon("iconpark/Charts/area-map.svg", 80, 130, 64, ACCENT_LIGHT),
        text_box(80, 210, 520, 80, "<p>SaP LISTMAP</p>", "title", "left", "rgb(248, 250, 252)", 52, bold=True),
        text_box(80, 290, 520, 50, "<p>System Overview</p>", "headline", "left", "rgb(148, 163, 184)", 28),
        text_box(
            80, 350, 520, 70,
            "<p>Cartography Dataset Dashboard</p><p>Browse · Select · Export Map Records</p>",
            "body", "left", "rgb(203, 213, 225)", 17,
        ),
        text_box(80, 440, 400, 30, "<p>Project Presentation for Supervisor Review</p>", "caption", "left", "rgb(100, 116, 139)", 13),
        hero_whiteboard(560, 90, 340, 340),
        slide_close(),
    ]
    return "".join(parts)


def slide_overview():
    parts = [slide_open()]
    parts.append(slide_header("Project Overview", "Web dashboard for cartography dataset management", "iconpark/Charts/data-screen.svg"))
    parts.append(text_box(
        48, 120, 520, 110,
        "<p><strong>Purpose:</strong> Browse cartography datasets, select records, and generate specification reports.</p>"
        "<p><strong>Users:</strong> Cartography / GIS staff needing map sheet lookup and exportable reports.</p>",
        "body", "left", TEXT_BODY, 15,
    ))
    parts.append(rect_card(590, 110, 320, 370, "rgb(248, 250, 252)"))
    parts.append(text_box(610, 125, 280, 28, "<p>Data Categories</p>", "headline", "left", ACCENT, 18, bold=True))
    cats = [
        ("iconpark/Charts/area-map.svg", "Topography", "Map sheets, scale &amp; year"),
        ("iconpark/Datas/database-point.svg", "DTED", "Terrain elevation data"),
        ("iconpark/Charts/chart-pie.svg", "Land Use", "Classification categories"),
        ("iconpark/Edit/mindmap-map.svg", "Sjungu", "Sjung map sheet records"),
    ]
    for i, (ic, name, desc) in enumerate(cats):
        y = 165 + i * 68
        parts.append(rect_card(610, y, 280, 58, WHITE))
        parts.append(icon_badge(ic, 620, y + 8, 42, 24))
        parts.append(text_box(672, y + 8, 200, 22, f"<p><strong>{name}</strong></p>", "body", "left", TEXT_PRIMARY, 14, bold=True))
        parts.append(text_box(672, y + 30, 200, 22, f"<p>{desc}</p>", "caption", "left", TEXT_MUTED, 11))
    parts.append(slide_close())
    return "".join(parts)


def slide_tech_stack():
    parts = [slide_open()]
    parts.append(slide_header("Technology Stack", "Modern full-stack components powering the platform", "iconpark/Hardware/server.svg"))
    parts.append(tech_banner_whiteboard(48, 115, 864, 100))
    layers = [
        ("iconpark/Others/browser.svg", "Frontend", "HTML5 · CSS3 · Vanilla JS", "Tabbed UI, search/filter, PDF via html2pdf.js"),
        ("iconpark/Office/file-code-one.svg", "Backend", "Python 3.10+ · Flask 3.x", "REST API, auth, rate limiting, Excel export"),
        ("iconpark/Datas/database-code.svg", "Database", "MySQL 8.0", "InnoDB tables, indexed search, audit log"),
        ("iconpark/Connect/link-cloud-sucess.svg", "Deploy", "Docker · Waitress · nginx", "One-command deploy, WSGI, HTTPS proxy"),
    ]
    for i, (ic, title, tech, detail) in enumerate(layers):
        x = 48 + (i % 2) * 460
        y = 255 + (i // 2) * 130
        parts.append(rect_card(x, y, 420, 115, WHITE))
        parts.append(icon_badge(ic, x + 16, y + 16, 44, 26))
        parts.append(text_box(x + 72, y + 16, 330, 26, f"<p><strong>{title}</strong></p>", "headline", "left", ACCENT, 18, bold=True))
        parts.append(text_box(x + 72, y + 44, 330, 24, f"<p>{tech}</p>", "body", "left", TEXT_PRIMARY, 14))
        parts.append(text_box(x + 16, y + 72, 388, 36, f"<p>{detail}</p>", "caption", "left", TEXT_MUTED, 12))
    parts.append(slide_close())
    return "".join(parts)


def slide_architecture():
    parts = [slide_open()]
    parts.append(slide_header("System Architecture", "Three-tier: Browser → Flask API → MySQL", "iconpark/Connect/network-tree.svg"))
    boxes = [
        ("iconpark/Others/browser.svg", 80, 150, "Browser (Dashboard UI)", "app.js · index.html · CSS"),
        ("iconpark/Hardware/data-server.svg", 80, 260, "Flask Application Server", "app.py · auth · database · export · audit"),
        ("iconpark/Datas/database-network.svg", 80, 370, "MySQL 8 — listmap", "topography · dted · landused · sjung · audit_log"),
    ]
    for ic, x, y, title, sub in boxes:
        parts.append(rect_card(x, y, 760, 88, WHITE))
        parts.append(icon_badge(ic, x + 20, y + 20, 48, 28, "rgb(240, 253, 250)", ACCENT))
        parts.append(text_box(x + 84, y + 18, 640, 28, f"<p><strong>{title}</strong></p>", "headline", "left", TEXT_PRIMARY, 18, bold=True))
        parts.append(text_box(x + 84, y + 48, 640, 24, f"<p>{sub}</p>", "caption", "left", TEXT_MUTED, 12))
    parts.append(arrow_line(460, 238, 460, 260))
    parts.append(arrow_line(460, 348, 460, 370))
    parts.append(arrow_line(450, 252, 460, 260))
    parts.append(arrow_line(470, 252, 460, 260))
    parts.append(arrow_line(450, 362, 460, 370))
    parts.append(arrow_line(470, 362, 460, 370))
    parts.append(slide_close())
    return "".join(parts)


def slide_workflow():
    parts = [slide_open()]
    parts.append(slide_header("User Workflow", "Typical session from login to report export", "iconpark/Arrows/transfer-data.svg"))
    steps = [
        ("iconpark/Arrows/login.svg", "Login", "Session auth\nadmin / user"),
        ("iconpark/Datas/data-display.svg", "Browse", "Search &amp; filter\nby category"),
        ("iconpark/Character/check-one.svg", "Select", "Check rows\nacross 4 tabs"),
        ("iconpark/Charts/data-screen.svg", "Preview", "Live report\nwith ref #"),
        ("iconpark/Office/file-excel.svg", "Export", "Excel / PDF\n/ Print"),
    ]
    for i, (ic, title, desc) in enumerate(steps):
        x = 40 + i * 182
        parts.append(rect_card(x, 140, 170, 290, WHITE))
        parts.append(icon_badge(ic, x + 55, 175, 60, 36, ACCENT_SOFT, ACCENT))
        parts.append(text_box(x + 16, 250, 138, 28, f"<p><strong>{title}</strong></p>", "headline", "center", TEXT_PRIMARY, 16, bold=True))
        parts.append(text_box(x + 12, 285, 146, 70, f"<p>{desc.replace(chr(10), '</p><p>')}</p>", "body", "center", TEXT_BODY, 12))
        if i < 4:
            parts.append(arrow_line(x + 170, 300, x + 182, 300, ACCENT_LIGHT))
    parts.append(slide_close())
    return "".join(parts)


def slide_flowchart():
    mermaid = """flowchart TD
    A[User opens browser] --> B{Authenticated?}
    B -->|No| C[Login page]
    C --> D[Session created]
    B -->|Yes| E[Dashboard]
    D --> E
    E --> F[Browse categories]
    F --> G[Select records]
    G --> H[Preview report]
    H --> I{Export type?}
    I -->|Excel| J[POST /api/export/xlsx]
    I -->|PDF| K[Client html2pdf]
    I -->|Print| L[Browser print]
    J --> M[Audit log entry]
    K --> M
    L --> M"""
    parts = [
        slide_open(),
        slide_header("System Flowchart", "End-to-end request flow from auth to export", "iconpark/Connect/tree-diagram.svg"),
        f'<whiteboard topLeftX="40" topLeftY="120" width="880" height="390">'
        f"<mermaid><![CDATA[{mermaid}]]></mermaid></whiteboard>",
        slide_close(),
    ]
    return "".join(parts)


def slide_database():
    parts = [slide_open()]
    parts.append(slide_header("Database Schema", "MySQL 8 · Database: listmap · InnoDB · utf8mb4", "iconpark/Datas/database-network.svg"))
    tables = [
        ("iconpark/Charts/area-map.svg", "topography", "PK: sheetNum", "sheetName, sheetScale, release_year"),
        ("iconpark/Datas/database-point.svg", "dted", "PK: id_name", "level (INT)"),
        ("iconpark/Charts/chart-pie.svg", "landused", "PK: landused_id (AI)", "category"),
        ("iconpark/Edit/mindmap-map.svg", "sjung", "PK: sheetNum", "sheetName, sheetScale"),
        ("iconpark/Datas/data-lock.svg", "audit_log", "PK: id (AI)", "username, role, action, report_ref, details (JSON)"),
    ]
    for i, (ic, name, pk, cols) in enumerate(tables):
        x = 48 + (i % 3) * 300
        y = 120 + (i // 3) * 195
        w, h = 280, 170
        parts.append(rect_card(x, y, w, h, WHITE))
        parts.append(icon_badge(ic, x + 16, y + 14, 40, 24))
        parts.append(text_box(x + 64, y + 18, w - 80, 24, f"<p><strong>{name}</strong></p>", "headline", "left", ACCENT, 16, bold=True))
        parts.append(text_box(x + 16, y + 58, w - 32, 22, f"<p>{pk}</p>", "caption", "left", TEXT_MUTED, 11))
        parts.append(text_box(x + 16, y + 82, w - 32, 72, f"<p>{cols}</p>", "body", "left", TEXT_BODY, 12))
    parts.append(slide_close())
    return "".join(parts)


def slide_api():
    parts = [slide_open()]
    parts.append(slide_header("API &amp; Export Features", "REST endpoints and multi-format output", "iconpark/Charts/data-all.svg"))
    parts.append(rect_card(48, 115, 420, 390, WHITE))
    parts.append(icon_badge("iconpark/Connect/network-tree.svg", 68, 130, 40, 24))
    parts.append(text_box(118, 135, 340, 28, "<p><strong>REST API Endpoints</strong></p>", "headline", "left", ACCENT, 18, bold=True))
    endpoints = [
        "GET  /login — Login page",
        "GET  / — Dashboard (auth required)",
        "GET  /api/filters — Years &amp; DTED levels",
        "GET  /api/records/{cat} — Paginated records",
        "POST /api/export/xlsx — Excel export",
        "GET  /api/audit — Audit log (admin)",
    ]
    for i, ep in enumerate(endpoints):
        parts.append(icon("iconpark/Character/check-small.svg", 68, 178 + i * 42, 16, ACCENT_LIGHT))
        parts.append(text_box(92, 172 + i * 42, 360, 34, f"<p>{ep}</p>", "body", "left", TEXT_BODY, 12))
    exports = [
        ("iconpark/Office/file-excel.svg", "Excel (.xlsx)", "Server-side openpyxl workbook"),
        ("iconpark/Office/file-pdf.svg", "PDF", "Client html2pdf.js report"),
        ("iconpark/Hardware/printer-one.svg", "Print", "Browser print dialog"),
    ]
    parts.append(rect_card(500, 115, 412, 390, WHITE))
    parts.append(text_box(520, 130, 372, 28, "<p><strong>Export Formats</strong></p>", "headline", "left", ACCENT, 18, bold=True))
    for i, (ic, title, desc) in enumerate(exports):
        y = 175 + i * 115
        parts.append(rect_card(520, y, 372, 95, "rgb(248, 250, 252)"))
        parts.append(icon_badge(ic, 536, y + 18, 56, 32, ACCENT_SOFT, ACCENT))
        parts.append(text_box(606, y + 22, 270, 24, f"<p><strong>{title}</strong></p>", "body", "left", TEXT_PRIMARY, 16, bold=True))
        parts.append(text_box(606, y + 50, 270, 36, f"<p>{desc}</p>", "caption", "left", TEXT_MUTED, 12))
    parts.append(slide_close())
    return "".join(parts)


def slide_security():
    parts = [slide_open()]
    parts.append(slide_header("Security &amp; Deployment", "Auth, roles, and production setup", "iconpark/Safe/protect.svg"))
    parts.append(rect_card(48, 115, 420, 390, WHITE))
    parts.append(icon_badge("iconpark/Safe/protect.svg", 68, 130, 40, 24))
    parts.append(text_box(118, 135, 340, 28, "<p><strong>Security Features</strong></p>", "headline", "left", ACCENT, 18, bold=True))
    security_items = [
        "Session auth (8h lifetime)",
        "Role-based: admin vs user",
        "Admin-only audit log viewer",
        "API rate limiting (120/min)",
        "Constant-time password check",
        "Failed logins logged",
    ]
    for i, item in enumerate(security_items):
        parts.append(icon("iconpark/Character/check-one.svg", 68, 178 + i * 48, 20, ACCENT))
        parts.append(text_box(98, 172 + i * 48, 350, 40, f"<p>{item}</p>", "body", "left", TEXT_BODY, 13))
    parts.append(rect_card(500, 115, 412, 390, WHITE))
    parts.append(icon_badge("iconpark/Connect/link-cloud-sucess.svg", 520, 130, 40, 24))
    parts.append(text_box(570, 135, 330, 28, "<p><strong>Deployment Options</strong></p>", "headline", "left", ACCENT, 18, bold=True))
    deploy = [
        ("iconpark/Office/file-code-one.svg", "Development", "python app.py"),
        ("iconpark/Hardware/server.svg", "Production", "Waitress WSGI server"),
        ("iconpark/Connect/link-cloud-sucess.svg", "Docker", "docker compose up"),
        ("iconpark/Safe/protect.svg", "HTTPS", "nginx reverse proxy"),
        ("iconpark/Character/check-one.svg", "CI/CD", "GitHub Actions pytest"),
    ]
    for i, (ic, title, desc) in enumerate(deploy):
        y = 175 + i * 62
        parts.append(icon_badge(ic, 520, y, 36, 22, ACCENT_SOFT, ACCENT))
        parts.append(text_box(568, y + 4, 330, 28, f"<p><strong>{title}</strong> — {desc}</p>", "body", "left", TEXT_BODY, 13))
    parts.append(slide_close())
    return "".join(parts)


def slide_limitations():
    parts = [slide_open()]
    parts.append(slide_header("Limitations &amp; Summary", "Known constraints and project status", "iconpark/Base/aiming.svg"))
    parts.append(rect_card(48, 115, 420, 390, WHITE))
    parts.append(icon_badge("iconpark/Datas/database-forbid.svg", 68, 130, 40, 24))
    parts.append(text_box(118, 135, 340, 28, "<p><strong>Known Limitations</strong></p>", "headline", "left", ACCENT, 18, bold=True))
    limits = [
        "Credentials in .env — no DB user mgmt",
        "PDF export is client-side only",
        "Rate limiter uses in-memory storage",
        "Manual DB population required",
        "LIKE search — no full-text by default",
        "Single-server — no auto-scaling",
    ]
    for i, item in enumerate(limits):
        parts.append(icon("iconpark/Character/close-one.svg", 68, 178 + i * 48, 18, "rgb(239, 68, 68)"))
        parts.append(text_box(98, 172 + i * 48, 350, 40, f"<p>{item}</p>", "body", "left", TEXT_BODY, 13))
    parts.append(rect_card(500, 115, 412, 390, WHITE))
    parts.append(icon_badge("iconpark/Character/check-one.svg", 520, 130, 48, 30, "rgb(220, 252, 231)", ACCENT))
    parts.append(text_box(520, 190, 372, 160,
        "<p><strong>Project Summary</strong></p>"
        "<p>Functional internal tool for cartography dataset lookup and report generation.</p>"
        "<p><strong>Deliverables:</strong> Full-stack app, MySQL schema, Docker, tests, CI, audit logging.</p>"
        "<p><strong>Status:</strong> Production-ready with deployment guide.</p>",
        "body", "left", TEXT_BODY, 14))
    parts.append(icon_badge("iconpark/Peoples/peoples.svg", 640, 380, 56, 32, ACCENT_SOFT, ACCENT))
    parts.append(text_box(520, 450, 372, 40, "<p>Thank you — Questions?</p>", "headline", "center", ACCENT, 24, bold=True))
    parts.append(slide_close())
    return "".join(parts)


SLIDES = [
    slide_cover(),
    slide_overview(),
    slide_tech_stack(),
    slide_architecture(),
    slide_workflow(),
    slide_flowchart(),
    slide_database(),
    slide_api(),
    slide_security(),
    slide_limitations(),
]


def main():
    slides_json = json.dumps(SLIDES, ensure_ascii=False)
    cmd = [
        "lark-cli", "slides", "+create",
        "--as", "user",
        "--title", "SaP LISTMAP — System Overview",
        "--slides", slides_json,
    ]
    print("Creating enhanced Lark Slides presentation...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="/mnt/c/Users/USER/Dev/SaP")
    if result.returncode != 0:
        print("STDERR:", result.stderr, file=sys.stderr)
        print("STDOUT:", result.stdout, file=sys.stderr)
        sys.exit(result.returncode)
    print(result.stdout)
    data = json.loads(result.stdout)
    inner = data.get("data", data)
    print("\n=== Enhanced Presentation Created ===", file=sys.stderr)
    print(f"ID: {inner.get('xml_presentation_id')}", file=sys.stderr)
    if inner.get("url"):
        print(f"URL: {inner.get('url')}", file=sys.stderr)
    print(f"Slides: {inner.get('slides_added')}", file=sys.stderr)


if __name__ == "__main__":
    main()
