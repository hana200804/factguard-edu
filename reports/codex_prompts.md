# Prompt giao cho Codex — bộ thu thập câu trả lời AI

Chạy từng prompt riêng, theo thứ tự, trong thư mục `D:\KHKT\factguard-edu`. Sau mỗi prompt, kiểm tra diff trước khi chạy prompt tiếp theo.

---

## Prompt 1 — Viết test cho module nhập dữ liệu

```text
Dự án Python/Streamlit tại D:\KHKT\factguard-edu. Python: .venv\Scripts\python.exe.

Nhiệm vụ: tạo tests/test_collection.py kiểm thử src/collection.py (đọc kỹ file này trước). Theo đúng phong cách tests/test_annotation_study.py: hàm test ngắn, dùng fixture có sẵn trong tests/conftest.py (corpus, facts, cases), dùng tmp_path cho mọi tệp và ReviewRepository(tmp_path). Không bao giờ ghi vào thư mục runtime/ thật.

Cần phủ các trường hợp:
1. load_question_bank đọc data/collection/cau_hoi.csv thật: 50 câu, mọi ma_su_kien thuộc eligible_events(facts, development), không câu nào thuộc departure1911/return1941/conference1941.
2. load_question_bank báo DataError khi: mã trùng, mã sai dạng, sự kiện thuộc development, loai không hợp lệ, thiếu cột.
3. read_table: đọc được CSV phân tách bằng ',' và ';' (Excel tiếng Việt), có BOM, ô có xuống dòng trong ngoặc kép; báo DataError khi tệp mã hóa cp1258/cp1252 (không phải UTF-8).
4. parse_answers (truyền today=date(2026, 10, 24) để test ổn định):
   - dòng không có cau_tra_loi được đếm vào blank, không phải lỗi;
   - ngay_lay nhận "2026-10-24", "24/10/2026", "24-10-2026"; từ chối ngày tương lai, trước 2022-11-30, dạng sai;
   - từ chối: mã câu hỏi lạ, câu hỏi bị sửa khác ngân hàng (nhưng chấp nhận khác biệt chỉ ở khoảng trắng), ma_su_kien khác ngân hàng, thiếu cong_cu/phien_ban/nguoi_thu_thap, kieu_lenh sai, câu trả lời > 12000 ký tự, câu trả lời bị Excel hỏng ("45000", "1945-09-02", "#NAME?"), hai dòng trùng nguyên văn;
   - câu trả lời hợp lệ như "Ngày 2/9/1945." KHÔNG bị coi là Excel hỏng;
   - origin chứa công cụ, phiên bản, ngày ISO, kiểu lệnh, mã câu hỏi, loại câu và ghi chú khi có.
5. import_cases: nhập 2 ca → collected_cases() có 2 ca đúng question/answer/event_id/submitter; chạy lại lần 2 trả status "đã có, bỏ qua" và không tạo ca mới; ca nhập vào chưa có nhãn nào (annotations() rỗng); repository.verify_audit() vẫn True.
6. write_template: ghi được tệp mới với đúng TEMPLATE_COLUMNS và 50×len(tools) dòng; từ chối ghi đè (DataError) khi tệp đích đã có ít nhất một cau_tra_loi; cho phép ghi đè tệp mẫu còn trống.
7. Test hai script bằng subprocess với env FACTGUARD_RUNTIME_DIR=tmp_path: scripts/import_collected.py --dry-run trên tệp hợp lệ trả exit 0 và không tạo research.sqlite3; trên tệp có lỗi trả exit khác 0 và không nhập gì. Đặt PYTHONIOENCODING=utf-8 trong env.

Ràng buộc:
- KHÔNG sửa src/collection.py hay bất kỳ tệp nào trong reports/research_v2/engine_freeze.json (claim_spans, claim_verifier, research_*, verifier, retriever, models, loader, utils, data/*.csv, data/relations.json...). Nếu thấy lỗi thật trong src/collection.py, dừng lại và mô tả lỗi, đừng tự sửa.
- Không tạo dữ liệu giả trong data/. Dữ liệu test chỉ nằm trong tmp_path, ghi rõ là dữ liệu kiểm thử.
- Kết thúc phải đạt cả ba lệnh:
  .venv\Scripts\python.exe -m pytest -q
  .venv\Scripts\python.exe -m ruff check .
  .venv\Scripts\python.exe -m pyright
  và .venv\Scripts\python.exe -c "from src.research_evaluator import validate_freeze; print(validate_freeze())" in ra True.
```

---

## Prompt 2 — Hướng dẫn thu thập + cập nhật README

```text
Dự án tại D:\KHKT\factguard-edu. Đọc trước: src/collection.py, scripts/build_collection_kit.py, scripts/import_collected.py, data/collection/cau_hoi.csv, reports/huong_dan_gan_nhan.md, README.md.

Nhiệm vụ: chỉ viết tài liệu tiếng Việt, không sửa mã.

1. Tạo reports/huong_dan_thu_thap.md, giọng văn và mức thận trọng giống reports/huong_dan_gan_nhan.md. Gồm:
   - Mục đích: thu câu trả lời THẬT từ chatbot cho bộ 50 câu, để hai người gán nhãn độc lập trong Phòng nghiên cứu.
   - Ghi rõ: 50 câu hỏi do trợ lý soạn (cột nguon_cau_hoi = tro_ly); giáo viên/học sinh nên thêm câu của mình (mã Q51 trở đi, nguon_cau_hoi = tên người đặt), sau đó chạy lại build_collection_kit.py với --output tên tệp mới.
   - Ý nghĩa cột loai: don, ket_hop, tien_de_sai, kiem_tra, mo, ngoai_kho, thieu_du_kien (thieu_du_kien = sự kiện có trong kho nhưng kho không có dữ kiện được hỏi). Nói rõ loại câu hỏi KHÔNG phải nhãn, người gán nhãn phải tự đọc nguồn.
   - Quy trình hỏi chatbot: mỗi câu mở một cuộc trò chuyện MỚI; tắt custom instructions/memory nếu có; không bật tìm kiếm web trừ khi ghi vào ghi_chu; kieu_lenh ngan_gon = gửi câu hỏi kèm "Trả lời ngắn gọn trong 1–2 câu.", tu_do = chỉ gửi câu hỏi; giữ một kiểu lệnh cố định cho cả lượt thu; chỉ lấy câu trả lời ĐẦU TIÊN, không bấm tạo lại để chọn câu đẹp; dán nguyên văn kể cả khi chatbot từ chối hoặc trả lời sai; ghi phiên bản mô hình hiển thị trong giao diện (hoặc "không rõ") và ngày lấy dạng YYYY-MM-DD.
   - Mẹo Excel: lưu bằng "CSV UTF-8 (Comma delimited)"; định dạng cột ngay_lay và cau_tra_loi là Text trước khi dán; câu trả lời bắt đầu bằng - = + thì gõ dấu ' ở đầu ô; khuyến nghị dùng Google Sheets hoặc LibreOffice nếu Excel đổi dữ liệu. Script tự phát hiện tệp không UTF-8, dấu ';' và ô bị Excel đổi thành số/ngày.
   - Người thu thập nên khác người gán nhãn; không xem đầu ra FactGuard trước khi gán nhãn.
   - Các lệnh (khối powershell):
     .\.venv\Scripts\python.exe scripts\build_collection_kit.py --tools ChatGPT Gemini Copilot --output data\collection\dot1.csv
     .\.venv\Scripts\python.exe scripts\import_collected.py data\collection\dot1.csv --dry-run
     .\.venv\Scripts\python.exe scripts\import_collected.py data\collection\dot1.csv
     Giải thích: kiểm tra toàn bộ trước, có lỗi thì không nhập dòng nào; nhập lại cùng tệp không tạo trùng; nhật ký ở runtime\collection_imports\.
   - Sau khi nhập: App → Phòng nghiên cứu → Gán nhãn độc lập; cần ≥2 tên gán cùng nhãn mới vào phép đo; kappa chỉ tính từ nhãn thật.
   - Quyền riêng tư: không đưa thông tin cá nhân vào câu hỏi/ghi chú; tệp đã điền chứa dữ liệu thật nên cân nhắc trước khi đưa vào ZIP (scripts/package_project.py hiện CÓ đóng gói data/collection/).
   - Giới hạn: một lượt thu tại một thời điểm không đại diện cho mọi phiên bản chatbot; câu trả lời chatbot thay đổi theo thời gian.

2. README.md: thêm một mục ngắn "Thu thập câu trả lời AI thật" (5–8 dòng) ngay sau mục "Phiên bản nghiên cứu v2", trỏ tới reports/huong_dan_thu_thap.md, kèm 2 lệnh build và import. Trong mục "Cấu trúc" thêm dòng data/collection/. Không đổi số liệu nào khác trong README.

3. data/README.md: thêm 2–3 dòng mô tả data/collection/cau_hoi.csv và mau_ghi_cau_tra_loi.csv.

Ràng buộc: không bịa số liệu, không viết như thể đã thu thập được dữ liệu. Không sửa tệp .py nào. Kiểm tra mọi đường dẫn/tên cột/lệnh bạn ghi khớp với mã thật.
```

---

## Prompt 3 (tùy chọn) — Nút tải CSV ngay trong giao diện

```text
Dự án tại D:\KHKT\factguard-edu. Đọc trước: src/research_ui.py (hàm independent_review), src/collection.py, scripts/import_collected.py.

Nhiệm vụ: trong independent_review, ngay dưới expander "Thu thập câu trả lời mới từ người dùng", thêm expander "Nhập nhiều câu trả lời từ tệp CSV" để làm đúng việc của scripts/import_collected.py qua giao diện:
- st.download_button tải data/collection/mau_ghi_cau_tra_loi.csv.
- st.file_uploader nhận .csv (giới hạn 5 MB). Ghi tạm vào runtime/collection_imports/upload_<timestamp>.csv rồi gọi read_table → parse_answers (bank = load_question_bank(QUESTION_BANK, eligible_events(facts, development))).
- Có lỗi: st.error liệt kê từng dòng lỗi, không nhập gì. Không lỗi: hiện số dòng hợp lệ/chưa điền và nút "Nhập vào hàng đợi gán nhãn"; bấm mới gọi import_cases(repository, cases) và ghi nhật ký CSV giống script.
- KHÔNG hiển thị cột origin/công cụ trong danh sách xem trước cho người gán nhãn (giữ ẩn nguồn).
- Mọi DataError bắt và hiện st.error tiếng Việt.

Thêm test AppTest trong tests/test_research_app.py theo mẫu có sẵn (dùng FACTGUARD_RUNTIME_DIR=tmp_path) cho trường hợp tệp hợp lệ và tệp lỗi; nếu AppTest không hỗ trợ file_uploader, test riêng một hàm thuần tách ra từ phần xử lý.

Ràng buộc: không sửa src/collection.py và các tệp trong reports/research_v2/engine_freeze.json. Phải đạt pytest -q, ruff check ., pyright, và validate_freeze() == True.
```

---

## Prompt 4 — Chặn tệp đã điền khỏi Git và ZIP

```text
Dự án tại D:\KHKT\factguard-edu (git, nhánh main). Python: .venv\Scripts\python.exe.

Mục tiêu: tệp CSV chứa câu trả lời thật (ví dụ data\collection\dot1.csv) không được lọt vào Git hay ZIP. Chỉ hai tệp sau được theo dõi và đóng gói trong data/collection/: cau_hoi.csv và mau_ghi_cau_tra_loi.csv.

1. .gitignore: thêm
     data/collection/*
     !data/collection/cau_hoi.csv
     !data/collection/mau_ghi_cau_tra_loi.csv
   Kiểm tra bằng: git check-ignore -v data/collection/dot1.csv (phải bị bỏ qua) và git ls-files data/collection (vẫn đúng 2 tệp).

2. scripts/package_project.py: trong vòng lặp os.walk, bỏ mọi tệp nằm trong data/collection/ trừ hai tệp trên. Dùng một hằng số kiểu COLLECTION_KEEP = {"cau_hoi.csv", "mau_ghi_cau_tra_loi.csv"}, viết gọn theo phong cách của tệp. Không đổi hành vi nào khác.

3. Thêm test (tests/test_package_project.py hoặc tệp test phù hợp): tạo tệp tạm data/collection/dot_test_tmp.csv, chạy hàm/luồng đóng gói ra một ZIP trong tmp_path, khẳng định ZIP có cau_hoi.csv + mau_ghi_cau_tra_loi.csv nhưng không có dot_test_tmp.csv; luôn xóa tệp tạm trong finally. Nếu cần, tách phần chọn tệp của package_project.py thành một hàm thuần (vd. collect_paths(root)) để test được mà không ghi ZIP ra D:\KHKT; main() vẫn chạy y như cũ.

4. Tài liệu: sửa cho khớp với quy tắc mới, không đổi số liệu khác.
   - reports/huong_dan_thu_thap.md: giữ ví dụ data\collection\dot1.csv / dot2.csv, nhưng thay đoạn cảnh báo ở mục "Quyền riêng tư" (đang nói package_project.py CÓ đóng gói data/collection/ và tệp đã điền có thể lên Git) bằng: tệp khác hai tệp gốc trong data/collection/ bị .gitignore bỏ qua và không vào ZIP; vẫn nên giữ bản sao lưu riêng, và nếu cố ý công bố dữ liệu thì phải tự sao ra chỗ khác sau khi xóa thông tin cá nhân. Lưu ý git add -f vẫn vượt được .gitignore.
   - README.md dòng 28: thay câu "Tệp đã điền trong data/collection/ có thể vào ZIP/Git, cần kiểm tra trước khi chia sẻ." bằng câu tương ứng với quy tắc mới.
   - Rà lại data/README.md xem có câu nào mâu thuẫn không.

Ràng buộc:
- Không sửa src/collection.py, src/collection_ui.py hay tệp nào trong reports/research_v2/engine_freeze.json.
- Không chạy package_project.py thật nếu nó ghi đè ZIP ở D:\KHKT; chỉ test vào tmp_path.
- Kết thúc phải đạt: pytest -q, ruff check ., pyright, và validate_freeze() == True.
- Commit một commit rõ ràng; chưa push cho tới khi mình xem diff.
```

---

## Prompt 5 — Test, đóng băng và tài liệu cho v3 (nhánh v3-nli)

```text
Dự án tại D:\KHKT\factguard-edu, nhánh git v3-nli (đừng chuyển sang main). Python: .venv\Scripts\python.exe.
Đọc kỹ trước: src/nli.py, src/hybrid_verifier.py, scripts/evaluate_v3.py, scripts/fetch_model.py, reports/research_v3/protocol.json, src/annotation_study.py, src/research_evaluator.py (hàm freeze_engine/validate_freeze để làm theo cùng kiểu).
Mô hình đã có sẵn ở models/mdeberta-xnli/ (bị .gitignore). KHÔNG tải lại, KHÔNG thêm tệp mô hình vào git.

Bối cảnh: v3 = luật v2 (không đổi) + NLI offline chỉ cho đoạn luật chưa đọc được, có chốt giá trị. Ngưỡng ENTAIL_MIN=0.80, CONTRADICT_MIN=0.90 đã ghi trước khi đo. KHÔNG đổi ngưỡng, KHÔNG đổi logic trong src/hybrid_verifier.py hay src/nli.py. Thấy lỗi thật thì dừng và mô tả, đừng tự sửa.

1. tests/test_hybrid_verifier.py (theo phong cách tests/test_claim_verifier.py, dùng fixture trong conftest):
   - Dùng pytest.mark.skipif khi model_status() có tệp chưa đúng, để CI không có mô hình vẫn chạy.
   - Bắt buộc có test KHÔNG cần mô hình: dùng một FakeNli (có hàm score trả NliScore cố định) truyền vào HybridVerifier, để kiểm tra:
     a) v2 trả supported/contradicted thì v3 giữ nguyên, không gọi NLI;
     b) có issue ngoài RESOLVABLE (vd. question_premise, open_question) thì giữ nhãn v2;
     c) entailment 0.95 nhưng đoạn chứa tên ngoài bằng chứng ("Đại tướng Văn Tiến Dũng") hoặc ngày sai ("8/5/1954") -> không được supported, trace ghi blocked_by_value_guard;
     d) entailment 0.79 -> không supported (ngưỡng biên); 0.80 -> được nhận nếu chốt giá trị qua;
     e) contradiction 0.95 -> contradicted; 0.89 -> không;
     f) fallback chọn bằng chứng: câu hỏi "Chiến dịch Điện Biên Phủ diễn ra từ ngày nào đến ngày nào?" + "Chiến dịch bắt đầu ngày 13/3/1954 và kết thúc ngày 7/5/1954." có premise thuộc dbp1954; neo một từ như "đến" không được kéo sự kiện decree1945;
     g) metadata có rules_label, nli_trace, algorithm_version == HYBRID_VERSION; method == "hybrid_v3".
   - Test có mô hình thật (skipif): NliModel().score cho cặp "Hồ Chí Minh không đọc Tuyên ngôn Độc lập." với câu bằng chứng F001 có contradiction > entailment; điểm lặp lại giống hệt giữa hai lần gọi.
   - test model_status trên tmp_path: thư mục rỗng -> tất cả False; tệp sai nội dung -> False.
   - test scripts/fetch_model.py KHÔNG gọi mạng: monkeypatch urllib.request.urlopen trả bytes sai -> SystemExit và không ghi tệp vào tmp_path (monkeypatch MODEL_DIR).

2. Đóng băng v3 (giống v2 nhưng file riêng): thêm vào scripts/evaluate_v3.py lệnh --freeze ghi reports/research_v3/engine_freeze.json gồm SHA-256 của src/hybrid_verifier.py, src/nli.py, các tệp đóng băng v2 (dùng code_fingerprints() từ research_evaluator), protocol.json và SHA-256 4 tệp mô hình; từ chối ghi đè nếu đã có. Thêm hàm validate_v3_freeze(). CHƯA chạy --freeze thật; chỉ test trên tmp_path bằng monkeypatch đường dẫn.

3. Đánh giá chính trên dữ liệu thật: tạo src/annotation_study_v3.py với hàm evaluate_collected_v3(facts, documents, development, accepted, nli) giống evaluate_collected trong src/annotation_study.py nhưng thêm phương pháp "hybrid_v3"; giữ nguyên các kiểm tra (accepted rỗng -> ValueError, trùng sự kiện development -> ValueError), ghi "v3_engine_matches_freeze". KHÔNG sửa src/annotation_study.py. Test bằng FakeNli.

4. Tài liệu: tạo reports/research_v3/README.md (tiếng Việt, giọng thận trọng như reports/gioi_han_nghien_cuu.md) gồm: mục tiêu v3; mô hình (id, revision, MIT, ONNX lượng tử hóa 339 MB, chạy CPU); cách cài: pip install -r requirements-v3.txt, python scripts/fetch_model.py; luật quyết định và chốt giá trị; quan sát trước khi viết luật (Võ Nguyên Giáp entailment 0.57); kết quả hồi quy đọc từ reports/research_v3/regression.json (đúng số trong tệp, ghi rõ là bộ đã xem, chỉ hồi quy); changelog từ protocol.json; giới hạn (mô hình lượng tử hóa yếu với tiếng Việt, điểm thường dưới 0.8 nên NLI ít khi kích hoạt; chốt viết hoa có thể chặn cách gọi đúng như "Bác"; chưa có dữ liệu thật). Không bịa số liệu. KHÔNG sửa README.md gốc trên nhánh này ngoài một dòng trỏ tới reports/research_v3/README.md.

Ràng buộc chung: không sửa tệp nào trong reports/research_v2/engine_freeze.json; validate_freeze() phải vẫn True. Kết thúc đạt pytest -q, ruff check ., pyright. Commit trên nhánh v3-nli, KHÔNG push, KHÔNG merge vào main.
```
