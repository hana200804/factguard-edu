from time import perf_counter

from rapidfuzz.fuzz import token_set_ratio

from src.models import INSUFFICIENT, SUPPORTED, Fact, Verdict
from src.utils import normalize

BASELINE_OVERLAP = 65  # Predefined lexical heuristic, not a factual confidence score.


class BaselineVerifier:
    """A question nearest-neighbour plus answer token-overlap baseline.

    It deliberately has no structured contradiction rules and cannot emit
    contradicted. This limitation is explicitly reported in the experiment.
    """

    def __init__(self, facts: list[Fact]):
        self.facts = tuple(fact for fact in facts if fact.verified)

    def verify(self, question: str, answer: str) -> Verdict:
        start = perf_counter()
        label = INSUFFICIENT
        reason = "So khớp từ đơn giản không tìm thấy câu trả lời tương ứng."
        if self.facts and normalize(question) and normalize(answer):
            ranked = sorted(self.facts, key=lambda f: -token_set_ratio(normalize(question), normalize(f.question)))
            fact = ranked[0]
            question_score = token_set_ratio(normalize(question), normalize(fact.question))
            answer_score = max(token_set_ratio(normalize(answer), normalize(a)) for a in fact.aliases)
            if question_score >= BASELINE_OVERLAP and answer_score >= BASELINE_OVERLAP:
                label = SUPPORTED
                reason = "Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn."
        return Verdict(label, reason, method="baseline", elapsed_ms=(perf_counter() - start) * 1000)
