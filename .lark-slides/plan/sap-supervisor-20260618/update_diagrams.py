#!/usr/bin/env python3
"""Add use case and architecture diagram slides to SaP LISTMAP presentation."""
import json
import subprocess
import sys

PID = "H9GTsFO1UlmXmJdpLXujmLkCpxu"


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def slide_header(title, subtitle, icon="iconpark/Connect/network-tree.svg"):
    return f"""
    <shape type="rect" topLeftX="0" topLeftY="0" width="10" height="540"><fill><fillColor color="rgba(15, 118, 110, 1)"/></fill><content/></shape>
    <shape type="ellipse" topLeftX="780" topLeftY="-40" width="200" height="200"><fill><fillColor color="rgba(204, 251, 241, 1)"/></fill><content/></shape>
    <shape type="ellipse" topLeftX="820" topLeftY="400" width="160" height="160"><fill><fillColor color="rgba(240, 253, 250, 1)"/></fill><content/></shape>
    <shape type="ellipse" topLeftX="-60" topLeftY="420" width="140" height="140"><fill><fillColor color="rgba(236, 253, 245, 1)"/></fill><content/></shape>
    <shape type="ellipse" topLeftX="48" topLeftY="28" width="52" height="52"><fill><fillColor color="rgba(204, 251, 241, 1)"/></fill><content/></shape>
    <icon iconType="{icon}" topLeftX="59" topLeftY="39" width="30" height="30"><fill><fillColor color="rgba(15, 118, 110, 1)"/></fill></icon>
    <shape type="text" topLeftX="115" topLeftY="32" width="800" height="46"><content textType="title" fontSize="34" fontFamily="思源黑体" color="rgba(15, 23, 42, 1)" bold="true" textAlign="left"><p>{title}</p></content></shape>
    <shape type="text" topLeftX="115" topLeftY="78" width="800" height="28"><content fontSize="14" fontFamily="思源黑体" color="rgba(100, 116, 139, 1)" textAlign="left"><p>{subtitle}</p></content></shape>
    """


ARCH_SVG = """
<whiteboard topLeftX="48" topLeftY="115" width="864" height="400">
  <svg xmlns="http://www.w3.org/2000/svg">
    <text x="432" y="24" text-anchor="middle" font-size="13" font-weight="bold" fill="rgba(15,118,110,1)">Three-Tier Architecture</text>
    <rect x="232" y="40" width="400" height="72" rx="10" fill="rgba(204,251,241,1)" stroke="rgba(15,118,110,1)" stroke-width="2"/>
    <text x="432" y="68" text-anchor="middle" font-size="14" font-weight="bold" fill="rgba(15,23,42,1)">Browser Dashboard</text>
    <text x="432" y="88" text-anchor="middle" font-size="11" fill="rgba(100,116,139,1)">HTML · CSS · Vanilla JS · html2pdf.js</text>
    <text x="432" y="104" text-anchor="middle" font-size="10" fill="rgba(100,116,139,1)">index.html · app.js</text>
    <line x1="432" y1="112" x2="432" y2="138" stroke="rgba(15,118,110,1)" stroke-width="2"/>
    <polygon points="432,138 426,128 438,128" fill="rgba(15,118,110,1)"/>
    <text x="470" y="128" font-size="10" fill="rgba(15,118,110,1)">HTTPS REST</text>
    <rect x="182" y="138" width="500" height="88" rx="10" fill="rgba(255,255,255,1)" stroke="rgba(15,118,110,1)" stroke-width="2"/>
    <text x="432" y="168" text-anchor="middle" font-size="14" font-weight="bold" fill="rgba(15,23,42,1)">Flask Application Server</text>
    <text x="432" y="188" text-anchor="middle" font-size="11" fill="rgba(100,116,139,1)">Waitress WSGI · auth · rate limit · REST API</text>
    <text x="432" y="206" text-anchor="middle" font-size="10" fill="rgba(100,116,139,1)">app.py · export_xlsx · audit</text>
    <line x1="432" y1="226" x2="432" y2="252" stroke="rgba(15,118,110,1)" stroke-width="2"/>
    <polygon points="432,252 426,242 438,242" fill="rgba(15,118,110,1)"/>
    <text x="455" y="242" font-size="10" fill="rgba(15,118,110,1)">SQL</text>
    <rect x="202" y="252" width="460" height="88" rx="10" fill="rgba(240,253,250,1)" stroke="rgba(15,118,110,1)" stroke-width="2"/>
    <text x="432" y="282" text-anchor="middle" font-size="14" font-weight="bold" fill="rgba(15,23,42,1)">MySQL 8 — listmap</text>
    <text x="432" y="302" text-anchor="middle" font-size="11" fill="rgba(100,116,139,1)">topography · dted · landused · sjung · audit_log</text>
    <rect x="40" y="360" width="180" height="30" rx="6" fill="rgba(248,250,252,1)" stroke="rgba(226,232,240,1)" stroke-width="1"/>
    <text x="130" y="380" text-anchor="middle" font-size="10" fill="rgba(51,65,85,1)">Docker / nginx (prod)</text>
  </svg>
</whiteboard>
"""

USECASE_SVG = """
<whiteboard topLeftX="40" topLeftY="115" width="880" height="395">
  <svg xmlns="http://www.w3.org/2000/svg">
    <rect x="250" y="20" width="380" height="340" rx="16" fill="rgba(248,250,252,1)" stroke="rgba(15,118,110,1)" stroke-width="2" stroke-dasharray="8,4"/>
    <text x="440" y="48" text-anchor="middle" font-size="13" font-weight="bold" fill="rgba(15,118,110,1)">SaP LISTMAP System</text>
    <ellipse cx="340" cy="100" rx="78" ry="24" fill="rgba(255,255,255,1)" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <text x="340" y="105" text-anchor="middle" font-size="11" fill="rgba(15,23,42,1)">Login / Logout</text>
    <ellipse cx="540" cy="100" rx="78" ry="24" fill="rgba(255,255,255,1)" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <text x="540" y="105" text-anchor="middle" font-size="11" fill="rgba(15,23,42,1)">Browse Records</text>
    <ellipse cx="340" cy="165" rx="88" ry="24" fill="rgba(255,255,255,1)" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <text x="340" y="170" text-anchor="middle" font-size="11" fill="rgba(15,23,42,1)">Search and Filter</text>
    <ellipse cx="540" cy="165" rx="78" ry="24" fill="rgba(255,255,255,1)" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <text x="540" y="170" text-anchor="middle" font-size="11" fill="rgba(15,23,42,1)">Select Records</text>
    <ellipse cx="340" cy="230" rx="78" ry="24" fill="rgba(255,255,255,1)" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <text x="340" y="235" text-anchor="middle" font-size="11" fill="rgba(15,23,42,1)">Preview Report</text>
    <ellipse cx="540" cy="230" rx="105" ry="24" fill="rgba(255,255,255,1)" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <text x="540" y="235" text-anchor="middle" font-size="10" fill="rgba(15,23,42,1)">Export Excel/PDF/Print</text>
    <ellipse cx="440" cy="300" rx="82" ry="24" fill="rgba(204,251,241,1)" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <text x="440" y="305" text-anchor="middle" font-size="11" font-weight="bold" fill="rgba(15,23,42,1)">View Audit Log</text>
    <circle cx="90" cy="130" r="34" fill="rgba(204,251,241,1)" stroke="rgba(15,118,110,1)" stroke-width="2"/>
    <text x="90" y="126" text-anchor="middle" font-size="11" font-weight="bold" fill="rgba(15,23,42,1)">GIS</text>
    <text x="90" y="142" text-anchor="middle" font-size="11" font-weight="bold" fill="rgba(15,23,42,1)">Staff</text>
    <circle cx="90" cy="260" r="38" fill="rgba(240,253,250,1)" stroke="rgba(15,118,110,1)" stroke-width="2"/>
    <text x="90" y="256" text-anchor="middle" font-size="11" font-weight="bold" fill="rgba(15,23,42,1)">Admin</text>
    <text x="90" y="272" text-anchor="middle" font-size="11" font-weight="bold" fill="rgba(15,23,42,1)">istrator</text>
    <line x1="124" y1="120" x2="262" y2="100" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
    <line x1="124" y1="135" x2="262" y2="165" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
    <line x1="124" y1="145" x2="262" y2="230" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
    <line x1="124" y1="150" x2="262" y2="100" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
    <line x1="124" y1="250" x2="358" y2="300" stroke="rgba(15,118,110,1)" stroke-width="1.5"/>
    <line x1="124" y1="140" x2="455" y2="100" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
    <line x1="124" y1="155" x2="455" y2="165" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
    <line x1="124" y1="165" x2="455" y2="230" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
    <line x1="124" y1="175" x2="435" y2="230" stroke="rgba(20,184,166,1)" stroke-width="1.5"/>
  </svg>
</whiteboard>
"""


def make_slide(title, subtitle, diagram_svg, icon):
    return (
        '<slide xmlns="http://www.larkoffice.com/sml/2.0">'
        '<style><fill><fillColor color="rgba(252, 252, 253, 1)"/></fill></style><data>'
        + slide_header(title, subtitle, icon)
        + diagram_svg
        + "</data></slide>"
    )


def delete_slide(slide_id):
    return run(
        "lark-cli", "slides", "xml_presentation.slide", "delete", "--as", "user", "--yes",
        "--params", json.dumps({"xml_presentation_id": PID, "slide_id": slide_id}),
    )


def create_slide(content, before_slide_id=None):
    payload = {"slide": {"content": content}}
    if before_slide_id:
        payload["before_slide_id"] = before_slide_id
    return run(
        "lark-cli", "slides", "xml_presentation.slide", "create", "--as", "user",
        "--params", json.dumps({"xml_presentation_id": PID}),
        "--data", json.dumps(payload),
    )


def main():
    print("=== Recreate Use Case slide (pJb) ===")
    delete_slide("pJb")
    use_case = make_slide(
        "Use Case Diagram",
        "Actors and system interactions for SaP LISTMAP",
        USECASE_SVG,
        "iconpark/People/user.svg",
    )
    create_slide(use_case, before_slide_id="pJW")

    print("=== Recreate Architecture slide (pJW) ===")
    delete_slide("pJW")
    arch = make_slide(
        "System Architecture",
        "Three-tier: Browser → Flask API → MySQL",
        ARCH_SVG,
        "iconpark/Connect/network-tree.svg",
    )
    # Insert before User Workflow (pJP)
    create_slide(arch, before_slide_id="pJP")


if __name__ == "__main__":
    main()
