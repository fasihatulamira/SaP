"""Shared export download naming for GIS Info / KEMBARAN I."""

DEFAULT_SUBTITLE = "EKSESAIS LATIHAN TAHUN 2026"
EXPORT_PREFIX = "KEMBARAN I - GIS INFO"


def build_export_basename(subtitle=None):
    """
    Build download basename: 'KEMBARAN I - GIS INFO {subtitle}'.

    Example: KEMBARAN I - GIS INFO EKSESAIS LATIHAN TAHUN 2026
    """
    text = " ".join(str(subtitle or DEFAULT_SUBTITLE).split()).strip() or DEFAULT_SUBTITLE
    return f"{EXPORT_PREFIX} {text}"


def build_export_filename(subtitle=None, extension="pdf"):
    """Basename + extension (extension with or without leading dot)."""
    ext = str(extension or "pdf").lstrip(".")
    return f"{build_export_basename(subtitle)}.{ext}"
