from __future__ import annotations

from pathlib import Path


_PACKAGE_DIR = Path(__file__).resolve().parent
_SRC_APP_DIR = _PACKAGE_DIR.parent / "src" / "app"

if _SRC_APP_DIR.exists():
    __path__.append(str(_SRC_APP_DIR))
