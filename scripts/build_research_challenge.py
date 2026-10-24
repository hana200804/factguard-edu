"""Author a published synthetic challenge AFTER freezing the verification engine.

Labels are specified here by the author, never inferred from model predictions.
This is not an independent human-labelled evaluation. Do not overwrite after scoring.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.research_evaluator import validate_freeze
from src.utils import digest_bytes, utc_now

ROOT = Path(__file__).resolve().parents[1]
Q = "Kiểm chứng các dữ kiện lịch sử sau."


def g(fid, value, label="supported", negated=False):
    return dict(fact_id=fid, value=value, label=label, negated=negated)


def main():
    if not validate_freeze():
        raise SystemExit("Freeze the engine before authoring a challenge.")
    directory = ROOT / "data" / "research"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "challenge.jsonl"
    if destination.exists():
        raise SystemExit("Challenge already exists; create a NEW version, do not overwrite scored labels.")
    rows = []

    def add(event, group, answer, label, gold, question=Q, exclude=""):
        rows.append(dict(id=f"R{len(rows) + 1:03}", question=question, answer=answer, label=label,
                         event_id=event, group=group, gold_claims=gold, exclude_event=exclude,
                         origin="assistant-authored synthetic challenge", created_at=utc_now()))

    add("independence1945", "Nhiều dữ kiện đúng", "Chủ tịch Hồ Chí Minh đọc bản Tuyên ngôn Độc lập ngày 02-09-1945 tại Quảng trường Ba Đình.", "supported",
        [g("F001", "02-09-1945"), g("F002", "Chủ tịch Hồ Chí Minh"), g("F003", "Quảng trường Ba Đình")])
    add("independence1945", "Đúng một phần", "Trần Phú đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Quảng trường Ba Đình.", "contradicted",
        [g("F001", "2/9/1945"), g("F002", "Trần Phú", "contradicted"), g("F003", "Quảng trường Ba Đình")])
    add("independence1945", "Đúng một phần", "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1946 tại Quảng trường Ba Đình.", "contradicted",
        [g("F001", "2/9/1946", "contradicted"), g("F002", "Hồ Chí Minh"), g("F003", "Quảng trường Ba Đình")])
    add("independence1945", "Đúng một phần", "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Him Lam.", "contradicted",
        [g("F001", "2/9/1945"), g("F002", "Hồ Chí Minh"), g("F003", "Him Lam", "contradicted")])
    add("independence1945", "Phủ định đơn", "Không phải ngày 03/09/1945 mà là ngày 02/09/1945.", "supported",
        [g("F001", "03/09/1945", negated=True), g("F001", "02/09/1945")],
        question="Tuyên ngôn Độc lập được đọc vào ngày nào?")
    add("independence1945", "Phủ định đơn", "Không phải ngày 02-09-1945 mà là ngày 03-09-1945.", "contradicted",
        [g("F001", "02-09-1945", "contradicted", True), g("F001", "03-09-1945", "contradicted")],
        question="Tuyên ngôn Độc lập được đọc vào ngày nào?")
    add("independence1945", "Phủ định phức tạp", "Hồ Chí Minh không đọc Tuyên ngôn Độc lập tại Quảng trường Ba Đình ngày 2/9/1945.", "contradicted",
        [g("F002", "Hồ Chí Minh", "contradicted", True)])
    add("independence1945", "Nội dung thêm ngoài nguồn", "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945. Người ngoài hành tinh giúp tổ chức sự kiện này.", "insufficient",
        [g("F001", "2/9/1945"), g("F002", "Hồ Chí Minh")])
    add("independence1945", "Tiền đề câu hỏi sai", "Chủ tịch Hồ Chí Minh.", "insufficient", [],
        question="Ai đọc Tuyên ngôn Độc lập tại Him Lam năm 1945?")
    add("independence1945", "Tiền đề câu hỏi sai", "Hồ Chí Minh.", "insufficient", [],
        question="Ai đọc Tuyên ngôn Độc lập tại Sao Hỏa năm 1945?")
    add("independence1945", "Đổi vai trò trong câu", "Quảng trường Ba Đình đọc Tuyên ngôn Độc lập tại Hồ Chí Minh vào ngày 2/9/1945.", "insufficient",
        [g("F001", "2/9/1945")])
    add("independence1945", "Độ chi tiết thời gian", "Tuyên ngôn Độc lập được đọc năm 1945.", "supported", [g("F001", "1945")])
    add("independence1945", "Độ chi tiết thời gian", "Vào năm 1945, chưa xác định ngày tháng.", "insufficient", [],
        question="Tuyên ngôn Độc lập được đọc vào ngày nào?")
    add("independence1945", "Thu hồi bằng chứng", "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945.", "insufficient", [], exclude="independence1945")
    add("dbp1954", "Nhiều mốc khác quan hệ", "Chiến dịch Điện Biên Phủ bắt đầu ngày 13/3/1954; Chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1954.", "supported",
        [g("F015", "13/3/1954"), g("F016", "7/5/1954")])
    add("dbp1954", "Hoán đổi mốc giữa quan hệ", "Chiến dịch Điện Biên Phủ bắt đầu ngày 7/5/1954; Chiến dịch Điện Biên Phủ kết thúc ngày 13/3/1954.", "contradicted",
        [g("F015", "7/5/1954", "contradicted"), g("F016", "13/3/1954", "contradicted")])
    add("dbp1954", "Đúng một phần", "Chiến dịch Điện Biên Phủ bắt đầu ngày 13/3/1954; Chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1953.", "contradicted",
        [g("F015", "13/3/1954"), g("F016", "7/5/1953", "contradicted")])
    add("dbp1954", "Đồng tham chiếu lược chủ ngữ", "Chiến dịch Điện Biên Phủ bắt đầu ngày 13/3/1954 và kết thúc ngày 7/5/1954.", "supported",
        [g("F015", "13/3/1954"), g("F016", "7/5/1954")])
    add("dbp1954", "Nhân vật trong câu đầy đủ", "Đại tướng Võ Nguyên Giáp chỉ huy chiến dịch Điện Biên Phủ.", "supported", [g("F017", "Đại tướng Võ Nguyên Giáp")])
    add("dbp1954", "Nhân vật trong câu đầy đủ", "Trần Phú chỉ huy chiến dịch Điện Biên Phủ.", "contradicted", [g("F017", "Trần Phú", "contradicted")])
    add("dbp1954", "Nhiều dữ kiện đúng", "Trận mở màn chiến dịch Điện Biên Phủ tiến công Him Lam ngày 13 tháng 3 năm 1954.", "supported",
        [g("F015", "ngày 13 tháng 3 năm 1954"), g("F018", "Him Lam")])
    add("dbp1954", "Không xác định dữ kiện", "Có thể chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1954.", "insufficient", [])
    add("dbp1954", "Nội dung thêm ngoài nguồn", "Chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1954 và mọi quốc gia đều đổi lịch học ngay hôm đó.", "insufficient", [g("F016", "7/5/1954")])
    add("dbp1954", "Thu hồi bằng chứng", "Đại tướng Võ Nguyên Giáp chỉ huy chiến dịch Điện Biên Phủ.", "insufficient", [],
        question="Ai chỉ huy chiến dịch Điện Biên Phủ?", exclude="dbp1954")
    add("hanoi1945", "Câu sự kiện đầy đủ", "Khởi nghĩa giành chính quyền ở Hà Nội thắng lợi ngày 19/8/1945.", "supported", [g("F007", "19/8/1945")])
    add("hanoi1945", "Sai ngày cùng năm", "Khởi nghĩa giành chính quyền ở Hà Nội thắng lợi ngày 18/8/1945.", "contradicted", [g("F007", "18/8/1945", "contradicted")])
    add("hue1945", "Câu sự kiện đầy đủ", "Khởi nghĩa giành chính quyền ở Huế thắng lợi ngày 23-08-1945.", "supported", [g("F009", "23-08-1945")])
    add("hue1945", "Hoán đổi địa phương", "Khởi nghĩa giành chính quyền ở Huế thắng lợi ngày 19/8/1945.", "contradicted", [g("F009", "19/8/1945", "contradicted")])
    add("saigon1945", "Câu sự kiện đầy đủ", "Khởi nghĩa giành chính quyền ở Sài Gòn thắng lợi ngày 25/8/1945.", "supported", [g("F010", "25/8/1945")])
    add("saigon1945", "Hoán đổi địa phương", "Khởi nghĩa giành chính quyền ở Sài Gòn thắng lợi ngày 23/8/1945.", "contradicted", [g("F010", "23/8/1945", "contradicted")])
    add("abdication1945", "Nhiều dữ kiện đúng", "Lễ thoái vị của vua Bảo Đại tổ chức ngày 30/8/1945 tại lầu Ngọ Môn.", "supported",
        [g("F011", "30/8/1945"), g("F012", "vua Bảo Đại"), g("F013", "lầu Ngọ Môn")])
    add("abdication1945", "Đúng một phần", "Lễ thoái vị của Bảo Đại tổ chức ngày 30/8/1945 tại Nhà hát lớn Hà Nội.", "contradicted",
        [g("F011", "30/8/1945"), g("F012", "Bảo Đại"), g("F013", "Nhà hát lớn Hà Nội", "contradicted")])
    add("party1930", "Câu sự kiện đầy đủ", "Đảng Cộng sản Việt Nam chính thức thành lập ngày 3/2/1930.", "supported", [g("F019", "3/2/1930")])
    add("party1930", "Sai ngày cùng năm", "Đảng Cộng sản Việt Nam thành lập ngày 4/2/1930.", "contradicted", [g("F019", "4/2/1930", "contradicted")])
    add("party1930", "Nhiều dữ kiện đúng", "Nguyễn Ái Quốc chủ trì hội nghị hợp nhất thành lập Đảng Cộng sản Việt Nam tại Hương Cảng.", "supported",
        [g("F020", "Nguyễn Ái Quốc"), g("F021", "Hương Cảng")])
    add("party1930", "Đúng một phần", "Trần Phú chủ trì hội nghị hợp nhất thành lập Đảng Cộng sản Việt Nam tại Hương Cảng.", "contradicted",
        [g("F020", "Trần Phú", "contradicted"), g("F021", "Hương Cảng")])
    add("decree1945", "Nhiều mốc khác quan hệ", "Sắc lệnh số 76 ban hành ngày 18/12/1945. Sắc lệnh số 76 hoãn tổng tuyển cử đến ngày 6/1/1946.", "supported",
        [g("F023", "18/12/1945"), g("F025", "6/1/1946")])
    add("decree1945", "Hoán đổi mốc giữa quan hệ", "Sắc lệnh số 76 ban hành ngày 6/1/1946. Sắc lệnh số 76 hoãn tổng tuyển cử đến ngày 18/12/1945.", "contradicted",
        [g("F023", "6/1/1946", "contradicted"), g("F025", "18/12/1945", "contradicted")])
    add("decree1945", "Nhân vật trong câu đầy đủ", "Chủ tịch Hồ Chí Minh ký Sắc lệnh số 76.", "supported", [g("F024", "Chủ tịch Hồ Chí Minh")])
    add("decree1945", "Nhân vật trong câu đầy đủ", "Bảo Đại ký Sắc lệnh số 76.", "contradicted", [g("F024", "Bảo Đại", "contradicted")])
    add("saigonindependence1945", "Câu sự kiện đầy đủ", "Lễ Độc lập tại Sài Gòn tổ chức ngày 2/9/1945 ở quảng trường Norodom.", "supported",
        [g("F006", "2/9/1945"), g("F005", "quảng trường Norodom")])
    add("saigonindependence1945", "Nhầm địa điểm", "Lễ Độc lập tại Sài Gòn tổ chức ngày 2/9/1945 ở Quảng trường Ba Đình.", "contradicted",
        [g("F006", "2/9/1945"), g("F005", "Quảng trường Ba Đình", "contradicted")])
    add("outside", "Sự kiện ngoài kho", "Hiệp định Paris được ký ngày 27/1/1973.", "insufficient", [])
    add("outside", "Sự kiện ngoài kho", "Ngô Quyền chỉ huy chiến thắng Bạch Đằng năm 938.", "insufficient", [])
    add("outside", "Suy luận ngoài phạm vi", "Mọi câu trả lời AI về lịch sử đều sai.", "insufficient", [])
    add("outside", "Thiếu dữ kiện để đối chiếu", "Đó là một sự kiện rất nổi tiếng.", "insufficient", [])
    old = set()
    with (ROOT / "data" / "evaluation.csv").open(encoding="utf-8-sig", newline="") as handle:
        old = {(r["question"], r["answer"]) for r in csv.DictReader(handle)}
    if any((row["question"], row["answer"]) in old for row in rows):
        raise SystemExit("Challenge duplicates a published v1 input.")
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    destination.write_text(content, encoding="utf-8")
    with (directory / "blind_review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "question", "answer", "exclude_event"])
        writer.writeheader()
        writer.writerows({k: row[k] for k in writer.fieldnames} for row in rows)
    card = {"created_at": utc_now(), "cases": len(rows), "event_clusters": len({r["event_id"] for r in rows}),
            "label_counts": {label: sum(r["label"] == label for r in rows) for label in ["supported", "contradicted", "insufficient"]},
            "origin": "assistant authored after engine freeze; NOT independent or human annotated",
            "human_annotations": 0, "sha256": digest_bytes(destination.read_bytes()),
            "policy": "No rule or label edits in response to challenge score. Human review data stored separately in runtime.",
            "withheld_evidence_cases": sum(bool(row["exclude_event"]) for row in rows)}
    (directory / "dataset_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(card, ensure_ascii=True))


if __name__ == "__main__":
    main()
