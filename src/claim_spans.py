"""Character-aligned extraction: every observed value points into the original answer."""
import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from src.utils import normalize


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class ValueSpan:
    kind: str
    canonical: str
    span: Span
    precision: str = "exact"


def aligned_normalize(text: str) -> tuple[str, list[int]]:
    chars, positions = [], []
    pending_space = False
    for index, char in enumerate(text):
        folded = unicodedata.normalize("NFD", char.casefold().replace("đ", "d"))
        folded = "".join(c for c in folded if unicodedata.category(c) != "Mn")
        for value in folded:
            if value.isascii() and value.isalnum():
                if pending_space and chars:
                    chars.append(" ")
                    positions.append(max(0, index - 1))
                chars.append(value)
                positions.append(index)
                pending_space = False
            else:
                pending_space = True
    return "".join(chars), positions


def phrase_spans(text: str, phrase: str) -> list[Span]:
    normalized, offsets = aligned_normalize(text)
    target = normalize(phrase)
    if not target:
        return []
    return [Span(offsets[m.start()], offsets[m.end() - 1] + 1,
                 text[offsets[m.start()]:offsets[m.end() - 1] + 1])
            for m in re.finditer(r"(?<![a-z0-9])" + re.escape(target) + r"(?![a-z0-9])", normalized)]


def split_clauses(text: str) -> list[Span]:
    # Full stops inside a numeric date never split a sentence.
    separators = re.compile(r"[;\n!?]+|(?<!\d)\.(?=\s|$)|(?<=\d)\.(?!\d)(?=\s|$)|\s+(?:và|nhưng|ngoài ra|đồng thời)\s+", re.IGNORECASE)
    spans, start = [], 0
    for match in separators.finditer(text):
        raw = text[start:match.start()]
        left = len(raw) - len(raw.lstrip())
        right = len(raw.rstrip())
        if right > left:
            spans.append(Span(start + left, start + right, raw[left:right]))
        start = match.end()
    raw = text[start:]
    left, right = len(raw) - len(raw.lstrip()), len(raw.rstrip())
    if right > left:
        spans.append(Span(start + left, start + right, raw[left:right]))
    return spans


NUMERIC_DATE = re.compile(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4})(?!\d)")
WORD_DATE = re.compile(r"\bngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})\b")


def date_spans(text: str) -> tuple[list[ValueSpan], bool]:
    normalized, offsets = aligned_normalize(text)
    matches = [(m.groups(), m.start(), m.end()) for m in NUMERIC_DATE.finditer(text)]
    matches += [(m.groups(), offsets[m.start()], offsets[m.end() - 1] + 1)
                for m in WORD_DATE.finditer(normalized)]
    values, invalid = [], False
    for (day, month, year), start, end in matches:
        try:
            canonical = date(int(year), int(month), int(day)).isoformat()
            values.append(ValueSpan("date", canonical, Span(start, end, text[start:end])))
        except ValueError:
            invalid = True
    for match in re.finditer(r"\b(?:1\d{3}|20\d{2})\b", text):
        if not any(v.span.start <= match.start() < v.span.end for v in values):
            values.append(ValueSpan("date", match.group(), Span(match.start(), match.end(), match.group()), "year"))
    unique = {(v.span.start, v.span.end, v.canonical): v for v in values}
    return sorted(unique.values(), key=lambda v: v.span.start), invalid


def alias_spans(text: str, aliases: dict[str, list[str]], kind: str) -> list[ValueSpan]:
    found = [ValueSpan(kind, canonical, span) for canonical, names in aliases.items()
             for name in names for span in phrase_spans(text, name)]
    selected = []
    for value in sorted(found, key=lambda v: (-(v.span.end - v.span.start), v.span.start, v.canonical)):
        if not any(value.span.start < other.span.end and other.span.start < value.span.end for other in selected):
            selected.append(value)
    return sorted(selected, key=lambda v: v.span.start)


def remove_spans(text: str, spans: list[Span]) -> str:
    chars = list(text)
    for span in spans:
        chars[max(0, span.start):min(len(chars), span.end)] = " " * max(0, min(len(chars), span.end) - max(0, span.start))
    return "".join(chars)
