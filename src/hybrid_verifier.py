"""v3: rule verifier (v2, unchanged) + offline NLI only for clauses the rules left unresolved.

Rules stay authoritative for every date/person/place value. NLI may resolve a clause only when
all values in it are already present in the premise (value guard), because the model alone
treats swapped names such as "Võ Nguyên Giáp đọc Tuyên ngôn Độc lập" as entailed.
Thresholds are fixed in reports/research_v3/protocol.json before any measurement.
"""
import re
from dataclasses import replace
from time import perf_counter

from src.claim_verifier import ClaimVerifier
from src.models import CONTRADICTED, INSUFFICIENT, SUPPORTED, UNDETERMINED, Fact, Verdict
from src.nli import NliModel
from src.retriever import Retriever
from src.utils import contains_phrase, normalize

HYBRID_VERSION = "3.0.0-dev"
ENTAIL_MIN = 0.80
CONTRADICT_MIN = 0.90
# Only these v2 issues describe content the rules could not read; all others are deliberate stops.
RESOLVABLE = {"uncovered_content", "unknown_relation"}
UNDETERMINED_REASONS = {"open_question", "invalid_date", "relation_ambiguous", "negation_scope", "source_conflict"}


class HybridVerifier:
    def __init__(self, facts: list[Fact], retriever: Retriever, nli: NliModel):
        self.rules = ClaimVerifier(facts, retriever)
        self.nli = nli
        self.facts = list(facts)

    def _premise_facts(self, question: str, verdict: Verdict, clause: str) -> list[Fact]:
        events = {r.event_id for r in self.rules._relations_for(question)}
        events |= {r.event_id for r in self.rules._relations_for(clause)}
        events |= {self.rules.fact_map[c.fact_id].event_id for c in verdict.checks}
        if not events:
            # Fallback: one anchor group of a relation names the event (e.g. "điện biên phủ" without
            # "kết thúc"). Used only when exactly one event matches; generic anchors stay ambiguous.
            # Single-word anchors ("đến", "huế") are too generic to name an event on their own.
            partial = {r.event_id for r in self.rules.relations for group in r.anchors for a in group
                       if len(normalize(a).split()) >= 2 and (contains_phrase(question, a) or contains_phrase(clause, a))}
            events = partial if len(partial) == 1 else set()
        return [f for f in self.facts if f.event_id in events and f.verified]

    def _value_guard(self, clause: str, premise: str, premise_facts: list[Fact]) -> bool:
        values, invalid = self.rules._values(clause)
        if invalid:
            return False
        known = {(f.kind if f.kind != "year" else "date", self.rules._canonical(f)) for f in premise_facts}
        for value in values:
            canonical = value.canonical if value.precision != "year" else value.canonical[:4]
            kind = "date" if value.kind in {"date", "year"} else value.kind
            if not any(k == kind and (c == canonical or value.precision == "year" and c[:4] == canonical) for k, c in known):
                return False
        # Bare numbers (years, decree numbers) and capitalised words (names outside the entity
        # dictionary, e.g. "Văn Tiến Dũng") must also occur in the premise.
        premise_words = set(normalize(premise).split())
        if not all(word in premise_words for word in normalize(clause).split() if word.isdigit()):
            return False
        capitalised = [w for w in re.findall(r"\w+", clause)[1:] if w[0].isupper()]
        return all(set(normalize(w).split()) <= premise_words for w in capitalised)

    def verify(self, question: str, answer: str) -> Verdict:
        started = perf_counter()
        base = self.rules.verify(question, answer)
        issues = list(base.metadata.get("issues", []))
        trace: list[dict] = []
        if base.label in {SUPPORTED, CONTRADICTED} or any(i["reason"] not in RESOLVABLE | {"missing_requested_attribute"} for i in issues):
            return self._finish(base, base.label, base.explanation, issues, trace, started)
        open_issues, nli_contradiction, nli_support = [], False, 0
        for issue in issues:
            if issue["reason"] not in RESOLVABLE:
                open_issues.append(issue)
                continue
            facts = self._premise_facts(question, base, issue["text"])
            if not facts:
                open_issues.append(issue)
                trace.append({"text": issue["text"], "decision": "no_premise"})
                continue
            premise = " ".join(dict.fromkeys(f.reference for f in facts))
            score = self.nli.score([(premise, issue["text"])])[0]
            guard = self._value_guard(issue["text"], premise, facts)
            decision = "unresolved"
            if score.contradiction >= CONTRADICT_MIN:
                decision, nli_contradiction = "contradiction", True
            elif score.entailment >= ENTAIL_MIN and guard:
                decision, nli_support = "entailment", nli_support + 1
            elif score.entailment >= ENTAIL_MIN:
                decision = "blocked_by_value_guard"
            if decision not in {"entailment"}:
                open_issues.append({**issue, "nli": decision})
            trace.append({"text": issue["text"], "decision": decision, "guard": guard, "fact_ids": [f.id for f in facts],
                          "entailment": score.entailment, "neutral": score.neutral, "contradiction": score.contradiction})
        if nli_contradiction:
            return self._finish(base, CONTRADICTED, "Mô hình NLI đánh giá một đoạn chưa đọc được bằng luật là trái với bằng chứng cùng sự kiện. Cần người đọc xác nhận.", open_issues, trace, started)
        if not open_issues and (base.checks or nli_support) and all(c.label == SUPPORTED for c in base.checks):
            return self._finish(base, SUPPORTED, f"{len(base.checks)} mệnh đề khớp luật và {nli_support} đoạn được NLI xác nhận có trong bằng chứng, sau chốt giá trị.", open_issues, trace, started)
        label = UNDETERMINED if any(i["reason"] in UNDETERMINED_REASONS for i in open_issues) else INSUFFICIENT
        return self._finish(base, label, base.explanation if label == base.label else "Vẫn còn phần chưa được đối chiếu sau bước NLI.", open_issues, trace, started)

    @staticmethod
    def _finish(base: Verdict, label: str, explanation: str, issues: list[dict], trace: list[dict], started: float) -> Verdict:
        metadata = {**base.metadata, "algorithm_version": HYBRID_VERSION, "issues": issues, "unresolved_count": len(issues),
                    "rules_label": base.label, "nli_trace": trace}
        return replace(base, label=label, explanation=explanation, method="hybrid_v3",
                       elapsed_ms=(perf_counter() - started) * 1000, metadata=metadata)
