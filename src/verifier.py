import re
from datetime import date
from time import perf_counter

from src.models import (
    CONTRADICTED,
    INSUFFICIENT,
    SUPPORTED,
    UNDETERMINED,
    ClaimCheck,
    Fact,
    Verdict,
)
from src.retriever import Retriever, match_facts, question_kind
from src.utils import contains_phrase, normalize

MAX_INPUT_CHARS = 12000
MAX_DIRECT_WORDS = 32
DATE_NUMERIC = re.compile(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4})(?!\d)")
DATE_WORDS = re.compile(r"\bngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})\b")
NEGATION = ["không", "chẳng", "chưa", "không phải", "thay vì", "phủ nhận"]
UNCERTAINTY = ["có lẽ", "có thể", "hình như", "khoảng", "hoặc", "không biết", "chưa rõ"]
GLUE = set(normalize("là vào ngày tháng năm tại ở do được diễn ra tổ chức chính thức đó chính câu trả lời đáp án").split())


def extract_dates(text: str) -> tuple[list[str], bool]:
    """Read Vietnamese dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy and word dates."""
    groups = [m.groups() for m in DATE_NUMERIC.finditer(text)]
    groups += [m.groups() for m in DATE_WORDS.finditer(normalize(text))]
    values = []
    invalid = False
    for day, month, year in groups:
        try:
            values.append(date(int(year), int(month), int(day)).isoformat())
        except ValueError:
            invalid = True
    return sorted(set(values)), invalid


def answer_is_complex(answer: str) -> bool:
    normalized = normalize(answer)
    return (len(normalized.split()) > MAX_DIRECT_WORDS
            or any(contains_phrase(answer, word) for word in NEGATION)
            or any(contains_phrase(answer, word) for word in ["và", "nhưng", "ngoài ra", "đồng thời"])
            or any(c in answer for c in [";", "?", "\n"])
            or bool(re.search(r"[.!]\s+\S", answer)))


def safe_residual(answer: str, fact: Fact, aliases: tuple[str, ...], *, date_mode: bool = False) -> bool:
    """Only accept a short assertion using the question context and simple connectors.

    This is a conservative lexical guard, not a general language entailment model.
    Extra sentences or unfamiliar content cause abstention even after a value matches.
    """
    residue = answer
    if date_mode:
        residue = DATE_NUMERIC.sub(" ", residue)
        residue = DATE_WORDS.sub(" ", normalize(residue))
        residue = re.sub(r"\b\d+\b", " ", residue)
    residue = f" {normalize(residue)} "
    for alias in sorted(aliases, key=len, reverse=True):
        residue = residue.replace(f" {normalize(alias)} ", " ")
    # The reference is not used as a bag of allowable claims: only the question's
    # context may frame a direct answer. Additional assertions require review.
    allowed = set(normalize(fact.question).split()) | GLUE
    return set(residue.split()) <= allowed


class ProposedVerifier:
    def __init__(self, facts: list[Fact], retriever: Retriever):
        self.facts = list(facts)
        self.retriever = retriever

    def verify(self, question: str, answer: str) -> Verdict:
        start = perf_counter()
        evidence = self.retriever.search(question)

        def finish(label: str, reason: str, checks: tuple[ClaimCheck, ...] = ()) -> Verdict:
            return Verdict(label, reason, checks, evidence, elapsed_ms=(perf_counter() - start) * 1000,
                           metadata={"scope": "Một dữ kiện được hỏi; chưa xác minh mọi mệnh đề trong văn bản."})

        if not question.strip() or not answer.strip():
            return finish(INSUFFICIENT, "Cần nhập cả câu hỏi và câu trả lời để kiểm chứng.")
        if len(question) > MAX_INPUT_CHARS or len(answer) > MAX_INPUT_CHARS:
            return finish(UNDETERMINED, "Văn bản quá dài. Hãy tách thành câu hỏi và câu trả lời ngắn.")
        candidates = match_facts(question, self.facts)
        if not candidates:
            if question_kind(question) is None and evidence:
                return finish(UNDETERMINED, "Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.")
            return finish(INSUFFICIENT, "Chưa có dữ kiện chuẩn phù hợp với câu hỏi trong kho hiện tại.")
        verified = [fact for fact in candidates if fact.verified]
        if not verified:
            return finish(INSUFFICIENT, "Dữ kiện liên quan chưa được kiểm tra nguồn, không dùng để kết luận.")
        if len(verified) != 1:
            return finish(UNDETERMINED, "Câu hỏi có thể chỉ nhiều dữ kiện. Hãy nêu rõ sự kiện và điều cần kiểm tra.")
        fact = verified[0]
        if any(contains_phrase(answer, phrase) for phrase in UNCERTAINTY):
            return finish(INSUFFICIENT, "Câu trả lời còn suy đoán hoặc chưa đưa ra một dữ kiện xác định.")
        if answer_is_complex(answer):
            return finish(UNDETERMINED, "Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.")

        label, observed, reason = self._check_value(fact, question, answer)
        check = ClaimCheck(fact.id, fact.question, fact.answer, observed, label, reason,
                           fact.reference, fact.source_id, fact.location)
        # Include the exact adjudication evidence even if top-k retrieval misses it.
        from src.models import Document, Evidence

        if not any(item.document.id == fact.id for item in evidence):
            known = next((doc for doc in self.retriever.documents if doc.id == fact.id), None)
            if known is None:
                known = Document(fact.id, fact.source_id, fact.reference, fact.location, verified=True)
            evidence = (Evidence(known, 0.0),) + evidence[:3]
        return finish(label, reason, (check,))

    def _check_value(self, fact: Fact, question: str, answer: str) -> tuple[str, str, str]:
        if fact.kind in {"date", "year"}:
            return self._check_date(fact, question, answer)
        relevant = [alias for alias in fact.aliases if contains_phrase(answer, alias)]
        if relevant:
            if safe_residual(answer, fact, fact.aliases):
                return SUPPORTED, fact.answer, "Tên riêng khớp một cách viết đã kiểm tra trong dữ kiện tham chiếu."
            return UNDETERMINED, answer, "Có tên phù hợp nhưng còn nội dung chưa được xác minh."
        # Only known names of the same type are recognized as replacements. An
        # arbitrary unknown string is not automatically treated as a contradiction.
        alternatives = [(other, alias) for other in self.facts if other.verified and other.kind == fact.kind
                        for alias in other.aliases if contains_phrase(answer, alias)]
        for _, alias in sorted(alternatives, key=lambda item: -len(item[1])):
            if any(contains_phrase(expected, alias) for expected in fact.aliases):
                continue  # E.g. a containing city is incomplete, not false.
            if safe_residual(answer, fact, (alias,)):
                return CONTRADICTED, alias, f"Tên được nêu khác đáp án chuẩn của dữ kiện này: {fact.answer}."
        return INSUFFICIENT, answer, "Chưa nhận dạng được tên riêng đủ cụ thể để đối chiếu."

    @staticmethod
    def _check_date(fact: Fact, question: str, answer: str) -> tuple[str, str, str]:
        values, invalid = extract_dates(answer)
        years = sorted(set(re.findall(r"\b(?:1\d{3}|20\d{2})\b", answer)))
        if invalid:
            return UNDETERMINED, answer, "Câu trả lời chứa ngày không hợp lệ; cần kiểm tra cách ghi."
        year_mode = question_kind(question) == "year" or fact.kind == "year"
        if len(values) > 1 or year_mode and len(years) > 1:
            return UNDETERMINED, answer, "Có nhiều mốc thời gian, chưa xác định được mốc gắn với sự kiện."
        if year_mode:
            if not years:
                return INSUFFICIENT, answer, "Chưa nêu năm có thể kiểm tra."
            observed, expected = years[0], fact.canonical[:4]
        elif values:
            observed, expected = values[0], fact.canonical
            # A second standalone year may be a second claim despite one full date.
            if any(year != observed[:4] for year in years):
                return UNDETERMINED, answer, "Có thêm năm chưa gắn được với sự kiện."
        else:
            if years and any(year != fact.canonical[:4] for year in years) and safe_residual(answer, fact, (), date_mode=True):
                return CONTRADICTED, ", ".join(years), f"Năm được nêu khác năm trong đáp án chuẩn ({fact.answer})."
            return INSUFFICIENT, answer, "Chưa nêu đủ ngày, tháng, năm mà câu hỏi yêu cầu."
        if not safe_residual(answer, fact, (), date_mode=True):
            return UNDETERMINED, answer, "Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu."
        if observed == expected:
            return SUPPORTED, observed, "Mốc thời gian được chuẩn hóa và khớp dữ kiện có nguồn."
        return CONTRADICTED, observed, f"Mốc thời gian được nêu khác đáp án chuẩn: {fact.answer}."
