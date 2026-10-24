import hashlib
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALGORITHM_VERSION = "1.0.0"


def normalize(text: str) -> str:
    """Accent/case insensitive tokens, with Vietnamese đ handled explicitly."""
    text = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"[a-z0-9]+", text))


def contains_phrase(text: str, phrase: str) -> bool:
    return f" {normalize(phrase)} " in f" {normalize(text)} "


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def runtime_dir() -> Path:
    path = Path(os.environ.get("FACTGUARD_RUNTIME_DIR", str(PROJECT_ROOT / "runtime")))
    path.mkdir(parents=True, exist_ok=True)
    return path


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def csv_safe(value: Any) -> Any:
    # Prevent formula evaluation when a result is opened in Excel.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value
