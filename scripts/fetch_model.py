"""Download the pinned NLI model files into models/ and verify SHA-256 (needs Internet once)."""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nli import MODEL_DIR, MODEL_FILES, MODEL_ID, MODEL_REVISION, model_status
from src.utils import digest_bytes


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name, ok in model_status().items():
        if ok:
            print(f"Đã có {name}")
            continue
        remote, sha = MODEL_FILES[name]
        url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{remote}"
        print(f"Đang tải {name} ...")
        content = urllib.request.urlopen(url, timeout=120).read()
        if digest_bytes(content) != sha:
            raise SystemExit(f"SHA-256 của {name} không khớp; không lưu tệp.")
        (MODEL_DIR / name).write_bytes(content)
    print("Mô hình đầy đủ và khớp SHA-256." if all(model_status().values()) else "Mô hình chưa đầy đủ.")


if __name__ == "__main__":
    main()
