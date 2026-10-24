"""Separate, non-overwriting fingerprints for the v3 engine and pinned model."""
import json

from src.hybrid_verifier import HYBRID_VERSION
from src.loader import DataError
from src.nli import MODEL_DIR, MODEL_FILES, MODEL_ID, MODEL_REVISION
from src.research_evaluator import code_fingerprints, validate_freeze
from src.utils import PROJECT_ROOT, digest_bytes, utc_now

V3_FILES = ["src/hybrid_verifier.py", "src/nli.py", "src/v3_freeze.py",
            "src/annotation_study.py", "src/annotation_study_v3.py", "scripts/evaluate_v3.py",
            "reports/research_v3/protocol.json"]


def v3_code_fingerprints() -> dict[str, str]:
    return {**code_fingerprints(), **{name: digest_bytes((PROJECT_ROOT / name).read_bytes()) for name in V3_FILES}}


def _model_record() -> dict:
    files = {}
    for name, (_, expected) in MODEL_FILES.items():
        path = MODEL_DIR / name
        if not path.is_file() or digest_bytes(path.read_bytes()) != expected:
            raise DataError(f"Thiếu hoặc sai SHA-256 mô hình: {name}. Chưa thể đóng băng v3.")
        files[name] = expected
    return {"id": MODEL_ID, "revision": MODEL_REVISION, "files": files}


def freeze_v3_engine() -> dict:
    path = PROJECT_ROOT / "reports" / "research_v3" / "engine_freeze.json"
    if path.exists():
        raise DataError("Đã có bản đóng băng v3; không ghi đè. Cần phiên bản nghiên cứu mới nếu sửa mã.")
    if not validate_freeze():
        raise DataError("Mã hoặc dữ liệu v2 khác bản đóng băng; chưa thể đóng băng v3.")
    result = {"version": HYBRID_VERSION, "frozen_at": utc_now(), "files": v3_code_fingerprints(),
              "model": _model_record(), "v2_engine_matches_freeze": True,
              "note": "Records this version; chronology and independent preregistration require external evidence. Regression sets were already seen."}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError as error:
        raise DataError("Đã có bản đóng băng v3; không ghi đè.") from error
    return result


def validate_v3_freeze() -> bool:
    path = PROJECT_ROOT / "reports" / "research_v3" / "engine_freeze.json"
    if not path.is_file():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        return (record["version"] == HYBRID_VERSION and record["files"] == v3_code_fingerprints()
                and record["model"] == _model_record() and validate_freeze())
    except (OSError, ValueError, KeyError, TypeError):
        return False
