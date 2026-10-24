# FactGuard EDU

## Phiên bản nghiên cứu v2

Ứng dụng hiện có **7 trang** và ba module có thể sử dụng/đo thực tế:

- **Kiểm chứng mệnh đề:** tách một số mệnh đề, gắn quan hệ với sự kiện, đối chiếu từng ngày/tên/địa điểm, tô màu vị trí nguyên bản và ghi phần chưa xác minh. Có chốt tiền đề sai, vai trò đảo, phủ định đơn và nguồn xung đột.
- **Thẩm định dữ kiện:** tải tài liệu → lập bản nháp từ đoạn có thật → người dùng duyệt/từ chối/thu hồi, có lịch sử phiên bản và chuỗi hash cục bộ. Dữ kiện đã duyệt dùng được ngay ở trang kiểm chứng.
- **Phòng nghiên cứu:** bốn phương pháp gồm đối chứng học máy ba nhãn, ablation, chỉ số nhãn/bằng chứng/mệnh đề, coverage/risk và bootstrap theo sự kiện. Có phiếu ẩn kết quả, nhập ca mới, lưu nhãn người thật và phép đo riêng khi có hai tên đồng thuận.

Kết quả chính v2 nằm ở [reports/research_v2/bao_cao_nghien_cuu.md](reports/research_v2/bao_cao_nghien_cuu.md). Thiết kế và diễn giải: [reports/nghien_cuu_v2.md](reports/nghien_cuu_v2.md). Bộ 46 ca mới vẫn là tổng hợp cùng tác giả, chưa có đánh giá người dùng thật. Các số liệu v1 được giữ riêng trong reports/archive/v1 và reports/experiment, không thay bằng điểm v2.

```powershell
.\.venv\Scripts\python.exe -m src.research_evaluator
```

Mã đã đóng băng trước khi tạo challenge. `scripts/build_research_challenge.py` và lệnh `--freeze` từ chối ghi đè. Không dùng kết quả challenge để sửa quy tắc/nhãn rồi gọi đó là kiểm thử chưa biết. Phân tích độ nhạy dạng câu hỏi được công bố riêng là hậu nghiệm.

## Thu thập câu trả lời AI thật

Ngân hàng có 50 câu do trợ lý soạn; mẫu đi kèm có 100 dòng trống cho ChatGPT/Gemini, chưa phải dữ liệu đã thu. Xem [hướng dẫn thu thập](reports/huong_dan_thu_thap.md) về cách hỏi, ghi nguyên văn, dùng Excel và bảo vệ dữ liệu. Chạy tại thư mục dự án:

```powershell
.\.venv\Scripts\python.exe scripts\build_collection_kit.py --tools ChatGPT Gemini --output data\collection\dot1.csv
.\.venv\Scripts\python.exe scripts\import_collected.py data\collection\dot1.csv --dry-run
```

Sau khi điền và hết lỗi, chạy lại lệnh nhập bỏ `--dry-run`; hoặc vào **Phòng nghiên cứu → Gán nhãn độc lập → Nhập nhiều câu trả lời từ tệp CSV** để tải mẫu, xem trước và bấm nhập (tối đa 5 MB). Ca mới chưa có nhãn. Tệp đã điền trong `data/collection/` có thể vào ZIP/Git, cần kiểm tra trước khi chia sẻ.

**Kiểm chứng để hiểu đúng.** Ứng dụng tiếng Việt giúp học sinh THPT đối chiếu câu trả lời AI về Lịch sử Việt Nam với kho dữ kiện có nguồn. Chạy bằng Python/Streamlit trên CPU, không cần API key. Sau khi cài thư viện, kiểm chứng và thực nghiệm chạy offline; nút mở nguồn gốc cần Internet.

## Chạy ngay trên máy này

```powershell
cd D:\KHKT\factguard-edu
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở **http://127.0.0.1:8501**. Có thể nhấp đúp `run.bat`. Dừng bằng Ctrl+C trong cửa sổ đang chạy. Không cần kích hoạt venv, không cần đổi PowerShell ExecutionPolicy.

## Cài trên Windows khác

Cài Python 3.11 trở lên (đã kiểm thử trên Python 3.12.10 / Windows), chọn thêm Python vào PATH. Giải nén source và mở PowerShell tại thư mục chứa app.py:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Hoặc nhấp `setup.bat`, chờ cài xong rồi nhấp `run.bat`. Việc cài thư viện lần đầu cần Internet. Thư mục .venv trên máy này không được đưa vào ZIP vì không thể mang nguyên môi trường Python sang máy khác. `requirements-lock.txt` lưu các phiên bản thực sự đã dùng trên Windows/Python 3.12; dùng file này để tái lập đúng môi trường. Với Python khác, dùng requirements.txt nếu wheel khóa không tương thích.

Muốn chuẩn bị một máy Windows/Python cùng phiên bản mà không có Internet:

```powershell
# Làm trước trên máy có mạng, cùng kiến trúc và phiên bản Python
.\.venv\Scripts\python.exe -m pip download -r requirements.txt -d wheelhouse
# Chép source + wheelhouse sang máy đích, tạo .venv rồi chạy:
.\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements.txt
```

Wheelhouse chưa được đóng gói sẵn; máy hiện tại đã cài đủ thư viện.

## Những gì đã triển khai

1. **Tổng quan**: đếm dữ kiện, nguồn, câu hỏi đánh giá và lượt kiểm chứng từ SQLite; kết quả thực nghiệm có thời điểm chạy, không có số giả.
2. **Kiểm chứng câu trả lời**: nhập câu hỏi + đáp án; đối chiếu nhiều mệnh đề ngày/năm, nhân vật, địa điểm trong các mẫu quan hệ; bốn trạng thái; bằng chứng, vị trí ký tự và phần chưa xử lý; lưu lịch sử cục bộ, xuất JSON.
3. **Kho kiến thức**: tìm dữ kiện, xem/tải CSV, đọc tóm lược và URL; tải TXT/Markdown/PDF văn bản, chống trùng SHA-256, tái lập chỉ mục. PDF scan/mật khẩu/lỗi được báo rõ.
4. **So sánh phương pháp**: baseline khớp từ và đề xuất đối chiếu dữ kiện trên cùng đầu vào.
5. **Thực nghiệm**: chạy development/evaluation; Accuracy, Precision/Recall/F1 theo nhãn và macro, confusion matrix, tỷ lệ từ chối, nhóm thất bại, thời gian thật; xuất CSV/Markdown.
6. **Phương pháp nghiên cứu**: đề cương, pipeline, thuật toán, giới hạn và câu hỏi phản biện.
7. **Phòng nghiên cứu v2**: thử thách nhiều mệnh đề, đối chứng ba nhãn, ablation, phân tích nguồn lỗi và luồng thu thập/gán nhãn người dùng.

Không có mô hình sinh văn bản hay API LLM trong bản này. Đây là so sánh hai **phương pháp kiểm chứng**.

## Dữ liệu và cách hiểu kết luận

- 33 dữ kiện, 7 bài/trang nguồn chính thức; có URL thật và vị trí đọc lại. Đã mở và đối chiếu bằng công cụ web ngày 24/10/2026. Chưa được giáo viên thẩm định độc lập.
- 111 ca do trợ lý xây dựng: 24 development, 87 evaluation. 87 ca evaluation gồm 29 câu hỏi phân biệt; các biến thể cùng câu hỏi phụ thuộc nhau.
- V2 bổ sung 46 ca/10 cụm sự kiện sau đóng băng. 87 ca evaluation v1 đã được xem và chỉ dùng hồi quy khi phát triển v2; không gọi là bộ độc lập mới.
- Đáp án sai chỉ là đối chứng có chủ đích. Không phải dữ liệu đã thu từ học sinh hoặc mô hình AI.
- Tóm lược nguồn được tự biên soạn ngắn, không sao chép toàn bộ sách/bài. Đây không phải kho học liệu đầy đủ cho cả chương trình THPT.
- ‘Có bằng chứng hỗ trợ’ áp dụng cho **các mệnh đề thuộc quan hệ được nhận dạng**, không đảm bảo bộ quy tắc hiểu mọi ý trong câu. Phủ định phức tạp, lược chủ ngữ, suy luận hoặc cách diễn đạt chưa bao phủ có thể bị từ chối.
- Điểm TF-IDF để xếp hạng văn bản, không phải phần trăm độ đúng. Không có ngưỡng ‘tin cậy’ dựng sẵn.
- Tài liệu tải thêm mặc định **chưa xác minh**, cần lập dữ kiện và người dùng thẩm định trước khi dùng đối chiếu. Thực nghiệm dùng kho đi kèm, tách khỏi uploads/dữ kiện duyệt.

Xem [data/README.md](data/README.md) để bổ sung dữ kiện và [reports/gioi_han_nghien_cuu.md](reports/gioi_han_nghien_cuu.md) để biết phạm vi.

## Kiểm thử và thực nghiệm

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q --cov=src
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pyright
.\.venv\Scripts\python.exe -m src.evaluator --split development --output reports/development
.\.venv\Scripts\python.exe -m src.evaluator --split evaluation --output reports/experiment
.\.venv\Scripts\python.exe scripts/reproduce.py
```

Kết quả thực tế: `reports/experiment/latest.json`, `results.csv`, `ket_qua_thuc_nghiem.md`. Báo cáo tổng hợp: `reports/ket_qua_thuc_nghiem.md`; bằng chứng kiểm thử: `reports/kiem_thu.md`, `pytest.xml`, `coverage.json`.

Kiểm thử bổ sung cho bộ thu thập và giao diện CSV: [reports/collection/kiem_thu.md](reports/collection/kiem_thu.md). Kết quả này tách khỏi các số liệu nghiên cứu v1/v2 đã lưu.

Không điều chỉnh thuật toán/ngưỡng theo điểm evaluation. Tách theo sự kiện, đóng băng cách xử lý trong reports/protocol.json. Đáp án tham chiếu vẫn nằm trong kho: đây là kiểm chứng kho đóng, không phải khả năng khái quát sang sự kiện chưa biết. Xem điểm yếu baseline trong báo cáo; baseline không có cơ chế sinh nhãn contradicted.

## Cấu trúc

```text
factguard-edu/
  app.py                 # 7 trang Streamlit
  requirements*.txt      # dependencies và phiên bản đã cài
  setup.bat / run.bat    # cài và chạy Windows
  .streamlit/config.toml # giao diện và chỉ nghe localhost
  assets/style.css
  src/                   # core v1, claim_verifier, research_evaluator, review, annotation_study, UI
  data/                  # 33 facts, v1 cases, 23 quan hệ, challenge v2, phiếu gán nhãn, 7 nguồn
    collection/          # ngân hàng câu hỏi và mẫu trống thu câu trả lời AI thật
  tests/                 # core, PDF, dữ liệu, metrics, SQLite, AppTest
  scripts/               # tạo dữ liệu, tái lập, đóng gói
  reports/               # nghiên cứu, phản biện, demo, log và số liệu thật
  runtime/               # tự tạo: lịch sử, uploads và kết quả từ giao diện
```

`runtime/` không vào ZIP. Dữ liệu nhập không gửi ra ngoài; link nguồn được mở khi bạn chọn. Sao lưu thư mục runtime nếu cần giữ lịch sử. Nội dung lưu dạng văn bản/SQLite cục bộ, chưa có phân quyền/mã hóa; không nhập dữ liệu cá nhân nhạy cảm. Chỉ chạy localhost, không đưa lên Internet công cộng như một dịch vụ nhiều người dùng.

## Trước khi nộp

Đọc `reports/truoc_khi_nop.md`: xác minh nguồn/nhãn với giáo viên; điền tên học sinh và thông tin thật; thực hành demo trên máy dự thi; bổ sung nghiên cứu thực tế nếu muốn kết luận về hiệu quả học tập. Nhật ký đã cung cấp mẫu trống, không tạo lịch sử hoạt động học sinh chưa diễn ra.

## Xử lý lỗi thường gặp

- Không tìm thấy Python: cài Python 3.11+ rồi chạy lại setup.bat.
- Thiếu streamlit: dùng đúng `.venv\Scripts\python.exe`, chạy pip install.
- Cổng 8501 bận: thêm `--server.port 8502` rồi mở đúng cổng.
- CSV bị Excel thay ngày/mã hóa: chỉnh bằng trình soạn thảo UTF-8; khôi phục từ ZIP. `scripts/build_dataset.py` ghi lại toàn bộ dữ liệu đi kèm, nên chỉ chạy khi muốn khôi phục và đã sao lưu thay đổi.
- Kho trống/trùng ID/câu hỏi/sai nguồn: giao diện báo lỗi và không tiếp tục kết luận; kiểm tra các dòng CSV.
- PDF scan: OCR bằng công cụ bạn có quyền dùng rồi đọc lại văn bản trước khi tải.
- Không ghi được runtime: chọn thư mục có quyền ghi, hoặc đặt `$env:FACTGUARD_RUNTIME_DIR = 'D:\du-lieu-factguard'`.
