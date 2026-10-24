# Kết quả thực nghiệm FactGuard EDU

Thời điểm chạy (UTC): 2026-10-24T08:58:01+00:00.
Phiên bản thuật toán: 1.0.0. Tập: development.
Số ca mỗi phương pháp: 24; số câu hỏi phân biệt: 8.

Các câu trả lời kiểm thử do người xây dựng dự án tạo có chủ đích; không phải mẫu thu từ học sinh hay ChatGPT.
Kết quả chỉ mô tả bộ kiểm thử nhỏ và kho tham chiếu hiện tại, chưa chứng minh hiệu quả trên quần thể học sinh.

## So sánh

| Phương pháp | Accuracy | Precision macro | Recall macro | F1 macro | Từ chối tự kết luận | Chưa kết luận đúng/sai | TB (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.5833 | 0.3889 | 0.5833 | 0.4667 | 0.0000 | 0.5000 | 0.908 |
| proposed | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.3333 | 1.491 |

Accuracy tính trên toàn bộ ca; undetermined khác cả ba nhãn chuẩn nên tính là sai.
Macro lấy trung bình ba nhãn chuẩn. Precision/recall/F1 mẫu số 0 được ghi 0.
Từ chối tự kết luận = undetermined/n. Chưa kết luận đúng/sai = (insufficient + undetermined)/n.
Thời gian đo từng lời gọi kiểm chứng, không gồm khởi tạo chỉ mục/giao diện; không phải benchmark phần cứng.

## baseline: theo nhãn

| Nhãn | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Có bằng chứng hỗ trợ | 0.6667 | 1.0000 | 0.8000 | 8 |
| Mâu thuẫn với bằng chứng | 0.0000 | 0.0000 | 0.0000 | 8 |
| Chưa đủ bằng chứng | 0.5000 | 0.7500 | 0.6000 | 8 |

Ma trận nhầm lẫn (hàng = nhãn chuẩn; cột = dự đoán):

Thứ tự: supported, contradicted, insufficient, undetermined

```json
[[8, 0, 0, 0], [2, 0, 6, 0], [2, 0, 6, 0], [0, 0, 0, 0]]
```

### Theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Câu trả lời không đủ thông tin | 8 | 0.7500 |
| Nhầm nhân vật hoặc địa danh | 6 | 0.0000 |
| Sai mốc thời gian | 2 | 0.0000 |
| Đúng ngày tháng năm | 2 | 1.0000 |
| Đúng nhân vật hoặc địa danh | 6 | 1.0000 |

### Các ca thất bại: 10

- E077: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E078: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E080: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E083: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E086: chuẩn `contradicted`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E087: chuẩn `insufficient`, dự đoán `supported`. Baseline khớp từ với đáp án; chưa phân tích phủ định, quan hệ hay mâu thuẫn.
- E089: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E092: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E095: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.
- E098: chuẩn `contradicted`, dự đoán `insufficient`. So khớp từ đơn giản không tìm thấy câu trả lời tương ứng.

## proposed: theo nhãn

| Nhãn | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Có bằng chứng hỗ trợ | 1.0000 | 1.0000 | 1.0000 | 8 |
| Mâu thuẫn với bằng chứng | 1.0000 | 1.0000 | 1.0000 | 8 |
| Chưa đủ bằng chứng | 1.0000 | 1.0000 | 1.0000 | 8 |

Ma trận nhầm lẫn (hàng = nhãn chuẩn; cột = dự đoán):

Thứ tự: supported, contradicted, insufficient, undetermined

```json
[[8, 0, 0, 0], [0, 8, 0, 0], [0, 0, 8, 0], [0, 0, 0, 0]]
```

### Theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Câu trả lời không đủ thông tin | 8 | 1.0000 |
| Nhầm nhân vật hoặc địa danh | 6 | 1.0000 |
| Sai mốc thời gian | 2 | 1.0000 |
| Đúng ngày tháng năm | 2 | 1.0000 |
| Đúng nhân vật hoặc địa danh | 6 | 1.0000 |

### Các ca thất bại: 0


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
