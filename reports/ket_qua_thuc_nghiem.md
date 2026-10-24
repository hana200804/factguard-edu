# Tóm tắt kết quả đo thực tế

87 ca đánh giá / 29 câu hỏi phân biệt. Câu trả lời tổng hợp có chủ đích; chưa có thẩm định nhãn độc lập.

| Phương pháp | Accuracy | F1 macro | Tỷ lệ từ chối tự kết luận |
|---|---:|---:|---:|
| Baseline | 51.72% | 0.4048 | 0.00% |
| Proposed | 93.10% | 0.9657 | 6.90% |

Thời điểm chạy: 2026-10-24T08:58:03+00:00 (UTC). Các ca từ chối được tính sai, không bỏ khỏi mẫu số. Chưa kiểm định hiệu quả học tập hoặc độ chính xác trên dữ liệu ngoài thực tế. Không diễn giải precision 1.0 trên bộ nhỏ là bảo đảm không có false positive.

Báo cáo đầy đủ, từng nhãn, ma trận, nhóm và ca thất bại bên dưới.

# Kết quả thực nghiệm FactGuard EDU

Thời điểm chạy (UTC): 2026-10-24T08:58:03+00:00.
Phiên bản thuật toán: 1.0.0. Tập: evaluation.
Số ca mỗi phương pháp: 87; số câu hỏi phân biệt: 29.

Các câu trả lời kiểm thử do người xây dựng dự án tạo có chủ đích; không phải mẫu thu từ học sinh hay ChatGPT.
Kết quả chỉ mô tả bộ kiểm thử nhỏ và kho tham chiếu hiện tại, chưa chứng minh hiệu quả trên quần thể học sinh.

## So sánh

| Phương pháp | Accuracy | Precision macro | Recall macro | F1 macro | Từ chối tự kết luận | Chưa kết luận đúng/sai | TB (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.5172 | 0.3579 | 0.5152 | 0.4048 | 0.0000 | 0.3448 | 0.915 |
| proposed | 0.9310 | 1.0000 | 0.9349 | 0.9657 | 0.0690 | 0.4023 | 1.452 |

Accuracy tính trên toàn bộ ca; undetermined khác cả ba nhãn chuẩn nên tính là sai.
Macro lấy trung bình ba nhãn chuẩn. Precision/recall/F1 mẫu số 0 được ghi 0.
Từ chối tự kết luận = undetermined/n. Chưa kết luận đúng/sai = (insufficient + undetermined)/n.
Thời gian đo từng lời gọi kiểm chứng, không gồm khởi tạo chỉ mục/giao diện; không phải benchmark phần cứng.

## baseline: theo nhãn

| Nhãn | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Có bằng chứng hỗ trợ | 0.4737 | 1.0000 | 0.6429 | 27 |
| Mâu thuẫn với bằng chứng | 0.0000 | 0.0000 | 0.0000 | 27 |
| Chưa đủ bằng chứng | 0.6000 | 0.5455 | 0.5714 | 33 |

Ma trận nhầm lẫn (hàng = nhãn chuẩn; cột = dự đoán):

Thứ tự: supported, contradicted, insufficient, undetermined

```json
[[27, 0, 0, 0], [15, 0, 12, 0], [15, 0, 18, 0], [0, 0, 0, 0]]
```

### Theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Biến thể cách viết | 2 | 1.0000 |
| Câu trả lời không đủ thông tin | 25 | 0.5600 |
| Nhầm nhân vật hoặc địa danh | 14 | 0.0000 |
| Nội dung nằm ngoài tài liệu | 8 | 0.5000 |
| Phủ định cần người đọc | 2 | 0.0000 |
| Sai mốc thời gian | 11 | 0.0000 |
| Đúng ngày tháng năm | 11 | 1.0000 |
| Đúng nhân vật hoặc địa danh | 14 | 1.0000 |

### Các ca thất bại: 42

- E002: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E003: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E005: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E008: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E011: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E014: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E017: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E018: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E020: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E021: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E023: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E026: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E027: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E029: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E030: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E032: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E033: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E035: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E038: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E041: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E044: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E045: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E047: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E048: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E050: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E053: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E056: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E057: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E059: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E062: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E065: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E068: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E069: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E071: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E074: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E075: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E100: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E101: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E102: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E103: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E104: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E105: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.

## proposed: theo nhãn

| Nhãn | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Có bằng chứng hỗ trợ | 1.0000 | 1.0000 | 1.0000 | 27 |
| Mâu thuẫn với bằng chứng | 1.0000 | 0.9259 | 0.9615 | 27 |
| Chưa đủ bằng chứng | 1.0000 | 0.8788 | 0.9355 | 33 |

Ma trận nhầm lẫn (hàng = nhãn chuẩn; cột = dự đoán):

Thứ tự: supported, contradicted, insufficient, undetermined

```json
[[27, 0, 0, 0], [0, 25, 0, 2], [0, 0, 29, 4], [0, 0, 0, 0]]
```

### Theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Biến thể cách viết | 2 | 1.0000 |
| Câu trả lời không đủ thông tin | 25 | 1.0000 |
| Nhầm nhân vật hoặc địa danh | 14 | 1.0000 |
| Nội dung nằm ngoài tài liệu | 8 | 0.5000 |
| Phủ định cần người đọc | 2 | 0.0000 |
| Sai mốc thời gian | 11 | 1.0000 |
| Đúng ngày tháng năm | 11 | 1.0000 |
| Đúng nhân vật hoặc địa danh | 14 | 1.0000 |

### Các ca thất bại: 6

- E100: chuẩn `insufficient`, dự đoán `undetermined`. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- E101: chuẩn `insufficient`, dự đoán `undetermined`. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- E102: chuẩn `insufficient`, dự đoán `undetermined`. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- E103: chuẩn `insufficient`, dự đoán `undetermined`. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- E104: chuẩn `contradicted`, dự đoán `undetermined`. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- E105: chuẩn `contradicted`, dự đoán `undetermined`. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.

## Khả năng tái lập

Dự đoán xác định, không dùng số ngẫu nhiên. Thời gian có thể thay đổi theo máy/lần chạy.
Kho tri thức chứa đáp án tham chiếu cho các sự kiện được đánh giá: đây là bài toán kiểm chứng trong kho đóng, không phải kiểm tra ghi nhớ của mô hình.
Tách development/evaluation theo event_id. Quy tắc không được điều chỉnh dựa trên điểm evaluation.
Baseline chỉ khớp từ, không có nhãn mâu thuẫn: đây là baseline đơn giản và yếu; chưa so với hệ thống kiểm chứng tiên tiến.
Cần bộ đánh giá độc lập do giáo viên gán nhãn, mở rộng dữ liệu và nghiên cứu người dùng trước khi suy rộng.

## Môi trường

```json
{
  "python": "3.12.10",
  "platform": "Windows-11-10.0.26200-SP0",
  "packages": {
    "streamlit": "1.66.1",
    "pandas": "3.0.6",
    "scikit-learn": "1.9.1",
    "rapidfuzz": "3.14.6",
    "pypdf": "6.21.2",
    "plotly": "6.9.0"
  }
}
```
