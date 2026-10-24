"""Import real chatbot answers from a filled spreadsheet into the blind annotation queue.

Questions come from data/collection/cau_hoi.csv; answers must be pasted verbatim by a person.
Nothing here assigns labels or runs the verifier: cases enter the queue unlabelled.
"""
import csv
import io
import re
from datetime import date, datetime
from pathlib import Path

from src.loader import DataError
from src.review import ReviewRepository, content_hash
from src.utils import PROJECT_ROOT

QUESTION_BANK = PROJECT_ROOT / "data" / "collection" / "cau_hoi.csv"
TEMPLATE = PROJECT_ROOT / "data" / "collection" / "mau_ghi_cau_tra_loi.csv"
BANK_COLUMNS = ["ma_cau_hoi", "ma_su_kien", "loai", "cau_hoi", "nguon_cau_hoi"]
QUESTION_TYPES = {"don", "ket_hop", "tien_de_sai", "kiem_tra", "mo", "ngoai_kho", "thieu_du_kien"}
TEMPLATE_COLUMNS = ["ma_cau_hoi", "ma_su_kien", "cau_hoi", "cong_cu", "phien_ban", "ngay_lay",
                    "kieu_lenh", "nguoi_thu_thap", "cau_tra_loi", "ghi_chu"]
PROMPT_MODES = {"ngan_gon": "câu hỏi + 'Trả lời ngắn gọn trong 1–2 câu.'", "tu_do": "chỉ gửi câu hỏi"}
DEFAULT_TOOLS = ["ChatGPT", "Gemini"]
EARLIEST_COLLECTION = date(2022, 11, 30)
# Cells Excel produces when it evaluated or reformatted a pasted answer.
EXCEL_DAMAGE = re.compile(r"^(#(NAME\?|VALUE!|REF!|DIV/0!|N/A|NUM!|NULL!)|-?\d+([.,]\d+)?(E[+-]?\d+)?|\d{4}-\d{2}-\d{2})$", re.I)


def eligible_events(facts, development) -> set[str]:
    """Events the collected study accepts: in the bundled store and outside development, or 'outside'."""
    return {f.event_id for f in facts} - set(development["event_id"]) | {"outside"}


def read_table(path: Path) -> list[dict]:
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except OSError as error:
        raise DataError(f"Không đọc được tệp {path}.") from error
    except UnicodeDecodeError as error:
        raise DataError("Tệp không phải UTF-8. Trong Excel chọn Save As → 'CSV UTF-8 (Comma delimited)'.") from error
    header = text.splitlines()[0] if text.strip() else ""
    # Excel with a Vietnamese locale saves CSV with ';' instead of ','.
    delimiter = max([",", ";", "\t"], key=header.count)
    rows = list(csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter))
    if not rows:
        raise DataError(f"Tệp {path.name} không có dòng dữ liệu.")
    return [{(k or "").strip(): (v or "").strip() if isinstance(v, str) else "" for k, v in row.items()} for row in rows]


def load_question_bank(path: Path, allowed_events: set[str]) -> dict[str, dict]:
    rows = read_table(path)
    missing = set(BANK_COLUMNS) - set(rows[0])
    if missing:
        raise DataError(f"Ngân hàng câu hỏi thiếu cột: {', '.join(sorted(missing))}.")
    bank = {}
    for row in rows:
        if not re.fullmatch(r"Q\d{2,4}", row["ma_cau_hoi"]) or row["ma_cau_hoi"] in bank:
            raise DataError(f"Mã câu hỏi không hợp lệ hoặc bị trùng: {row['ma_cau_hoi']!r}.")
        if row["ma_su_kien"] not in allowed_events:
            raise DataError(f"{row['ma_cau_hoi']}: sự kiện {row['ma_su_kien']!r} không có trong kho hoặc thuộc development.")
        if row["loai"] not in QUESTION_TYPES or not row["cau_hoi"] or not row["nguon_cau_hoi"]:
            raise DataError(f"{row['ma_cau_hoi']}: thiếu câu hỏi/nguồn câu hỏi hoặc loại không hợp lệ.")
        bank[row["ma_cau_hoi"]] = row
    return bank


def template_rows(bank: dict[str, dict], tools: list[str]) -> list[dict]:
    return [{"ma_cau_hoi": q["ma_cau_hoi"], "ma_su_kien": q["ma_su_kien"], "cau_hoi": q["cau_hoi"], "cong_cu": tool,
             "phien_ban": "", "ngay_lay": "", "kieu_lenh": "ngan_gon", "nguoi_thu_thap": "", "cau_tra_loi": "", "ghi_chu": ""}
            for q in bank.values() for tool in tools]


def write_template(path: Path, rows: list[dict]) -> None:
    if path.exists() and any(row.get("cau_tra_loi") for row in read_table(path)):
        raise DataError(f"{path.name} đã có câu trả lời được điền; không ghi đè. Chọn tên tệp khác.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, TEMPLATE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_date(value: str, today: date) -> str:
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            parsed = datetime.strptime(value, pattern).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError("ngay_lay cần dạng YYYY-MM-DD hoặc ngày/tháng/năm")
    if not EARLIEST_COLLECTION <= parsed <= today:
        raise ValueError(f"ngay_lay {parsed.isoformat()} nằm ngoài khoảng hợp lý")
    return parsed.isoformat()


def parse_answers(rows: list[dict], bank: dict[str, dict], today: date | None = None) -> tuple[list[dict], list[str], int]:
    """Return (cases, errors, blank_rows). Rows without an answer are skipped, not errors."""
    today = today or date.today()
    missing = set(TEMPLATE_COLUMNS) - set(rows[0]) - {"ghi_chu"}
    if missing:
        return [], [f"Thiếu cột: {', '.join(sorted(missing))}."], 0
    cases, errors, blank, seen = [], [], 0, {}
    for index, row in enumerate(rows):
        where = f"Dòng {index + 2}"  # header is spreadsheet row 1
        if not row["cau_tra_loi"]:
            blank += 1
            continue
        question = bank.get(row["ma_cau_hoi"])
        problems = []
        if question is None:
            problems.append(f"mã câu hỏi {row['ma_cau_hoi']!r} không có trong ngân hàng")
        else:
            if " ".join(row["cau_hoi"].split()) != " ".join(question["cau_hoi"].split()):
                problems.append("câu hỏi khác ngân hàng; nếu đã hỏi cách khác, thêm mã câu hỏi mới")
            if row["ma_su_kien"] != question["ma_su_kien"]:
                problems.append("ma_su_kien khác ngân hàng")
        for column in ["cong_cu", "phien_ban", "nguoi_thu_thap"]:
            if not row[column]:
                problems.append(f"thiếu {column} (ghi 'không rõ' nếu không biết phiên bản)")
        if row["kieu_lenh"] not in PROMPT_MODES:
            problems.append(f"kieu_lenh chỉ nhận {', '.join(PROMPT_MODES)}")
        try:
            collected_on = parse_date(row["ngay_lay"], today)
        except ValueError as error:
            problems.append(str(error))
            collected_on = ""
        if len(row["cau_tra_loi"]) > 12000:
            problems.append("câu trả lời vượt 12.000 ký tự")
        if EXCEL_DAMAGE.fullmatch(row["cau_tra_loi"]):
            problems.append("câu trả lời trông như Excel đã đổi thành số/ngày/lỗi công thức; dán lại dạng văn bản")
        signature = content_hash(row["cau_hoi"], row["cau_tra_loi"])
        if signature in seen:
            problems.append(f"trùng nguyên văn với dòng {seen[signature]}")
        seen.setdefault(signature, index + 2)
        if problems:
            errors.append(f"{where} ({row['ma_cau_hoi'] or 'không mã'}): " + "; ".join(problems) + ".")
            continue
        assert question is not None
        origin = (f"{row['cong_cu']} / phiên bản {row['phien_ban']} / lấy ngày {collected_on} / "
                  f"lệnh {row['kieu_lenh']} / câu {row['ma_cau_hoi']} ({question['loai']}, đặt bởi {question['nguon_cau_hoi']})")
        if row.get("ghi_chu"):
            origin += f" / ghi chú: {row['ghi_chu']}"
        cases.append({"row": index + 2, "qid": row["ma_cau_hoi"], "question": row["cau_hoi"], "answer": row["cau_tra_loi"],
                      "origin": origin, "submitter": row["nguoi_thu_thap"], "event_id": row["ma_su_kien"]})
    return cases, errors, blank


def import_cases(repository: ReviewRepository, cases: list[dict]) -> list[dict]:
    existing = {row["content_hash"]: row["id"] for row in repository.collected_cases()}
    log = []
    for case in cases:
        signature = content_hash(case["question"], case["answer"])
        if signature in existing:
            log.append({"row": case["row"], "qid": case["qid"], "case_id": existing[signature], "status": "đã có, bỏ qua"})
            continue
        identifier = repository.add_case(question=case["question"], answer=case["answer"], origin=case["origin"],
                                         submitter=case["submitter"], event_id=case["event_id"])
        existing[signature] = identifier
        log.append({"row": case["row"], "qid": case["qid"], "case_id": identifier, "status": "đã nhập"})
    return log
