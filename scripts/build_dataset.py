"""Rebuild the small, explicitly synthetic benchmark from source-checked facts.

Source pages were opened and inspected on 2026-10-24. Evidence is our own short
paraphrase, not an archival copy or verbatim quotation of the entire source.
Do not change cases after inspecting evaluation scores; create a new version.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CHECKED = "2026-10-24"

SOURCES = [
    ("S01", "Ký ức không phai về ngày 02/9/1945 ở Sài Gòn – Gia Định", "Bảo tàng Thành phố Hồ Chí Minh",
     "https://hcmc-museum.edu.vn/luu-tru/4844", "2024-09-01",
     "Phần mở đầu ghi lễ đọc Tuyên ngôn diễn ra ngày 02/9/1945 ở Ba Đình, Hà Nội, do Hồ Chí Minh thực hiện. Bài viết cũng ghi lễ tại Sài Gòn ở quảng trường Norodom và Trần Văn Giàu phát biểu khi không tiếp sóng được."),
    ("S02", "Tổng khởi nghĩa Cách mạng tháng Tám năm 1945", "Bảo tàng Lịch sử Quốc gia",
     "https://baotanglichsuquocgia.vn/vi/Articles/3097/18473/tong-khoi-nghia-cach-mang-thang-tam-nam-1945.html", "2015-08-18",
     "Các đề mục xác định ngày giành chính quyền: Hà Nội 19/8/1945, Huế 23/8/1945, Sài Gòn 25/8/1945. Đoạn Hà Nội mô tả cuộc tập hợp tại Nhà hát lớn. Phần Huế ghi lễ thoái vị của Bảo Đại vào chiều 30/8 ở lầu Ngọ Môn. Phần Sài Gòn nêu Trần Văn Giàu là Chủ tịch Ủy ban Hành chính Lâm thời Nam Bộ. Lưu ý trang gốc có chú thích ảnh gõ nhầm ‘2945’; bộ dữ kiện dùng đề mục và phần văn xuôi 1945, không dùng chú thích sai đó."),
    ("S03", "Một quyết định mang tính lịch sử của Đại tướng Võ Nguyên Giáp", "Bảo tàng Lịch sử Quốc gia",
     "https://baotanglichsuquocgia.vn/vi/Articles/3096/15973/mot-quyet-djinh-mang-tinh-lich-su-cua-djai-tuong-vo-nguyen-giap.html", "2014-03-20",
     "Bài viết xác định Võ Nguyên Giáp giữ trách nhiệm chỉ huy chiến dịch. Đoạn cuối nêu trận mở màn vào Him Lam ngày 13/3/1954 và ngày kết thúc thắng lợi là 7/5/1954."),
    ("S04", "Kỷ niệm 84 năm thành lập Đảng Cộng sản Việt Nam – Con dấu của Đảng Cộng sản Đông Dương", "Bảo tàng Lịch sử Quốc gia",
     "https://baotanglichsu.vn/VI/Articles/3097/15722/ky-niem-84-nam-thanh-lap-djang-cong-san-viet-nam-3-2-1930-3-2-2014-con-dau-cua-djang-cong-san-djong-duong.html", "2014-01-31",
     "Tiêu đề và chú thích tranh nêu ngày thành lập Đảng Cộng sản Việt Nam là 3/2/1930. Đoạn mở đầu nêu Nguyễn Ái Quốc chủ trì hội nghị hợp nhất tại Hương Cảng. Đoạn về tháng 10/1930 ghi Trần Phú chủ trì Hội nghị Trung ương lần thứ nhất. Không dùng bài này để kết luận toàn bộ tranh luận về thời gian bắt đầu hội nghị hợp nhất."),
    ("S05", "Sắc lệnh số 76: hoãn cuộc tổng tuyển cử đến ngày 6-1-1946", "Cổng Thông tin điện tử Chính phủ",
     "https://chinhphu.vn/default.aspx?docid=511&pageid=27160", "1945-12-18",
     "Trang siêu dữ liệu ghi số 76, ban hành 18-12-1945, người ký Hồ Chí Minh. Trích yếu nêu hoãn tổng tuyển cử đến 6-1-1946. Bộ dữ kiện chỉ đối chiếu thông tin hiển thị trên trang, không tuyên bố đã đọc tệp RTF đính kèm."),
    ("S06", "Kỷ niệm 100 năm Ngày Bác Hồ ra đi tìm đường cứu nước", "Báo Điện tử Chính phủ",
     "https://baochinhphu.vn/ky-niem-100-nam-ngay-bac-ho-ra-di-tim-duong-cuu-nuoc-5-6-1911-5-6-2011-nguoi-tao-nen-buoc-ngoat-lich-su-cho-cach-mang-viet-nam-10281639.htm", "2011-06-06",
     "Phần mở đầu ghi Nguyễn Tất Thành khởi hành ngày 5/6/1911 từ bến cảng Nhà Rồng ở Sài Gòn trên tàu Đô đốc Latouche Tréville. Chỉ ba dữ kiện ngày, nơi khởi hành và nhân vật được đưa vào kho."),
    ("S07", "Hội nghị lần thứ VIII Ban Chấp hành Trung ương Đảng", "Bảo tàng Lịch sử Quốc gia",
     "https://baotanglichsu.vn/vi/Articles/3097/14317/hoi-nghi-lan-thu-viii-ban-chap-hanh-trung-uong-djang-va-quyet-djinh-tien-hanh-cong-cuoc-giai-phong-dan-toc-tu-ngay-10-djen-ngay-19-5-1941.html", "2013-05-20",
     "Đoạn mở đầu nêu Nguyễn Ái Quốc trở về Cao Bằng ngày 28/1/1941 và chủ trì Hội nghị Trung ương VIII tại Pắc Bó tháng 5/1941. Chú thích ảnh dùng cách viết Pác Bó. Phần kiện toàn lãnh đạo nêu Trường Chinh làm Tổng Bí thư."),
]


def fact(fid, event, topic, question, answer, kind, canonical, aliases, anchors, reference, source, location):
    return dict(id=fid, event_id=event, topic=topic, question=question, answer=answer, kind=kind,
                canonical=canonical, aliases=json.dumps(aliases, ensure_ascii=False),
                anchors=json.dumps(anchors, ensure_ascii=False), reference=reference,
                source_id=source, location=location, verified="true")


def build_facts():
    rows = []

    def add(event, question, answer, kind, canonical, aliases, anchors, reference, source, location):
        rows.append(fact(f"F{len(rows) + 1:03}", event, "Lịch sử Việt Nam 1911–1954", question, answer,
                         kind, canonical, aliases, anchors, reference, source, location))

    ind = [["tuyên ngôn độc lập"], ["đọc", "tuyên đọc"]]
    ref = "Tuyên ngôn Độc lập được Hồ Chí Minh đọc ở Quảng trường Ba Đình, Hà Nội, ngày 2/9/1945."
    add("independence1945", "Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?", "2/9/1945", "date", "1945-09-02", ["2/9/1945", "Ngày 2 tháng 9 năm 1945"], ind, ref, "S01", "Đoạn mở đầu, câu thứ nhất")
    add("independence1945", "Ai đọc Tuyên ngôn Độc lập tại Quảng trường Ba Đình năm 1945?", "Hồ Chí Minh", "person", "Hồ Chí Minh", ["Hồ Chí Minh", "Chủ tịch Hồ Chí Minh"], ind, ref, "S01", "Đoạn mở đầu, câu thứ nhất")
    add("independence1945", "Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập ở đâu?", "Quảng trường Ba Đình, Hà Nội", "place", "Ba Đình", ["Quảng trường Ba Đình, Hà Nội", "Quảng trường Ba Đình", "Ba Đình"], ind, ref, "S01", "Đoạn mở đầu, câu thứ nhất")
    ceremony = [["lễ độc lập"], ["sài gòn"]]
    add("saigonindependence1945", "Ai phát biểu tại Lễ Độc lập ở Sài Gòn khi không tiếp sóng được ngày 2/9/1945?", "Trần Văn Giàu", "person", "Trần Văn Giàu", ["Trần Văn Giàu"], ceremony, "Khi không tiếp sóng được, Ban Tổ chức mời Trần Văn Giàu phát biểu tại lễ ở Sài Gòn.", "S01", "Đoạn bắt đầu ‘Theo dự kiến’")
    add("saigonindependence1945", "Lễ Độc lập ngày 2/9/1945 ở Sài Gòn tổ chức ở đâu?", "Quảng trường Norodom", "place", "Norodom", ["Quảng trường Norodom", "Norodom"], ceremony, "Tại Sài Gòn, lễ ngày 2/9 được tổ chức ở quảng trường Norodom.", "S01", "Đoạn mở đầu, câu thứ hai")
    add("saigonindependence1945", "Lễ Độc lập tại Sài Gòn được tổ chức vào ngày nào?", "2/9/1945", "date", "1945-09-02", ["2/9/1945", "Ngày 2 tháng 9 năm 1945"], ceremony, "Bài viết mô tả Lễ Độc lập ngày 02/9/1945 tại Sài Gòn.", "S01", "Tiêu đề và đoạn mở đầu")
    add("hanoi1945", "Khởi nghĩa giành chính quyền ở Hà Nội năm 1945 thắng lợi vào ngày nào?", "19/8/1945", "date", "1945-08-19", ["19/8/1945", "Ngày 19 tháng 8 năm 1945"], [["giành chính quyền"], ["hà nội"]], "Đề mục Hà Nội và đoạn kết mục này xác định thắng lợi giành chính quyền ngày 19/8/1945.", "S02", "Mục ‘Giành chính quyền tại Hà Nội 19/8/1945’")
    add("hanoi1945", "Cuộc mít tinh tại Hà Nội ngày 19/8/1945 tập hợp trước địa điểm nào?", "Nhà hát lớn Hà Nội", "place", "Nhà hát lớn", ["Nhà hát lớn Hà Nội", "Nhà hát lớn"], [["mít tinh"], ["hà nội"], ["19/8/1945", "19 tháng 8"]], "Sáng 19/8, quần chúng tập hợp trước Nhà hát lớn Hà Nội.", "S02", "Mục Hà Nội, đoạn ‘Hàng vạn quần chúng’")
    add("hue1945", "Khởi nghĩa giành chính quyền ở Huế năm 1945 thắng lợi vào ngày nào?", "23/8/1945", "date", "1945-08-23", ["23/8/1945", "Ngày 23 tháng 8 năm 1945"], [["giành chính quyền"], ["huế"]], "Đề mục Huế ghi ngày giành chính quyền là 23/8/1945.", "S02", "Mục ‘Giành chính quyền tại Huế 23/8/1945’")
    add("saigon1945", "Khởi nghĩa giành chính quyền ở Sài Gòn năm 1945 thắng lợi vào ngày nào?", "25/8/1945", "date", "1945-08-25", ["25/8/1945", "Ngày 25 tháng 8 năm 1945"], [["giành chính quyền"], ["sài gòn"]], "Đề mục Sài Gòn và phần mô tả sáng 25/8 xác định thắng lợi ngày 25/8/1945.", "S02", "Mục ‘Giành chính quyền tại Sài Gòn, 25/8/1945’")
    abd = [["thoái vị"], ["bảo đại", "vua cuối cùng"]]
    add("abdication1945", "Lễ thoái vị của vua Bảo Đại diễn ra vào ngày nào?", "30/8/1945", "date", "1945-08-30", ["30/8/1945", "Ngày 30 tháng 8 năm 1945"], abd, "Phần Huế mô tả lễ thoái vị của Bảo Đại chiều 30/8/1945.", "S02", "Mục Huế, đoạn ‘Chiều 30/8’")
    add("abdication1945", "Vị vua cuối cùng thoái vị tại Huế năm 1945 là ai?", "Bảo Đại", "person", "Bảo Đại", ["Bảo Đại", "Vua Bảo Đại"], [["vua cuối cùng"], ["thoái vị"]], "Bảo Đại là nhân vật thực hiện lễ thoái vị được mô tả trong phần Huế.", "S02", "Mục Huế, đoạn về lễ thoái vị")
    add("abdication1945", "Lễ thoái vị của Bảo Đại được tổ chức ở đâu?", "Lầu Ngọ Môn, Huế", "place", "Ngọ Môn", ["Lầu Ngọ Môn, Huế", "Lầu Ngọ Môn", "Ngọ Môn"], abd, "Lễ thoái vị được tổ chức ở lầu Ngọ Môn thuộc kinh thành Huế.", "S02", "Mục Huế, đoạn ‘Chiều 30/8’")
    add("saigon1945", "Ai là Chủ tịch Ủy ban Hành chính Lâm thời Nam Bộ ra mắt ngày 25/8/1945?", "Trần Văn Giàu", "person", "Trần Văn Giàu", ["Trần Văn Giàu"], [["chủ tịch"], ["ủy ban hành chính lâm thời nam bộ"]], "Ủy ban Hành chính Lâm thời Nam Bộ ra mắt với Trần Văn Giàu làm Chủ tịch.", "S02", "Mục Sài Gòn, đoạn ‘Sáng 25/8’")
    dbp = [["điện biên phủ"]]
    add("dbp1954", "Chiến dịch Điện Biên Phủ bắt đầu vào ngày nào?", "13/3/1954", "date", "1954-03-13", ["13/3/1954", "Ngày 13 tháng 3 năm 1954"], dbp + [["bắt đầu", "mở màn"]], "Chiến dịch mở màn bằng đòn tiến công Him Lam ngày 13/3/1954.", "S03", "Đoạn cuối trước ảnh bộ đội vượt cầu")
    add("dbp1954", "Chiến dịch Điện Biên Phủ kết thúc vào ngày nào?", "7/5/1954", "date", "1954-05-07", ["7/5/1954", "Ngày 7 tháng 5 năm 1954"], dbp + [["kết thúc", "toàn thắng"]], "Chiến dịch Điện Biên Phủ kết thúc thắng lợi ngày 7/5/1954.", "S03", "Đoạn cuối trước ảnh bộ đội vượt cầu")
    add("dbp1954", "Ai chỉ huy chiến dịch Điện Biên Phủ?", "Võ Nguyên Giáp", "person", "Võ Nguyên Giáp", ["Võ Nguyên Giáp", "Đại tướng Võ Nguyên Giáp"], dbp + [["chỉ huy"]], "Bài viết nêu Đại tướng Võ Nguyên Giáp giữ trọng trách chỉ huy chiến dịch.", "S03", "Đoạn ‘Là người giữ trọng trách chỉ huy’")
    add("dbp1954", "Trận mở màn chiến dịch Điện Biên Phủ tiến công địa điểm nào?", "Him Lam", "place", "Him Lam", ["Him Lam", "Cứ điểm Him Lam"], dbp + [["mở màn"], ["tiến công"]], "Pháo binh tiến công trung tâm đề kháng Him Lam để mở màn chiến dịch.", "S03", "Đoạn cuối trước ảnh bộ đội vượt cầu")
    party = [["đảng cộng sản việt nam"], ["thành lập", "hợp nhất"]]
    add("party1930", "Đảng Cộng sản Việt Nam thành lập vào ngày nào?", "3/2/1930", "date", "1930-02-03", ["3/2/1930", "Ngày 3 tháng 2 năm 1930"], party, "Tiêu đề bài và chú thích tranh xác định ngày thành lập Đảng là 3/2/1930.", "S04", "Tiêu đề và chú thích tranh hội nghị")
    add("party1930", "Ai chủ trì hội nghị hợp nhất thành lập Đảng Cộng sản Việt Nam?", "Nguyễn Ái Quốc", "person", "Nguyễn Ái Quốc", ["Nguyễn Ái Quốc", "Hồ Chí Minh"], party + [["chủ trì"]], "Hội nghị hợp nhất tại Hương Cảng do Nguyễn Ái Quốc chủ trì.", "S04", "Đoạn mở đầu")
    add("party1930", "Hội nghị hợp nhất thành lập Đảng Cộng sản Việt Nam diễn ra ở đâu?", "Hương Cảng", "place", "Hương Cảng", ["Hương Cảng", "Hồng Kông", "Hong Kong"], party, "Địa điểm hội nghị hợp nhất được bài viết ghi là Hương Cảng.", "S04", "Đoạn mở đầu")
    add("party1930", "Ai chủ trì Hội nghị Trung ương lần thứ nhất tháng 10/1930?", "Trần Phú", "person", "Trần Phú", ["Trần Phú"], [["hội nghị trung ương"], ["lần thứ nhất"], ["1930"]], "Bài viết nêu Hội nghị Trung ương lần thứ nhất tháng 10/1930 do Trần Phú chủ trì.", "S04", "Đoạn bắt đầu ‘Trong tình hình ấy’")
    decree = [["sắc lệnh"], ["76"]]
    add("decree1945", "Sắc lệnh số 76 hoãn tổng tuyển cử được ban hành vào ngày nào?", "18/12/1945", "date", "1945-12-18", ["18/12/1945", "Ngày 18 tháng 12 năm 1945"], decree + [["ban hành"]], "Siêu dữ liệu Sắc lệnh 76 ghi ngày ban hành 18-12-1945.", "S05", "Trường ‘Ngày ban hành’")
    add("decree1945", "Ai ký Sắc lệnh số 76 hoãn tổng tuyển cử?", "Hồ Chí Minh", "person", "Hồ Chí Minh", ["Hồ Chí Minh", "Chủ tịch Hồ Chí Minh"], decree + [["ký"]], "Trường người ký của Sắc lệnh 76 ghi Hồ Chí Minh.", "S05", "Trường ‘Người ký’")
    add("decree1945", "Sắc lệnh số 76 hoãn tổng tuyển cử đến ngày nào?", "6/1/1946", "date", "1946-01-06", ["6/1/1946", "Ngày 6 tháng 1 năm 1946"], decree + [["đến"]], "Trích yếu của Sắc lệnh 76 ghi hoãn tổng tuyển cử đến 6-1-1946.", "S05", "Tiêu đề và trường ‘Trích yếu’")
    dep = [["ra đi tìm đường cứu nước", "khởi hành tìm đường cứu nước"]]
    add("departure1911", "Nguyễn Tất Thành ra đi tìm đường cứu nước vào ngày nào?", "5/6/1911", "date", "1911-06-05", ["5/6/1911", "Ngày 5 tháng 6 năm 1911"], dep, "Nguyễn Tất Thành khởi hành ngày 5/6/1911 tại bến cảng Nhà Rồng.", "S06", "Đoạn ‘Ngày 5 tháng 6 năm 1911’")
    add("departure1911", "Nguyễn Tất Thành ra đi tìm đường cứu nước từ địa điểm nào?", "Bến Nhà Rồng", "place", "Nhà Rồng", ["Bến Nhà Rồng", "Bến cảng Nhà Rồng", "Nhà Rồng"], dep, "Điểm khởi hành là bến cảng Nhà Rồng ở Sài Gòn.", "S06", "Đoạn ‘Ngày 5 tháng 6 năm 1911’")
    add("departure1911", "Ai ra đi tìm đường cứu nước từ bến Nhà Rồng năm 1911?", "Nguyễn Tất Thành", "person", "Nguyễn Tất Thành", ["Nguyễn Tất Thành", "Hồ Chí Minh"], dep, "Người khởi hành năm 1911 được bài viết gọi là Nguyễn Tất Thành.", "S06", "Đoạn ‘Ngày 5 tháng 6 năm 1911’")
    ret = [["nguyễn ái quốc"], ["trở về", "về nước"]]
    add("return1941", "Nguyễn Ái Quốc trở về nước năm 1941 vào ngày nào?", "28/1/1941", "date", "1941-01-28", ["28/1/1941", "Ngày 28 tháng 1 năm 1941"], ret, "Bài viết ghi Nguyễn Ái Quốc trở về Cao Bằng ngày 28/1/1941.", "S07", "Đoạn thứ hai")
    add("return1941", "Nguyễn Ái Quốc trở về tỉnh nào ngày 28/1/1941?", "Cao Bằng", "place", "Cao Bằng", ["Cao Bằng", "Tỉnh Cao Bằng"], ret, "Điểm trở về ngày 28/1/1941 được ghi là Cao Bằng.", "S07", "Đoạn thứ hai")
    conf = [["hội nghị trung ương viii", "hội nghị trung ương lần thứ viii", "hội nghị trung ương lần thứ 8"]]
    add("conference1941", "Hội nghị Trung ương VIII tháng 5/1941 diễn ra ở đâu?", "Pác Bó, Cao Bằng", "place", "Pác Bó", ["Pác Bó, Cao Bằng", "Pác Bó", "Pắc Bó"], conf, "Hội nghị tháng 5/1941 diễn ra tại Pắc Bó (Hà Quảng, Cao Bằng); chú thích ảnh viết Pác Bó.", "S07", "Đoạn thứ hai và chú thích ảnh lán Khuổi Nậm")
    add("conference1941", "Ai chủ trì Hội nghị Trung ương VIII tháng 5/1941?", "Nguyễn Ái Quốc", "person", "Nguyễn Ái Quốc", ["Nguyễn Ái Quốc", "Hồ Chí Minh"], conf + [["chủ trì"]], "Nguyễn Ái Quốc triệu tập và chủ trì Hội nghị Trung ương VIII.", "S07", "Đoạn thứ hai")
    add("conference1941", "Ai được cử làm Tổng Bí thư tại Hội nghị Trung ương VIII năm 1941?", "Trường Chinh", "person", "Trường Chinh", ["Trường Chinh"], conf + [["tổng bí thư"]], "Phần kiện toàn lãnh đạo nêu Trường Chinh làm Tổng Bí thư.", "S07", "Đoạn ‘Dưới sự chủ trì của lãnh tụ’")
    return rows


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    DATA.mkdir(exist_ok=True)
    (DATA / "sources").mkdir(exist_ok=True)
    sources = []
    for sid, title, publisher, url, published, summary in SOURCES:
        filename = f"{sid}.md"
        sources.append(dict(id=sid, title=title, publisher=publisher, url=url, published_at=published,
                            checked_at=CHECKED, verified=True, file=filename,
                            verification_method="Mở trang gốc và đối chiếu nội dung bằng công cụ web; chưa có thẩm định độc lập của giáo viên"))
        (DATA / "sources" / filename).write_text(
            f"# {title}\n\nCơ quan: {publisher}.\nNgày đăng/ban hành: {published}.\n"
            f"URL: {url}\n\nĐối chiếu ngày {CHECKED}.\n\n## Tóm lược tự biên soạn\n\n{summary}\n\n"
            "Đây là bản tóm lược ngắn để truy xuất offline, không phải bản lưu toàn văn hoặc trích dẫn nguyên văn. "
            "Đọc nguồn gốc để kiểm tra ngữ cảnh; vị trí cụ thể của từng dữ kiện nằm trong facts.csv.\n", encoding="utf-8")
    (DATA / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
    facts = build_facts()
    write_csv(DATA / "facts.csv", facts)
    development = {"departure1911", "return1941", "conference1941"}
    rows = []

    def case(f, answer, label, group, question=None):
        rows.append(dict(id=f"E{len(rows) + 1:03}", fact_id=f["id"], event_id=f["event_id"],
                         question=question or f["question"], answer=answer, label=label, group=group,
                         split="development" if f["event_id"] in development else "evaluation",
                         origin="Câu trả lời kiểm thử xây dựng có chủ đích; không phải dữ liệu thu thập từ người dùng/LLM"))

    for f in facts:
        kind = f["kind"]
        aliases = json.loads(f["aliases"])
        answer = aliases[-1] if kind == "date" else f["answer"]
        case(f, answer, "supported", "Đúng ngày tháng năm" if kind == "date" else "Đúng nhân vật hoặc địa danh")
        if kind == "date":
            year, month, day = f["canonical"].split("-")
            case(f, f"Ngày {int(day)}/{int(month)}/{int(year) + 1}.", "contradicted", "Sai mốc thời gian")
            case(f, f"Vào năm {year}.", "insufficient", "Câu trả lời không đủ thông tin")
        else:
            replacement = next(other["answer"] for other in facts if other["kind"] == kind
                               and not any(a.casefold() in other["answer"].casefold() for a in aliases)
                               and not any(a.casefold() in f["answer"].casefold() for a in json.loads(other["aliases"])))
            case(f, replacement, "contradicted", "Nhầm nhân vật hoặc địa danh")
            case(f, "Tôi chưa rõ.", "insufficient", "Câu trả lời không đủ thông tin")
    # Stress cases are part of the published benchmark, not used to tune rules.
    for idx in [0, 1, 14, 15]:
        f = facts[idx]
        case(f, f"{f['answer']}. Ngoài ra, người ngoài hành tinh đã giúp tạo ra sự kiện này.",
             "insufficient", "Nội dung nằm ngoài tài liệu")
    f = facts[0]
    case(f, "Không phải ngày 2/9/1945.", "contradicted", "Phủ định cần người đọc")
    case(f, "Ngày 3/9/1945, chứ không phải ngày 2/9/1945.", "contradicted", "Phủ định cần người đọc")
    case(f, "2-9-1945", "supported", "Biến thể cách viết")
    case(f, "2.9.1945", "supported", "Biến thể cách viết")
    for question, answer in [
        ("Trận Bạch Đằng năm 938 diễn ra vào ngày nào?", "Ngày 1/1/938."),
        ("Ai phát minh máy in hiện đại?", "Johannes Gutenberg."),
        ("Hiệp định Paris năm 1973 được ký vào ngày nào?", "Ngày 27/1/1973."),
        ("Cách mạng công nghiệp Anh bắt đầu vào năm nào?", "Năm 1760."),
    ]:
        case({"id": "OUTSIDE", "event_id": "outside", "question": question}, answer, "insufficient", "Nội dung nằm ngoài tài liệu")
    write_csv(DATA / "evaluation.csv", rows)
    (DATA / "dataset_card.json").write_text(json.dumps({
        "version": "1.0", "created_at": CHECKED, "facts": len(facts), "sources": len(sources),
        "cases": len(rows), "evaluation_cases": sum(r["split"] == "evaluation" for r in rows),
        "development_cases": sum(r["split"] == "development" for r in rows),
        "origin": "Dữ kiện đối chiếu nguồn công khai; câu trả lời và nhãn kiểm thử do trợ lý xây dựng có chủ đích.",
        "human_review": "Chưa được giáo viên/người gán nhãn độc lập rà soát.",
        "unverified_seed_facts": [], "split_unit": "event_id",
        "limits": "Nguồn nhỏ; kiểm thử tổng hợp; các biến thể cùng câu hỏi phụ thuộc nhau; không coi mỗi ca là một quan sát học sinh độc lập.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created {len(facts)} facts, {len(sources)} sources, {len(rows)} labelled cases.")


if __name__ == "__main__":
    main()
