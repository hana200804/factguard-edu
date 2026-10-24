"""Create a portable source ZIP; exclude environments, private history and uploads."""
import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".venv", "runtime", "__pycache__", ".pytest_cache", ".ruff_cache", ".git", "htmlcov", "wheelhouse", "node_modules"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="FactGuard-EDU-source.zip")
    args = parser.parse_args()
    if Path(args.name).name != args.name or not args.name.endswith(".zip"):
        raise ValueError("Archive name must be a plain .zip filename")
    destination = ROOT.parent / args.name
    paths = []
    for folder, directories, filenames in os.walk(ROOT):
        directories[:] = [d for d in directories if d not in EXCLUDED and not d.startswith("pytest-cache-files-")]
        for filename in filenames:
            path = Path(folder) / filename
            if filename != ".coverage" and path.suffix not in {".pyc", ".zip", ".log"}:
                paths.append(path)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, arcname=Path("factguard-edu") / path.relative_to(ROOT))
    with zipfile.ZipFile(destination) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC failed: {bad}")
        count = len(archive.namelist())
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    result = {"file": str(destination), "files": count, "bytes": destination.stat().st_size,
              "sha256": digest, "zip_crc_ok": True}
    destination.with_suffix(".sha256").write_text(f"{digest}  {destination.name}\n", encoding="ascii")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
