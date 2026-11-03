import os
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
DOCS_DIR = PROJECT_ROOT / "docs"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"


def get_configured_processed_dir():
    """BIBLIO_DATA_DIR (o DATA_DIR) apunta a la carpeta 'data'; los JSON viven en <data>/processed."""
    configured = os.getenv("BIBLIO_DATA_DIR") or os.getenv("DATA_DIR")
    return (Path(configured) / "processed") if configured else PROCESSED_DIR


def get_configured_reports_dir():
    configured = os.getenv("BIBLIO_REPORTS_DIR") or os.getenv("REPORTS_DIR")
    return Path(configured) if configured else REPORTS_DIR


def get_fallback_processed_dir():
    return Path(tempfile.gettempdir()) / "bibliometria" / "processed"


def get_fallback_reports_dir():
    return Path(tempfile.gettempdir()) / "bibliometria" / "reports"


def ensure_writable_dir(preferred, fallback):
    """Si la carpeta preferida no se puede escribir (por ejemplo en Render), usa una carpeta temporal."""
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_test"
        with probe.open("w", encoding="utf-8") as handle:
            handle.write("ok")
        probe.unlink(missing_ok=True)
        return preferred
    except Exception:
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_runtime_reports_dir():
    return ensure_writable_dir(get_configured_reports_dir(), get_fallback_reports_dir())


def find_data_file(name):
    """Busca un archivo de datos primero en la carpeta configurada y luego en data/processed del repositorio."""
    candidates = (get_configured_processed_dir() / name, PROCESSED_DIR / name)
    for path in candidates:
        if path.exists():
            return path
    return None
