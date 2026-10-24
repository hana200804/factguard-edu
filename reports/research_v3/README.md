# Nghiên cứu v3: luật v2 kết hợp NLI offline

## Trạng thái và mục tiêu

V3 (`3.0.0-dev`, nhánh `v3-nli`) thử dùng NLI cho những đoạn mà luật v2 chưa đọc được. Câu hỏi nghiên cứu là: **có tăng số ca kết luận đúng mà không tăng số ca hỗ trợ sai không?** Luật v2 và dữ liệu đã đóng băng được giữ nguyên. Đây là module thử nghiệm, chưa thay phương pháp v2 trong giao diện chính.

Hiện có kết quả hồi quy trên dữ liệu tổng hợp đã xem. **Chưa có kết quả đánh giá v3 trên câu trả lời AI thật được hai người gán nhãn đồng thuận.** V3 đã được đóng băng lúc `2026-10-24T15:40:16+00:00` (UTC), **trước khi có bất kỳ câu trả lời AI thật nào**; manifest ở [engine_freeze.json](engine_freeze.json). Đóng băng không có nghĩa là đã được kiểm chứng độc lập.

Thiết kế, ngưỡng và lịch sử sửa luật nằm trong [protocol.json](protocol.json). Những giới hạn của kho dữ kiện và thiết kế v2 vẫn áp dụng; xem [giới hạn nghiên cứu](../gioi_han_nghien_cuu.md).

## Mô hình và cài đặt

Thông tin được khóa trong [src/nli.py](../../src/nli.py) và `protocol.json`:

| Thuộc tính | Giá trị |
| --- | --- |
| Model ID | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` |
| Revision | `b5113eb38ab63efdd7f280f8c144ea8b13f978ce` |
| Giấy phép mô hình | MIT, theo metadata và tệp `LICENSE` đi kèm mô hình |
| Tệp trọng số | `onnx/model_quantized.onnx`, ONNX lượng tử hóa |
| Dung lượng trọng số cục bộ | 338.679.133 byte, khoảng 339 MB theo hệ thập phân |
| Thực thi | ONNX Runtime, `CPUExecutionProvider`; không cần GPU hoặc API key |
| Ba đầu ra | `entailment`, `neutral`, `contradiction` |

Trọng số và tokenizer nằm trong `models/mdeberta-xnli/`; `models/` được `.gitignore` bỏ qua. Khi chia sẻ source, giữ trọng số ngoài Git/ZIP. Trước khi khởi tạo mô hình, chương trình kiểm tra SHA-256 của cả bốn tệp: `model_quantized.onnx`, `tokenizer.json`, `config.json`, `LICENSE`. Sai hoặc thiếu tệp sẽ báo lỗi; không tự chuyển sang mô hình khác.

Trên máy mới, tạo môi trường Python theo README gốc rồi chạy tại thư mục dự án:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-v3.txt
.\.venv\Scripts\python.exe scripts\fetch_model.py
```

Lần cài thư viện và tải mô hình đầu tiên cần Internet. `fetch_model.py` chỉ lưu nội dung khi SHA-256 đúng và bỏ qua tệp đã khớp. **Máy hiện tại đã có mô hình; không cần tải lại.** Sau khi chuẩn bị đủ, suy luận chạy offline. Kiểm tra tình trạng tệp bằng:

```powershell
.\.venv\Scripts\python.exe -c "from src.nli import model_status; print(model_status())"
```

## Luật quyết định và chốt giá trị

1. Chạy luật v2 trước. Nếu v2 đã trả `supported` hoặc `contradicted`, v3 giữ kết quả và không gọi NLI.
2. NLI chỉ xét issue `uncovered_content` hoặc `unknown_relation`. Các chốt khác như tiền đề câu hỏi sai, câu hỏi mở, phạm vi phủ định hoặc nguồn xung đột vẫn ngăn việc dùng NLI để kết luận. Issue `missing_requested_attribute` được giữ lại, NLI không tự xóa.
3. Bằng chứng là các câu tham chiếu của dữ kiện đã xác minh thuộc sự kiện nhận ra từ câu hỏi, đoạn trả lời hoặc mệnh đề v2 đã kiểm. Khi chưa nhận đủ quan hệ, chỉ dùng sự kiện duy nhất khớp một nhóm neo có ít nhất hai từ. Neo một từ như “đến” không đủ để chọn sự kiện.
4. `contradiction >= 0.90` cho nhãn `contradicted` và lời nhắc người đọc xác nhận. Chốt giá trị không phải điều kiện của nhánh mâu thuẫn.
5. `entailment >= 0.80` chỉ được chấp nhận nếu chốt giá trị qua: ngày, tên và địa điểm được nhận dạng phải khớp dữ kiện; mọi số và từ viết hoa, trừ từ đầu đoạn, phải xuất hiện trong bằng chứng. Entailment cao nhưng chốt không qua được ghi `blocked_by_value_guard`.
6. Chỉ trả `supported` khi hết issue chưa giải quyết và các mệnh đề đã kiểm đều được hỗ trợ. Phần chưa đối chiếu còn lại dẫn tới `insufficient` hoặc `undetermined` tùy lý do.

Ngưỡng `0.80` và `0.90` đã ghi trong protocol trước phép đo; không đổi theo kết quả hồi quy. Điểm NLI là đầu ra phân loại của mô hình, chưa được hiệu chuẩn thành xác suất câu trả lời lịch sử đúng. Kết quả lưu `rules_label`, `nli_trace`, phiên bản thuật toán và tên phương pháp `hybrid_v3` để đọc lại quyết định.

### Quan sát trước khi viết luật

`protocol.json` ghi lại lần thử trước khi viết luật: câu “Võ Nguyên Giáp đọc Tuyên ngôn Độc lập” nhận entailment **0,57** so với bằng chứng về Hồ Chí Minh. Đây là quan sát thăm dò đã được ghi lại, dùng để giải thích nhu cầu chốt giá trị; không phải thử nghiệm độc lập mới hay tỷ lệ lỗi của mô hình. Mức 0,57 cũng thấp hơn ngưỡng chấp nhận 0,80. Tài liệu này không chạy lại để biến quan sát đó thành kết quả mới.

## Hồi quy đã lưu

Bảng sau đọc từ [regression.json](regression.json), thời điểm `2026-10-24T11:14:30+00:00`, cùng revision mô hình nêu trên. `claims_guarded` là luật v2; `hybrid_v3` là luật v2 kết hợp NLI.

| Bộ đã xem | Phương pháp | Đúng / tổng | Accuracy | Macro F1 | Hỗ trợ sai / ca gold không supported |
| --- | --- | ---: | ---: | ---: | ---: |
| v1 development | claims_guarded | 24/24 | 100,00% | 1,0000 | 0/16 |
| v1 development | hybrid_v3 | 24/24 | 100,00% | 1,0000 | 0/16 |
| v1 evaluation | claims_guarded | 80/87 | 91,95% | 0,9572 | 0/60 |
| v1 evaluation | hybrid_v3 | 80/87 | 91,95% | 0,9572 | 0/60 |
| v2 challenge | claims_guarded | 42/46 | 91,30% | 0,9391 | 0/30 |
| v2 challenge | hybrid_v3 | 43/46 | 93,48% | 0,9621 | 0/30 |

Có **1 ca đổi nhãn** giữa hai phương pháp trong kết quả đã lưu. `false_support_count` đếm ca gold khác `supported` nhưng máy trả `supported`; mẫu số là `non_supported_gold_count`. Không quan sát hỗ trợ sai trong các ca này không chứng minh rủi ro bằng không.

**Cả ba bộ đều đã được xem khi phát triển v2; đây chỉ là hồi quy.** Development còn được dùng để phát triển phương pháp. Những con số trên không chứng minh v3 vượt trội ngoài thực tế và không thay thế đánh giá trên dữ liệu thật giữ riêng. V2 ở bảng là `claims_guarded` chạy trong phép đo v3, không phải phương pháp v1 `rules_single_v1`; vì vậy không thay các số liệu báo cáo v1/v2 cũ bằng bảng này. Mã đo ở [scripts/evaluate_v3.py](../../scripts/evaluate_v3.py); chạy không có `--freeze` sẽ ghi lại tệp hồi quy, nên chỉ chạy khi chủ động muốn tạo lần đo mới.

## Changelog theo protocol

Ba thay đổi đều được ghi ngày 24/10/2026. Không gọi toàn bộ logic hiện tại là đã định trước phép đo đầu tiên:

1. **Sau lần hồi quy đầu** (v3 đúng 43/46 challenge, 0 hỗ trợ sai) và câu thử tự viết: thêm dự phòng chọn bằng chứng theo sự kiện duy nhất khớp một nhóm neo. Câu hỏi về thời gian bắt đầu/kết thúc Điện Biên Phủ trước đó không có bằng chứng cho NLI. Ngưỡng giữ nguyên.
2. **Sau khi gỡ lỗi câu thử đó:** dự phòng chỉ dùng neo từ hai âm tiết trở lên; neo một từ “đến” của quan hệ `decree.election` đã kéo nhầm sự kiện.
3. **Sau câu thử “Đại tướng Văn Tiến Dũng” qua được chốt vì tên ngoài từ điển:** bổ sung kiểm tra từ viết hoa, trừ từ đầu đoạn, phải có trong bằng chứng. Chốt này có thể chặn cả cách gọi đúng như “Bác”, “Đại tướng”.

## Đóng băng và đánh giá dữ liệu thật

Quy trình dự kiến: xem diff và duyệt logic → đóng băng → thu câu trả lời mới → gán nhãn độc lập trước khi xem dự đoán → đánh giá. Bất kỳ ca thật nào đã xem khi sửa luật đều không còn là dữ liệu đánh giá chưa biết. Nếu sửa sau đóng băng, cần phiên bản/protocol và bộ đánh giá mới, không chỉnh rồi dùng lại nhãn “chưa xem”.

**Lệnh dưới đây đã chạy ngày 24/10/2026 và manifest đã tồn tại**; chạy lại sẽ bị từ chối. Mọi sửa đổi v3 từ nay cần phiên bản và protocol mới:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_v3.py --freeze
```

Manifest `reports/research_v3/engine_freeze.json` khóa SHA-256 của hai module NLI/hybrid, các tệp v2 do `code_fingerprints()` liệt kê, protocol, mã đánh giá/kiểm tra đóng băng và bốn tệp mô hình. Lệnh từ chối ghi đè manifest đã có. Sau khi tạo, kiểm tra bằng:

```powershell
.\.venv\Scripts\python.exe -c "from src.v3_freeze import validate_v3_freeze; print(validate_v3_freeze())"
.\.venv\Scripts\python.exe -c "from src.research_evaluator import validate_freeze; print(validate_freeze())"
```

Chưa có manifest v3 thì không được mô tả là khớp đóng băng. Kiểm tra v2 riêng vẫn cần trả `True`.

Hàm [evaluate_collected_v3](../../src/annotation_study_v3.py) nhận `facts, documents, development, accepted, nli`, thêm phương pháp `hybrid_v3` vào phép đo ca đã được chấp nhận. `accepted` phải được lấy từ luồng đồng thuận của người gán nhãn, không lấy từ nhãn máy. Hàm từ chối tập rỗng và sự kiện trùng development; kết quả báo `v3_engine_matches_freeze` để phân biệt điểm đo với trạng thái mã. Hàm đánh giá không thay việc duyệt nguồn, kiểm tra đóng băng hoặc giữ kín dữ liệu.

Xem [hướng dẫn thu thập](../huong_dan_thu_thap.md) và [hướng dẫn gán nhãn](../huong_dan_gan_nhan.md). Hai tên khác nhau cùng nhãn là điều kiện kỹ thuật của luồng hiện tại; danh tính tự khai không chứng minh hai người độc lập. Các ca này chỉ có nhãn câu trả lời và ID nguồn, chưa có chuẩn mệnh đề/bằng chứng chi tiết, nên phép đo chưa kết luận chất lượng trích từng mệnh đề hay hiệu quả học tập.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pyright
```

Kiểm thử logic dùng `FakeNli`, không cần tải trọng số; kiểm thử mô hình thật được bỏ qua khi các tệp mô hình thiếu hoặc không khớp SHA-256. Các test tải mô hình giả lập phản hồi, không gọi mạng. Test đóng băng dùng thư mục tạm, không tạo manifest v3 thật. Test đánh giá dùng ca kiểm thử, không phải dữ liệu người dùng đã thu.

## Giới hạn riêng của v3

- Mô hình lượng tử hóa còn yếu với các cách diễn đạt tiếng Việt đã thử; điểm thường dưới 0,80 nên NLI ít khi kích hoạt. Chưa có benchmark độc lập để ước lượng mức độ yếu hay lợi ích trên dân số câu hỏi rộng hơn.
- Chốt viết hoa/từ vựng thận trọng có thể từ chối cách gọi đúng như “Bác”, danh xưng, tên khác hoặc biến thể không có trong bằng chứng. Các ngày/tên mà parser không nhận ra và từ đầu đoạn vẫn là điểm cần nghiên cứu.
- NLI suy từ câu tham chiếu trong kho; kho thiếu, sai hoặc không chọn được sự kiện thì không thể xem kết quả như xác minh ngoài kho. Ghép nhiều câu cùng sự kiện không bảo đảm mô hình gắn đúng từng vai trò.
- Đầu vào tokenizer bị cắt ở 256 token. Câu dài hoặc bằng chứng dài có thể mất nội dung; điểm cao không bảo đảm đã đọc hết đoạn gốc.
- Nhánh mâu thuẫn dựa trên ngưỡng NLI; con người vẫn cần đọc lại nguồn. Không có hiệu chuẩn xác suất hay bằng chứng rủi ro bằng không.
- Hồi quy đã xem và các chỉnh sửa sau đo không tạo bằng chứng khái quát. Chưa có dữ liệu thật để kết luận mô hình giúp ích cho người dùng, giáo viên hoặc học sinh.
