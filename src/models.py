from dataclasses import asdict, dataclass, field
from typing import Any

SUPPORTED = "supported"
CONTRADICTED = "contradicted"
INSUFFICIENT = "insufficient"
UNDETERMINED = "undetermined"
GOLD_LABELS = [SUPPORTED, CONTRADICTED, INSUFFICIENT]
ALL_LABELS = GOLD_LABELS + [UNDETERMINED]
LABELS_VI = {
    SUPPORTED: "Có bằng chứng hỗ trợ",
    CONTRADICTED: "Mâu thuẫn với bằng chứng",
    INSUFFICIENT: "Chưa đủ bằng chứng",
    UNDETERMINED: "Không thể tự động kết luận",
}


@dataclass(frozen=True)
class Fact:
    id: str
    topic: str
    event_id: str
    question: str
    answer: str
    kind: str
    canonical: str
    aliases: tuple[str, ...]
    anchors: tuple[tuple[str, ...], ...]
    reference: str
    source_id: str
    location: str
    verified: bool


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    location: str
    url: str = ""
    verified: bool = False


@dataclass(frozen=True)
class Evidence:
    document: Document
    similarity: float


@dataclass(frozen=True)
class ClaimCheck:
    fact_id: str
    question: str
    expected: str
    observed: str
    label: str
    explanation: str
    reference: str
    source_id: str
    location: str
    claim_text: str = ""
    span_start: int = -1
    span_end: int = -1
    relation: str = ""
    negated: bool = False


@dataclass(frozen=True)
class Verdict:
    label: str
    explanation: str
    checks: tuple[ClaimCheck, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    method: str = "proposed"
    elapsed_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
