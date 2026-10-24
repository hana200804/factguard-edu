"""Freeze tests use an isolated source tree and tiny fake model files in tmp_path."""
import hashlib
import json
import sys

import pytest

from scripts import evaluate_v3
from src import v3_freeze
from src.loader import DataError


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    root = tmp_path / "software-test-project"
    for name in [*v3_freeze.V3_FILES, "src/v2_fixture.py"]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Software test source fixture.\n", encoding="utf-8")
    models = root / "models" / "mdeberta-xnli"
    models.mkdir(parents=True)
    entries = {}
    for name in v3_freeze.MODEL_FILES:
        payload = f"Fake software test model file: {name}".encode()
        (models / name).write_bytes(payload)
        entries[name] = (name, hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(v3_freeze, "PROJECT_ROOT", root)
    monkeypatch.setattr(v3_freeze, "MODEL_DIR", models)
    monkeypatch.setattr(v3_freeze, "MODEL_FILES", entries)
    monkeypatch.setattr(v3_freeze, "validate_freeze", lambda: True)
    monkeypatch.setattr(v3_freeze, "code_fingerprints", lambda: {
        "src/v2_fixture.py": hashlib.sha256((root / "src/v2_fixture.py").read_bytes()).hexdigest()})
    return root, models, root / "reports/research_v3/engine_freeze.json"


def test_freeze_records_sources_and_four_model_hashes_without_overwriting(workspace):
    root, models, manifest = workspace
    assert not v3_freeze.validate_v3_freeze()
    result = v3_freeze.freeze_v3_engine()
    assert result == json.loads(manifest.read_text(encoding="utf-8"))
    assert set(result["files"]) == set(v3_freeze.V3_FILES) | {"src/v2_fixture.py"}
    assert result["model"]["revision"] == v3_freeze.MODEL_REVISION
    assert len(result["model"]["files"]) == 4
    for name, digest in result["files"].items():
        assert digest == hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name, digest in result["model"]["files"].items():
        assert digest == hashlib.sha256((models / name).read_bytes()).hexdigest()
    assert v3_freeze.validate_v3_freeze()
    before = manifest.read_bytes()
    with pytest.raises(DataError, match="không ghi đè"):
        v3_freeze.freeze_v3_engine()
    assert manifest.read_bytes() == before


@pytest.mark.parametrize("relative", [
    "src/hybrid_verifier.py", "src/nli.py", "src/v3_freeze.py", "src/annotation_study_v3.py",
    "scripts/evaluate_v3.py", "src/v2_fixture.py", "reports/research_v3/protocol.json",
    "models/mdeberta-xnli/model_quantized.onnx",
])
def test_freeze_detects_changed_code_protocol_or_model(workspace, relative):
    root, _, _ = workspace
    v3_freeze.freeze_v3_engine()
    (root / relative).write_bytes(b"changed software test fixture")
    assert not v3_freeze.validate_v3_freeze()


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_freeze_requires_all_pinned_model_files(workspace, damage):
    _, models, manifest = workspace
    target = models / "tokenizer.json"
    if damage == "missing":
        target.unlink()
    else:
        target.write_bytes(b"corrupt software test tokenizer")
    with pytest.raises(DataError, match="SHA-256"):
        v3_freeze.freeze_v3_engine()
    assert not manifest.exists()


def test_freeze_requires_unchanged_v2(workspace, monkeypatch):
    _, _, manifest = workspace
    monkeypatch.setattr(v3_freeze, "validate_freeze", lambda: False)
    with pytest.raises(DataError, match="v2 khác"):
        v3_freeze.freeze_v3_engine()
    assert not manifest.exists()


def test_validation_rejects_malformed_manifest_or_v2_mismatch(workspace, monkeypatch):
    _, _, manifest = workspace
    v3_freeze.freeze_v3_engine()
    monkeypatch.setattr(v3_freeze, "validate_freeze", lambda: False)
    assert not v3_freeze.validate_v3_freeze()
    monkeypatch.setattr(v3_freeze, "validate_freeze", lambda: True)
    for content in ["not json", "{}", "[]"]:
        manifest.write_text(content, encoding="utf-8")
        assert not v3_freeze.validate_v3_freeze()
        with pytest.raises(DataError, match="không ghi đè"):
            v3_freeze.freeze_v3_engine()
        assert manifest.read_text(encoding="utf-8") == content


def test_cli_freeze_only_uses_temporary_paths_and_never_runs_regression(workspace, monkeypatch, capsys):
    root, _, manifest = workspace
    monkeypatch.setattr(sys, "argv", ["evaluate_v3.py", "--freeze"])

    def forbidden(*args, **kwargs):
        pytest.fail("Freeze must not load inference or regression data")

    monkeypatch.setattr(evaluate_v3, "shared_model", forbidden)
    monkeypatch.setattr(evaluate_v3, "load_sources", forbidden)
    evaluate_v3.main()
    assert manifest.is_file() and "engine_freeze.json" in capsys.readouterr().out
    assert not (root / "reports/research_v3/regression.json").exists()
    before = manifest.read_bytes()
    with pytest.raises(SystemExit, match="không ghi đè"):
        evaluate_v3.main()
    assert manifest.read_bytes() == before
