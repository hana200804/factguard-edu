# Nghiên cứu kiểm chứng mệnh đề FactGuard EDU v2

Lần chạy: 2026-10-24T09:55:12+00:00 (UTC).
46 ca/phương pháp; 10 cụm sự kiện; 4 phương pháp.
**Dữ liệu tổng hợp do trợ lý xây dựng, chưa gán nhãn độc lập. Không phải kết quả nghiên cứu học sinh.**

## Câu hỏi nghiên cứu

Tách mệnh đề và chặn quan hệ/phạm vi chưa rõ có giảm kết luận hỗ trợ sai trên bộ thử thách này không?

## Đối chứng và ablation

- lexical_3way: TF-IDF ký tự và 6 đặc trưng từ vựng, StandardScaler + LogisticRegression, học ba nhãn chỉ trên 24 ca development v1.
- rules_single_v1: luật một dữ kiện của bản đầu, giữ nguyên.
- claims_no_guard: bộ trích mệnh đề v2, tắt chốt tiền đề câu hỏi và nội dung dư; vẫn kiểm tra giá trị và tính hợp lệ nguồn.
- claims_guarded: đầy đủ bộ trích, đối chiếu, chốt tiền đề/vai trò và theo dõi phần chưa xử lý.

| Phương pháp | Accuracy | F1 macro | Hỗ trợ sai / ca không được hỗ trợ | Kết luận đúng/sai | Rủi ro trên ca có kết luận | Đúng nhãn + đủ bằng chứng |
|---|---:|---:|---:|---:|---:|---:|
| lexical_3way | 0.3696 | 0.1858 | 0.0667 | 1.0000 | 0.6304 | 0.0217 |
| rules_single_v1 | 0.0217 | 0.0476 | 0.0333 | 0.0217 | 1.0000 | 0.0217 |
| claims_no_guard | 0.8696 | 0.8539 | 0.1667 | 0.8043 | 0.1351 | 0.8478 |
| claims_guarded | 0.9130 | 0.9391 | 0.0000 | 0.6739 | 0.0000 | 0.9130 |

Accuracy tính mọi ca; undetermined vẫn tính sai. Coverage chỉ tính supported/contradicted; risk là tỷ lệ sai trong các ca đó.
Hỗ trợ sai = số ca dự đoán supported khi nhãn chuẩn khác supported / tổng ca nhãn chuẩn khác supported.
Đúng nhãn + đủ bằng chứng yêu cầu tập ID dữ kiện chuẩn nằm trong dữ kiện được phương pháp quy trách nhiệm; không tính các đoạn truy xuất ngẫu nhiên như đã kiểm chứng.

## Phân tích từng giai đoạn

| Phương pháp | Recall trích giá trị | Recall đúng nhãn mệnh đề | Precision trích giá trị | Thời gian TB / median / p95 (ms) |
|---|---:|---:|---:|---:|
| lexical_3way | 0.0000 | 0.0000 | không xác định | 1.927 / 1.870 / 2.441 |
| rules_single_v1 | 0.0000 | 0.0000 | 0.0000 | 1.013 / 0.966 / 1.301 |
| claims_no_guard | 0.9677 | 0.9677 | 0.9231 | 3.739 / 3.730 / 5.457 |
| claims_guarded | 0.9677 | 0.9677 | 0.9836 | 4.212 / 4.374 / 6.098 |

Recall@4 trung bình của truy xuất từ vựng trước tra cứu có cấu trúc: 0.9861. Chỉ tính ca có ID bằng chứng chuẩn.
Những ca nguồn bị rút khỏi kho làm phép thử mất bằng chứng; mọi phương pháp đều dùng cùng kho bị rút của ca đó.
Các đối chứng không có bộ trích mệnh đề không được diễn giải điểm trích bằng 0 là lỗi phân loại; đó là khả năng không triển khai ở phương pháp đó.

## Khoảng biến thiên theo cụm sự kiện

```json
{
  "first": "claims_guarded",
  "second": "lexical_3way",
  "n_clusters": 10,
  "estimate": 0.5528571428571428,
  "lower": 0.48571428571428577,
  "upper": 0.6599999999999999,
  "replicates": 2000,
  "seed": 20261024,
  "estimand": "Mean paired accuracy difference with equal weight per event cluster",
  "caution": "Mô tả thăm dò trên số ít cụm tổng hợp; không suy rộng tới người học hay mọi câu trả lời AI."
}
```
Bootstrap cặp 2.000 lần, cùng trọng số cho từng cụm sự kiện, seed cố định. Khoảng này có tính thăm dò trên số ít cụm do tác giả chọn; không phải bảo đảm xác suất cho câu trả lời mới hay kết luận tác động giáo dục.

## lexical_3way: theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Câu sự kiện đầy đủ | 5 | 0.0000 |
| Hoán đổi mốc giữa quan hệ | 2 | 1.0000 |
| Hoán đổi địa phương | 2 | 1.0000 |
| Không xác định dữ kiện | 1 | 0.0000 |
| Nhiều dữ kiện đúng | 4 | 0.0000 |
| Nhiều mốc khác quan hệ | 2 | 0.0000 |
| Nhân vật trong câu đầy đủ | 4 | 0.5000 |
| Nhầm địa điểm | 1 | 1.0000 |
| Nội dung thêm ngoài nguồn | 2 | 0.0000 |
| Phủ định phức tạp | 1 | 1.0000 |
| Phủ định đơn | 2 | 0.5000 |
| Sai ngày cùng năm | 2 | 1.0000 |
| Suy luận ngoài phạm vi | 1 | 0.0000 |
| Sự kiện ngoài kho | 2 | 0.0000 |
| Thiếu dữ kiện để đối chiếu | 1 | 0.0000 |
| Thu hồi bằng chứng | 2 | 0.0000 |
| Tiền đề câu hỏi sai | 2 | 0.0000 |
| Đúng một phần | 6 | 1.0000 |
| Đồng tham chiếu lược chủ ngữ | 1 | 0.0000 |
| Đổi vai trò trong câu | 1 | 0.0000 |
| Độ chi tiết thời gian | 2 | 0.0000 |

Chỉ số từng nhãn:

```json
{
  "supported": {
    "precision": 0.0,
    "recall": 0.0,
    "f1-score": 0.0,
    "support": 16.0
  },
  "contradicted": {
    "precision": 0.38636363636363635,
    "recall": 1.0,
    "f1-score": 0.5573770491803278,
    "support": 17.0
  },
  "insufficient": {
    "precision": 0.0,
    "recall": 0.0,
    "f1-score": 0.0,
    "support": 13.0
  }
}
```

Ma trận (hàng chuẩn/cột dự đoán, thứ tự supported, contradicted, insufficient, undetermined):

```json
[[0, 16, 0, 0], [0, 17, 0, 0], [2, 11, 0, 0], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R001: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R005: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R008: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R009: chuẩn insufficient, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R010: chuẩn insufficient, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R011: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R012: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R013: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R014: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R015: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R018: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R019: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R021: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R022: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R023: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R024: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R025: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R027: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R029: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R031: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R033: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R035: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R037: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R039: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R041: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R043: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R044: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R045: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R046: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
## rules_single_v1: theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Câu sự kiện đầy đủ | 5 | 0.0000 |
| Hoán đổi mốc giữa quan hệ | 2 | 0.0000 |
| Hoán đổi địa phương | 2 | 0.0000 |
| Không xác định dữ kiện | 1 | 0.0000 |
| Nhiều dữ kiện đúng | 4 | 0.0000 |
| Nhiều mốc khác quan hệ | 2 | 0.0000 |
| Nhân vật trong câu đầy đủ | 4 | 0.0000 |
| Nhầm địa điểm | 1 | 0.0000 |
| Nội dung thêm ngoài nguồn | 2 | 0.0000 |
| Phủ định phức tạp | 1 | 0.0000 |
| Phủ định đơn | 2 | 0.0000 |
| Sai ngày cùng năm | 2 | 0.0000 |
| Suy luận ngoài phạm vi | 1 | 0.0000 |
| Sự kiện ngoài kho | 2 | 0.0000 |
| Thiếu dữ kiện để đối chiếu | 1 | 0.0000 |
| Thu hồi bằng chứng | 2 | 0.5000 |
| Tiền đề câu hỏi sai | 2 | 0.0000 |
| Đúng một phần | 6 | 0.0000 |
| Đồng tham chiếu lược chủ ngữ | 1 | 0.0000 |
| Đổi vai trò trong câu | 1 | 0.0000 |
| Độ chi tiết thời gian | 2 | 0.0000 |

Chỉ số từng nhãn:

```json
{
  "supported": {
    "precision": 0.0,
    "recall": 0.0,
    "f1-score": 0.0,
    "support": 16.0
  },
  "contradicted": {
    "precision": 0.0,
    "recall": 0.0,
    "f1-score": 0.0,
    "support": 17.0
  },
  "insufficient": {
    "precision": 1.0,
    "recall": 0.07692307692307693,
    "f1-score": 0.14285714285714285,
    "support": 13.0
  }
}
```

Ma trận (hàng chuẩn/cột dự đoán, thứ tự supported, contradicted, insufficient, undetermined):

```json
[[0, 0, 0, 16], [0, 0, 0, 17], [1, 0, 1, 11], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R001: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R002: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R003: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R004: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R005: chuẩn supported, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R006: chuẩn contradicted, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R007: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R008: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R009: chuẩn insufficient, dự đoán supported. Tên riêng khớp một cách viết đã kiểm tra trong dữ kiện tham chiếu.
- R010: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R011: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R012: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R013: chuẩn insufficient, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R014: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R015: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R016: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R017: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R018: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R019: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R020: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R021: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R022: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R023: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R025: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R026: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R027: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R028: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R029: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R030: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R031: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R032: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R033: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R034: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R035: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R036: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R037: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R038: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R039: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R040: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R041: chuẩn supported, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R042: chuẩn contradicted, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R043: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R044: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R045: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R046: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
## claims_no_guard: theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Câu sự kiện đầy đủ | 5 | 1.0000 |
| Hoán đổi mốc giữa quan hệ | 2 | 1.0000 |
| Hoán đổi địa phương | 2 | 1.0000 |
| Không xác định dữ kiện | 1 | 1.0000 |
| Nhiều dữ kiện đúng | 4 | 1.0000 |
| Nhiều mốc khác quan hệ | 2 | 1.0000 |
| Nhân vật trong câu đầy đủ | 4 | 1.0000 |
| Nhầm địa điểm | 1 | 1.0000 |
| Nội dung thêm ngoài nguồn | 2 | 0.0000 |
| Phủ định phức tạp | 1 | 0.0000 |
| Phủ định đơn | 2 | 1.0000 |
| Sai ngày cùng năm | 2 | 1.0000 |
| Suy luận ngoài phạm vi | 1 | 1.0000 |
| Sự kiện ngoài kho | 2 | 1.0000 |
| Thiếu dữ kiện để đối chiếu | 1 | 1.0000 |
| Thu hồi bằng chứng | 2 | 1.0000 |
| Tiền đề câu hỏi sai | 2 | 0.0000 |
| Đúng một phần | 6 | 1.0000 |
| Đồng tham chiếu lược chủ ngữ | 1 | 1.0000 |
| Đổi vai trò trong câu | 1 | 0.0000 |
| Độ chi tiết thời gian | 2 | 1.0000 |

Chỉ số từng nhãn:

```json
{
  "supported": {
    "precision": 0.7619047619047619,
    "recall": 1.0,
    "f1-score": 0.8648648648648649,
    "support": 16.0
  },
  "contradicted": {
    "precision": 1.0,
    "recall": 0.9411764705882353,
    "f1-score": 0.9696969696969697,
    "support": 17.0
  },
  "insufficient": {
    "precision": 0.8888888888888888,
    "recall": 0.6153846153846154,
    "f1-score": 0.7272727272727273,
    "support": 13.0
  }
}
```

Ma trận (hàng chuẩn/cột dự đoán, thứ tự supported, contradicted, insufficient, undetermined):

```json
[[16, 0, 0, 0], [0, 16, 1, 0], [5, 0, 8, 0], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R007: chuẩn contradicted, dự đoán insufficient. Chưa có đủ mệnh đề có thể đối chiếu với nguồn đã xác minh.
- R008: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 2 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R009: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 1 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R010: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 1 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R011: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 3 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R023: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 1 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
## claims_guarded: theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Câu sự kiện đầy đủ | 5 | 1.0000 |
| Hoán đổi mốc giữa quan hệ | 2 | 1.0000 |
| Hoán đổi địa phương | 2 | 1.0000 |
| Không xác định dữ kiện | 1 | 1.0000 |
| Nhiều dữ kiện đúng | 4 | 1.0000 |
| Nhiều mốc khác quan hệ | 2 | 1.0000 |
| Nhân vật trong câu đầy đủ | 4 | 1.0000 |
| Nhầm địa điểm | 1 | 1.0000 |
| Nội dung thêm ngoài nguồn | 2 | 1.0000 |
| Phủ định phức tạp | 1 | 0.0000 |
| Phủ định đơn | 2 | 1.0000 |
| Sai ngày cùng năm | 2 | 1.0000 |
| Suy luận ngoài phạm vi | 1 | 1.0000 |
| Sự kiện ngoài kho | 2 | 1.0000 |
| Thiếu dữ kiện để đối chiếu | 1 | 1.0000 |
| Thu hồi bằng chứng | 2 | 1.0000 |
| Tiền đề câu hỏi sai | 2 | 0.0000 |
| Đúng một phần | 6 | 1.0000 |
| Đồng tham chiếu lược chủ ngữ | 1 | 0.0000 |
| Đổi vai trò trong câu | 1 | 1.0000 |
| Độ chi tiết thời gian | 2 | 1.0000 |

Chỉ số từng nhãn:

```json
{
  "supported": {
    "precision": 1.0,
    "recall": 0.9375,
    "f1-score": 0.967741935483871,
    "support": 16.0
  },
  "contradicted": {
    "precision": 1.0,
    "recall": 0.9411764705882353,
    "f1-score": 0.9696969696969697,
    "support": 17.0
  },
  "insufficient": {
    "precision": 0.9166666666666666,
    "recall": 0.8461538461538461,
    "f1-score": 0.88,
    "support": 13.0
  }
}
```

Ma trận (hàng chuẩn/cột dự đoán, thứ tự supported, contradicted, insufficient, undetermined):

```json
[[15, 0, 1, 0], [0, 16, 0, 1], [0, 0, 11, 2], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R007: chuẩn contradicted, dự đoán undetermined. Có phần chưa thể xử lý tự động; các mệnh đề đã kiểm tra được liệt kê riêng.
- R009: chuẩn insufficient, dự đoán undetermined. Cần kiểm tra tiền đề câu hỏi trước khi đối chiếu câu trả lời.
- R010: chuẩn insufficient, dự đoán undetermined. Cần kiểm tra tiền đề câu hỏi trước khi đối chiếu câu trả lời.
- R018: chuẩn supported, dự đoán insufficient. Chưa đủ bằng chứng để hỗ trợ toàn bộ nội dung được hỏi; có phần chưa được đối chiếu.

## Giới hạn diễn giải

Bộ thử thách được tạo sau đóng băng mã nhưng cùng trợ lý thiết kế cả mã và dữ liệu; không phải đánh giá mù hoặc độc lập. V1 evaluation đã xem nên chỉ làm hồi quy. Nguồn và nhãn cần người thật thẩm định.
Đây là kho đóng và ngữ pháp hữu hạn, chưa giải quyết mọi câu trả lời AI, mọi phép phủ định hoặc vai trò ngữ nghĩa. Không báo kết quả của người gán nhãn hay thử nghiệm học sinh khi chưa có dữ liệu thật.
Mã còn khớp bản đóng băng tại lúc đo: True.
