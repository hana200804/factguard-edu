"""Relation-bound atomic verification with explicit uncovered-content accounting.

No pretrained language model or API is used. Grammar coverage is deliberately
finite: the program returns unresolved spans instead of declaring arbitrary prose true.
"""
import json
import re
from dataclasses import dataclass
from time import perf_counter

from src.claim_spans import (
    Span,
    ValueSpan,
    alias_spans,
    date_spans,
    phrase_spans,
    remove_spans,
    split_clauses,
)
from src.models import (
    CONTRADICTED,
    INSUFFICIENT,
    SUPPORTED,
    UNDETERMINED,
    ClaimCheck,
    Document,
    Evidence,
    Fact,
    Verdict,
)
from src.retriever import Retriever, match_facts, question_kind
from src.utils import PROJECT_ROOT, contains_phrase, normalize

RESEARCH_VERSION = "2.0.0"
CONNECTORS = set(normalize(
    "ngày tháng năm vào tại ở từ do bởi được đã là chính thức diễn ra tổ chức "
    "câu trả lời đáp án đó bản một cuộc của trong với trước tới người nhân vật "
    "không phải mà là chẳng chưa"
).split())
HEDGES = ["có lẽ", "có thể", "hình như", "khoảng", "hoặc", "ước tính", "dường như", "trước ngày", "sau ngày"]
OPEN_QUESTIONS = ["vì sao", "tại sao", "ý nghĩa", "phân tích", "đánh giá", "so sánh"]


@dataclass(frozen=True)
class Relation:
    id: str
    event_id: str
    anchors: tuple[tuple[str, ...], ...]
    slots: dict[str, str]
    context: tuple[str, ...]

    def matches(self, text: str) -> bool:
        return all(any(contains_phrase(text, alias) for alias in group) for group in self.anchors)


def load_relations(facts: list[Fact]) -> list[Relation]:
    fact_ids = {f.id for f in facts}
    rows = json.loads((PROJECT_ROOT / "data" / "relations.json").read_text(encoding="utf-8"))
    result = [Relation(row["id"], row["event_id"], tuple(tuple(g) for g in row["anchors"]),
                       {k: v for k, v in row["slots"].items() if v in fact_ids}, tuple(row["context"]))
              for row in rows if any(fid in fact_ids for fid in row["slots"].values())]
    covered = {fid for relation in result for fid in relation.slots.values()}
    result += [Relation(f"custom.{f.id}", f.event_id, f.anchors, {f.kind: f.id}, ())
               for f in facts if f.id not in covered]
    return result


def entity_dictionary(facts: list[Fact], kind: str) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Merge explicitly overlapping alias sets (e.g. HCM/NAQ), never fuzzy names."""
    groups: list[set[str]] = []
    for fact in [f for f in facts if f.kind == kind]:
        names = {normalize(a) for a in (*fact.aliases, fact.canonical)}
        overlapping = [g for g in groups if g & names]
        for group in overlapping:
            names |= group
            groups.remove(group)
        groups.append(names)
    lookup = {name: min(group) for group in groups for name in group}
    aliases = {min(group): sorted(group, key=lambda s: (-len(s), s)) for group in groups}
    return aliases, lookup


class ClaimVerifier:
    def __init__(self, facts: list[Fact], retriever: Retriever, *, guarded: bool = True):
        self.facts = list(facts)
        self.fact_map = {f.id: f for f in facts}
        self.retriever = retriever
        self.guarded = guarded
        self.relations = load_relations(facts)
        self.entities = {kind: entity_dictionary(facts, kind) for kind in ["person", "place"]}

    def _relations_for(self, text: str) -> list[Relation]:
        matches = [r for r in self.relations if r.matches(text)]
        # A broad frame is superseded only within the same event; multiple
        # unrelated event frames are never collapsed by lexical similarity.
        return [r for r in matches if not any(other.event_id == r.event_id and len(other.anchors) > len(r.anchors)
                                             for other in matches)]

    def _values(self, text: str) -> tuple[list[ValueSpan], bool]:
        dates, invalid = date_spans(text)
        return dates + [v for kind, (aliases, _) in self.entities.items()
                        for v in alias_spans(text, aliases, kind)], invalid

    def _canonical(self, fact: Fact, precision: str = "exact") -> str:
        if fact.kind in {"date", "year"}:
            return fact.canonical[:4] if precision == "year" else fact.canonical
        return self.entities[fact.kind][1].get(normalize(fact.canonical), normalize(fact.canonical))

    def _question_issues(self, question: str, relations: list[Relation]) -> list[dict]:
        if not self.guarded or not relations:
            return []
        issues = []
        asked_kind = question_kind(question)
        values, _ = self._values(question)
        for relation in relations:
            for value in values:
                if value.kind == asked_kind or asked_kind == "year" and value.kind == "date":
                    continue
                fid = relation.slots.get(value.kind)
                if fid and value.canonical != self._canonical(self.fact_map[fid], value.precision):
                    # A location in an event anchor identifies the topic rather
                    # than asserting that the checked property has that value.
                    if any(contains_phrase(alias, value.span.text) for group in relation.anchors for alias in group):
                        continue
                    issues.append({"reason": "question_premise", "text": value.span.text,
                                   "explanation": "Tiền đề trong câu hỏi khác dữ kiện tham chiếu.", "start": value.span.start, "end": value.span.end})
        # Detect an explicit unrecognized place premise rather than inheriting it.
        if asked_kind != "place":
            for match in re.finditer(r"\b(?:tại|ở|từ)\s+([^?.,;]+)", question, re.IGNORECASE):
                phrase = match.group(1)
                if any(contains_phrase(phrase, q) for q in ["đâu", "nơi nào", "địa điểm nào", "ngày nào"]):
                    continue
                places = [v for v in values if v.kind == "place" and match.start(1) <= v.span.start < match.end(1)]
                known_context = " ".join(a for r in relations for group in r.anchors for a in group)
                known_context += " " + " ".join(self.fact_map[fid].answer for r in relations for fid in r.slots.values())
                words = set(normalize(re.sub(r"\d+", "", phrase)).split()) - CONNECTORS
                if words and not places and not words <= set(normalize(known_context).split()):
                    issues.append({"reason": "unknown_question_premise", "text": phrase,
                                   "explanation": "Địa điểm trong tiền đề chưa được xác minh.", "start": match.start(1), "end": match.end(1)})
        return issues

    def _source_conflict(self, fact: Fact) -> bool:
        signature = sorted(sorted(normalize(a) for a in group) for group in fact.anchors)
        return any(other.verified and other.id != fact.id and other.event_id == fact.event_id
                   and other.kind == fact.kind
                   and sorted(sorted(normalize(a) for a in group) for group in other.anchors) == signature
                   and self._canonical(other) != self._canonical(fact) for other in self.facts)

    def verify(self, question: str, answer: str) -> Verdict:
        started = perf_counter()
        evidence = self.retriever.search(question + " " + answer, 4)
        checks: list[ClaimCheck] = []
        issues: list[dict] = []

        def result(label: str, explanation: str) -> Verdict:
            checked_ids = {c.fact_id for c in checks}
            evidence_by_id = {e.document.id: e for e in evidence}
            for fid in sorted(checked_ids):
                if fid not in evidence_by_id:
                    fact = self.fact_map[fid]
                    doc = next((d for d in self.retriever.documents if d.id == fid),
                               Document(fid, fact.source_id, fact.reference, fact.location, verified=fact.verified))
                    evidence_by_id[fid] = Evidence(doc, 0.0)
            return Verdict(label, explanation, tuple(checks), tuple(evidence_by_id.values()),
                           method="claims_guarded" if self.guarded else "claims_no_guard",
                           elapsed_ms=(perf_counter() - started) * 1000,
                           metadata={"algorithm_version": RESEARCH_VERSION, "issues": issues,
                                     "claim_count": len(checks), "unresolved_count": len(issues),
                                     "scope": "Các mệnh đề có quan hệ được nhận dạng trong kho; không phải chứng nhận sự thật toàn văn."})

        if not question.strip() or not answer.strip():
            return result(INSUFFICIENT, "Cần cả câu hỏi và câu trả lời.")
        if max(len(question), len(answer)) > 12000:
            return result(UNDETERMINED, "Văn bản vượt 12.000 ký tự; hãy chia thành đoạn ngắn hơn.")
        question_relations = self._relations_for(question)
        asked = match_facts(question, self.facts)
        if any(self._source_conflict(self.fact_map[fid]) for relation in question_relations for fid in relation.slots.values()):
            issues.append({"reason": "source_conflict", "text": question, "explanation": "Có dữ kiện cùng quan hệ nhưng trái giá trị trong kho.", "start": -1, "end": -1})
            return result(UNDETERMINED, "Kho có bằng chứng đã duyệt mâu thuẫn; cần người thẩm định trước khi kết luận.")
        issues.extend(self._question_issues(question, question_relations))
        if any(contains_phrase(question, q) for q in OPEN_QUESTIONS):
            issues.append({"reason": "open_question", "text": question, "explanation": "Câu hỏi yêu cầu phân tích vượt đối chiếu dữ kiện.", "start": -1, "end": -1})
        if self.guarded and any(i["reason"] in {"question_premise", "unknown_question_premise"} for i in issues):
            return result(UNDETERMINED, "Cần kiểm tra tiền đề câu hỏi trước khi đối chiếu câu trả lời.")
        for clause in split_clauses(answer):
            local_relations = self._relations_for(clause.text)
            explicit = bool(local_relations)
            if not local_relations and len(question_relations) == 1:
                local_relations = question_relations
            if len(local_relations) != 1:
                issues.append(self._issue(clause, "relation_ambiguous" if local_relations else "unknown_relation",
                                          "Chưa gắn được đoạn với một quan hệ lịch sử duy nhất."))
                continue
            relation = local_relations[0]
            if explicit and question_relations and relation.event_id not in {r.event_id for r in question_relations}:
                issues.append(self._issue(clause, "answer_event_mismatch", "Đoạn trả lời nói về sự kiện khác câu hỏi."))
            self._check_clause(clause, relation, question, explicit, checks, issues)
        # Answering a different attribute must not silently count as answering the question.
        if len(asked) == 1 and not any(c.fact_id == asked[0].id for c in checks):
            issues.append({"reason": "missing_requested_attribute", "text": asked[0].question,
                           "explanation": "Chưa có giá trị cho thuộc tính câu hỏi yêu cầu.", "start": -1, "end": -1})
        if any(c.label == CONTRADICTED for c in checks):
            return result(CONTRADICTED, "Phát hiện ít nhất một mệnh đề có giá trị hoặc phủ định trái với bằng chứng. Xem từng mệnh đề bên dưới.")
        if self.guarded and issues:
            if any(i["reason"] in {"open_question", "invalid_date", "relation_ambiguous", "negation_scope", "source_conflict"} for i in issues):
                return result(UNDETERMINED, "Có phần chưa thể xử lý tự động; các mệnh đề đã kiểm tra được liệt kê riêng.")
            return result(INSUFFICIENT, "Chưa đủ bằng chứng để hỗ trợ toàn bộ nội dung được hỏi; có phần chưa được đối chiếu.")
        if not checks or any(c.label != SUPPORTED for c in checks):
            return result(INSUFFICIENT, "Chưa có đủ mệnh đề có thể đối chiếu với nguồn đã xác minh.")
        return result(SUPPORTED, f"Có bằng chứng hỗ trợ {len(checks)} mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.")

    @staticmethod
    def _issue(clause: Span, reason: str, explanation: str) -> dict:
        return {"reason": reason, "text": clause.text, "explanation": explanation,
                "start": clause.start, "end": clause.end}

    def _check_clause(self, clause: Span, relation: Relation, question: str, explicit: bool,
                      checks: list[ClaimCheck], issues: list[dict]) -> None:
        values, invalid = self._values(clause.text)
        if invalid:
            issues.append(self._issue(clause, "invalid_date", "Có ngày không tồn tại hoặc sai định dạng."))
            return
        if any(contains_phrase(clause.text, hedge) for hedge in HEDGES):
            issues.append(self._issue(clause, "modality", "Đoạn có suy đoán, lựa chọn hoặc quan hệ thời gian chưa được mô hình hóa."))
            return
        negations = [s for word in ["không phải", "không", "chẳng"] for s in phrase_spans(clause.text, word)]
        pivot = phrase_spans(clause.text, "mà")
        bound = [v for v in values if v.kind in relation.slots]
        if negations and len({v.kind for v in bound}) > 1:
            issues.append(self._issue(clause, "negation_scope", "Phủ định có thể tác động nhiều quan hệ; cần người đọc xác định phạm vi."))
            return
        if any(len([v for v in bound if v.kind == kind]) > 1 for kind in relation.slots) and not (negations and pivot):
            issues.append(self._issue(clause, "relation_ambiguous", "Có nhiều giá trị cho cùng thuộc tính trong một mệnh đề."))
            return
        covered: list[Span] = []
        for value in values:
            if value.kind not in relation.slots:
                continue
            prefix = normalize(clause.text[:value.span.start])
            if self.guarded and explicit and value.kind == "person" and re.search(r"(?:^| )(?:tai|o|tu)$", prefix):
                issues.append(self._issue(clause, "wrong_role", "Tên nhân vật đang ở vị trí địa điểm; chưa gắn được vai trò trong câu."))
                continue
            if self.guarded and explicit and value.kind == "place" and not re.search(
                r"(?:^| )(?:tai|o|tu|truoc|vao|tien cong|dia diem|cu diem|de khang)$", prefix
            ):
                issues.append(self._issue(clause, "wrong_role", "Địa danh chưa có quan hệ vị trí rõ ràng trong mệnh đề."))
                continue
            fact = self.fact_map[relation.slots[value.kind]]
            if not fact.verified:
                issues.append(self._issue(clause, "unverified_source", "Dữ kiện chưa qua đối chiếu nguồn."))
                continue
            if self._source_conflict(fact):
                issues.append(self._issue(clause, "source_conflict", "Kho có các giá trị đã duyệt trái nhau cho cùng dữ kiện."))
                continue
            negated = bool(negations and any(n.end <= value.span.start for n in negations)
                           and (not pivot or value.span.end <= pivot[0].start))
            matches = value.canonical == self._canonical(fact, value.precision)
            year_incomplete = value.precision == "year" and not explicit and question_kind(question) != "year"
            label = SUPPORTED if matches != negated else CONTRADICTED
            if matches and year_incomplete:
                label = INSUFFICIENT
            explanation = ("Giá trị chuẩn hóa khớp nguồn." if label == SUPPORTED else
                           "Mệnh đề trái giá trị có nguồn hoặc phủ định giá trị đúng." if label == CONTRADICTED else
                           "Chỉ nêu năm khi câu hỏi cần đầy đủ ngày tháng năm.")
            if negated:
                explanation += " Đã đối chiếu phủ định đơn trên thuộc tính đơn trị."
            checks.append(ClaimCheck(fact.id, fact.question, fact.answer, value.span.text, label, explanation,
                                     fact.reference, fact.source_id, fact.location, clause.text,
                                     clause.start + value.span.start, clause.start + value.span.end,
                                     relation.id, negated))
            covered.append(value.span)
        if not self.guarded:
            return
        for phrase in [a for group in relation.anchors for a in group] + list(relation.context):
            covered.extend(phrase_spans(clause.text, phrase))
        residue = remove_spans(clause.text, covered)
        remaining = set(normalize(residue).split()) - CONNECTORS
        # Date/year that belongs to a relation's fixed context (e.g. conference1941)
        # is context only if it occurs in a curated question for that relation.
        expected_context = " ".join(self.fact_map[fid].question for fid in relation.slots.values())
        remaining -= {word for word in normalize(expected_context).split() if word.isdigit()}
        if remaining:
            issues.append(self._issue(clause, "uncovered_content", "Chưa xác minh các từ/ý còn lại: " + ", ".join(sorted(remaining))))
