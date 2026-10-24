"""Offline multilingual NLI (mDeBERTa-v3 XNLI, quantized ONNX) on CPU.

The model files are not shipped in Git/ZIP; fetch them with scripts/fetch_model.py.
Every file is checked against the pinned SHA-256 before the session starts.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from src.loader import DataError
from src.utils import PROJECT_ROOT, digest_bytes

MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
MODEL_REVISION = "b5113eb38ab63efdd7f280f8c144ea8b13f978ce"
MODEL_DIR = PROJECT_ROOT / "models" / "mdeberta-xnli"
# local name -> (path inside the Hugging Face repo, sha256)
MODEL_FILES = {
    "model_quantized.onnx": ("onnx/model_quantized.onnx", "18307c3bcb5d896a624c077af061b259d341829f3d13c8b3d49a044e28d4fe6a"),
    "tokenizer.json": ("tokenizer.json", "e23095eb61ba944c7be3a5d3e8ec19e37ce7ced0daa03550bde03e83c21b3f8a"),
    "config.json": ("config.json", "bc7b85f164a17c1b007d87fb99d3676f4a4d2e6511d2288dd3f5334dc0f34e6b"),
    "LICENSE": ("LICENSE", "655d75c66aadf109f3e3fe6175810c977e642a027f1dcf227463a0ccb3873d2a"),
}
LABELS = ("entailment", "neutral", "contradiction")  # config.json id2label order
MAX_TOKENS = 256


@dataclass(frozen=True)
class NliScore:
    entailment: float
    neutral: float
    contradiction: float

    @property
    def label(self) -> str:
        return max(LABELS, key=lambda name: getattr(self, name))


def model_status(directory: Path = MODEL_DIR) -> dict[str, bool]:
    return {name: (directory / name).is_file() and digest_bytes((directory / name).read_bytes()) == sha
            for name, (_, sha) in MODEL_FILES.items()}


class NliModel:
    def __init__(self, directory: Path = MODEL_DIR):
        bad = [name for name, ok in model_status(directory).items() if not ok]
        if bad:
            raise DataError(f"Thiếu hoặc sai mã SHA-256 tệp mô hình: {', '.join(bad)}. Chạy scripts/fetch_model.py.")
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        self.tokenizer.enable_truncation(MAX_TOKENS)
        self.tokenizer.enable_padding(pad_id=0)
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        self.session = ort.InferenceSession(str(directory / "model_quantized.onnx"), options, providers=["CPUExecutionProvider"])

    def score(self, pairs: list[tuple[str, str]]) -> list[NliScore]:
        """pairs = [(premise, hypothesis)]; deterministic on the same CPU build."""
        if not pairs:
            return []
        encodings = self.tokenizer.encode_batch(pairs)
        ids = np.array([e.ids for e in encodings], dtype=np.int64)
        mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        logits = np.asarray(self.session.run(["logits"], {"input_ids": ids, "attention_mask": mask})[0])
        exp = np.exp(logits - logits.max(axis=1, keepdims=True))
        probs = exp / exp.sum(axis=1, keepdims=True)
        return [NliScore(*(round(float(p), 6) for p in row)) for row in probs]


@lru_cache(maxsize=1)
def shared_model() -> NliModel:
    return NliModel()
