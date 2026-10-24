"""Packaging fixtures stay inside tmp_path and never contain real collected responses."""

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts import package_project

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COLLECTION_ORIGINALS = {"cau_hoi.csv", "mau_ghi_cau_tra_loi.csv"}


def test_package_main_excludes_collected_data_and_preserves_existing_filters(tmp_path, monkeypatch, capsys):
    root = tmp_path / "isolated-project"
    collection = root / "data" / "collection"
    collection.mkdir(parents=True)
    for name in COLLECTION_ORIGINALS:
        shutil.copyfile(PROJECT_ROOT / "data" / "collection" / name, collection / name)

    included = {"README.md", "src/example.py", "data/facts.csv", "reports/example.md", ".gitignore"}
    excluded = {
        "data/collection/dot_test_tmp.csv",
        "data/collection/dot1.csv",
        "data/collection/notes.txt",
        "data/collection/nested/cau_hoi.csv",
        "data/collection/nested/mau_ghi_cau_tra_loi.csv",
        "data/collection/nested/answers.csv",
        "runtime/research.sqlite3",
        ".venv/pyvenv.cfg",
        "src/__pycache__/example.pyc",
        ".pytest_cache/state",
        ".ruff_cache/state",
        ".git/config",
        "htmlcov/index.html",
        "wheelhouse/dependency.whl",
        "node_modules/dependency/index.js",
        "pytest-cache-files-test/state",
        "src/pytest-cache-files-test/state",
        ".coverage",
        "example.pyc",
        "old-release.zip",
        "example.log",
    }
    try:
        for relative in included | excluded:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Software test fixture; not study data.\n", encoding="utf-8")

        monkeypatch.setattr(package_project, "ROOT", root)
        monkeypatch.setattr(sys, "argv", ["package_project.py", "--name", "isolated-package.zip"])
        package_project.main()

        destination = tmp_path / "isolated-package.zip"
        expected = included | {f"data/collection/{name}" for name in COLLECTION_ORIGINALS}
        with zipfile.ZipFile(destination) as archive:
            assert archive.testzip() is None
            assert set(archive.namelist()) == {f"factguard-edu/{relative}" for relative in expected}
            for name in COLLECTION_ORIGINALS:
                assert archive.read(f"factguard-edu/data/collection/{name}") == (collection / name).read_bytes()

        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        assert destination.with_suffix(".sha256").read_text(encoding="ascii") == (
            f"{digest}  {destination.name}\n"
        )
        result = json.loads(capsys.readouterr().out)
        assert result == {
            "file": str(destination), "files": len(expected), "bytes": destination.stat().st_size,
            "sha256": digest, "zip_crc_ok": True,
        }
    finally:
        (collection / "dot_test_tmp.csv").unlink(missing_ok=True)


@pytest.mark.parametrize("name", ["../outside.zip", "nested/archive.zip", "archive.txt"])
def test_package_main_rejects_non_plain_zip_names(tmp_path, monkeypatch, name):
    root = tmp_path / "isolated-project"
    root.mkdir()
    monkeypatch.setattr(package_project, "ROOT", root)
    monkeypatch.setattr(sys, "argv", ["package_project.py", "--name", name])
    with pytest.raises(ValueError, match="plain .zip filename"):
        package_project.main()
    assert list(tmp_path.iterdir()) == [root]


def test_gitignore_keeps_only_two_top_level_collection_templates(tmp_path):
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is required to verify .gitignore semantics")
    root = tmp_path / "isolated-repository"
    root.mkdir()
    shutil.copyfile(PROJECT_ROOT / ".gitignore", root / ".gitignore")
    subprocess.run([git, "init", "--quiet", str(root)], check=True, capture_output=True, timeout=30)

    ignored = [
        "data/collection/dot1.csv", "data/collection/notes.txt",
        "data/collection/nested/answers.csv", "data/collection/nested/cau_hoi.csv",
        "data/collection/nested/mau_ghi_cau_tra_loi.csv",
    ]
    visible = [f"data/collection/{name}" for name in COLLECTION_ORIGINALS]
    visible.extend(["README.md", "data/facts.csv"])
    for relative, expected_code in [(name, 0) for name in ignored] + [(name, 1) for name in visible]:
        result = subprocess.run(
            [git, "check-ignore", "--quiet", "--no-index", "--", relative],
            cwd=root, capture_output=True, text=True, check=False, timeout=30,
        )
        assert result.returncode == expected_code, (relative, result.stdout, result.stderr)
