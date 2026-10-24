# Phân tích hậu nghiệm về dạng câu hỏi

Phân tích này được bổ sung SAU khi xem kết quả bộ chính. Thay chỉ dẫn chung bằng câu hỏi chuẩn cho những ca phù hợp, giữ nguyên đáp án và nhãn. Mục đích: kiểm tra mức phụ thuộc vào dạng đầu vào của đối chứng. Không coi là một bộ độc lập hoặc thay kết quả chính.

# Nghiên cứu kiểm chứng mệnh đề FactGuard EDU v2

Lần chạy: 2026-10-24T10:03:14+00:00 (UTC).
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
| lexical_3way | 0.4565 | 0.3476 | 0.2000 | 1.0000 | 0.5435 | 0.2609 |
| rules_single_v1 | 0.2826 | 0.3895 | 0.0333 | 0.2826 | 0.0769 | 0.2826 |
| claims_no_guard | 0.8478 | 0.8339 | 0.1667 | 0.8043 | 0.1622 | 0.8478 |
| claims_guarded | 0.9130 | 0.9419 | 0.0000 | 0.6957 | 0.0312 | 0.9130 |

Accuracy tính mọi ca; undetermined vẫn tính sai. Coverage chỉ tính supported/contradicted; risk là tỷ lệ sai trong các ca đó.
Hỗ trợ sai = số ca dự đoán supported khi nhãn chuẩn khác supported / tổng ca nhãn chuẩn khác supported.
Đúng nhãn + đủ bằng chứng yêu cầu tập ID dữ kiện chuẩn nằm trong dữ kiện được phương pháp quy trách nhiệm; không tính các đoạn truy xuất ngẫu nhiên như đã kiểm chứng.

## Phân tích từng giai đoạn

| Phương pháp | Recall trích giá trị | Recall đúng nhãn mệnh đề | Precision trích giá trị | Thời gian TB / median / p95 (ms) |
|---|---:|---:|---:|---:|
| lexical_3way | 0.0000 | 0.0000 | không xác định | 1.911 / 1.879 / 2.239 |
| rules_single_v1 | 0.3710 | 0.1935 | 0.8846 | 1.341 / 1.365 / 1.677 |
| claims_no_guard | 0.9677 | 0.9677 | 0.9091 | 4.025 / 4.288 / 5.656 |
| claims_guarded | 0.9677 | 0.9677 | 0.9677 | 5.760 / 6.606 / 8.354 |

Recall@4 trung bình của truy xuất từ vựng trước tra cứu có cấu trúc: 1.0000. Chỉ tính ca có ID bằng chứng chuẩn.
Những ca nguồn bị rút khỏi kho làm phép thử mất bằng chứng; mọi phương pháp đều dùng cùng kho bị rút của ca đó.
Các đối chứng không có bộ trích mệnh đề không được diễn giải điểm trích bằng 0 là lỗi phân loại; đó là khả năng không triển khai ở phương pháp đó.

## Khoảng biến thiên theo cụm sự kiện

```json
{
  "first": "claims_guarded",
  "second": "lexical_3way",
  "n_clusters": 10,
  "estimate": 0.39714285714285713,
  "lower": 0.225,
  "upper": 0.5643035714285713,
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
| Câu sự kiện đầy đủ | 5 | 0.4000 |
| Hoán đổi mốc giữa quan hệ | 2 | 1.0000 |
| Hoán đổi địa phương | 2 | 1.0000 |
| Không xác định dữ kiện | 1 | 0.0000 |
| Nhiều dữ kiện đúng | 4 | 0.5000 |
| Nhiều mốc khác quan hệ | 2 | 0.0000 |
| Nhân vật trong câu đầy đủ | 4 | 1.0000 |
| Nhầm địa điểm | 1 | 1.0000 |
| Nội dung thêm ngoài nguồn | 2 | 0.0000 |
| Phủ định phức tạp | 1 | 0.0000 |
| Phủ định đơn | 2 | 0.5000 |
| Sai ngày cùng năm | 2 | 1.0000 |
| Suy luận ngoài phạm vi | 1 | 0.0000 |
| Sự kiện ngoài kho | 2 | 0.0000 |
| Thiếu dữ kiện để đối chiếu | 1 | 0.0000 |
| Thu hồi bằng chứng | 2 | 0.0000 |
| Tiền đề câu hỏi sai | 2 | 0.0000 |
| Đúng một phần | 6 | 0.6667 |
| Đồng tham chiếu lược chủ ngữ | 1 | 0.0000 |
| Đổi vai trò trong câu | 1 | 0.0000 |
| Độ chi tiết thời gian | 2 | 0.5000 |

Chỉ số từng nhãn:

```json
{
  "supported": {
    "precision": 0.5384615384615384,
    "recall": 0.4375,
    "f1-score": 0.4827586206896552,
    "support": 16.0
  },
  "contradicted": {
    "precision": 0.42424242424242425,
    "recall": 0.8235294117647058,
    "f1-score": 0.56,
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
[[7, 9, 0, 0], [3, 14, 0, 0], [3, 10, 0, 0], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R001: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R002: chuẩn contradicted, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R004: chuẩn contradicted, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R005: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R007: chuẩn contradicted, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R008: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R009: chuẩn insufficient, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R010: chuẩn insufficient, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R011: chuẩn insufficient, dự đoán supported. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R013: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R014: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R015: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R018: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R022: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R023: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R024: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R029: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R031: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R033: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R037: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R041: chuẩn supported, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R043: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R044: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R045: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
- R046: chuẩn insufficient, dự đoán contradicted. Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.
## rules_single_v1: theo nhóm

| Nhóm | Số ca | Accuracy |
|---|---:|---:|
| Câu sự kiện đầy đủ | 5 | 0.8000 |
| Hoán đổi mốc giữa quan hệ | 2 | 0.0000 |
| Hoán đổi địa phương | 2 | 1.0000 |
| Không xác định dữ kiện | 1 | 0.0000 |
| Nhiều dữ kiện đúng | 4 | 0.0000 |
| Nhiều mốc khác quan hệ | 2 | 0.0000 |
| Nhân vật trong câu đầy đủ | 4 | 1.0000 |
| Nhầm địa điểm | 1 | 0.0000 |
| Nội dung thêm ngoài nguồn | 2 | 0.0000 |
| Phủ định phức tạp | 1 | 0.0000 |
| Phủ định đơn | 2 | 0.0000 |
| Sai ngày cùng năm | 2 | 1.0000 |
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
    "precision": 0.8571428571428571,
    "recall": 0.375,
    "f1-score": 0.5217391304347826,
    "support": 16.0
  },
  "contradicted": {
    "precision": 1.0,
    "recall": 0.35294117647058826,
    "f1-score": 0.5217391304347826,
    "support": 17.0
  },
  "insufficient": {
    "precision": 0.3333333333333333,
    "recall": 0.07692307692307693,
    "f1-score": 0.125,
    "support": 13.0
  }
}
```

Ma trận (hàng chuẩn/cột dự đoán, thứ tự supported, contradicted, insufficient, undetermined):

```json
[[6, 0, 1, 9], [0, 6, 1, 10], [1, 0, 1, 11], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R001: chuẩn supported, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R002: chuẩn contradicted, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R003: chuẩn contradicted, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R004: chuẩn contradicted, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R005: chuẩn supported, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R006: chuẩn contradicted, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R007: chuẩn contradicted, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R008: chuẩn insufficient, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R009: chuẩn insufficient, dự đoán supported. Tên riêng khớp một cách viết đã kiểm tra trong dữ kiện tham chiếu.
- R010: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R011: chuẩn insufficient, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R012: chuẩn supported, dự đoán insufficient. Chưa nêu đủ ngày, tháng, năm mà câu hỏi yêu cầu.
- R013: chuẩn insufficient, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R014: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R015: chuẩn supported, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R016: chuẩn contradicted, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R017: chuẩn contradicted, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R018: chuẩn supported, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R021: chuẩn supported, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R022: chuẩn insufficient, dự đoán undetermined. Câu hỏi mở hoặc chưa nhận dạng được dữ kiện. Chỉ cung cấp bằng chứng để tự đối chiếu.
- R023: chuẩn insufficient, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R031: chuẩn supported, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R032: chuẩn contradicted, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R035: chuẩn supported, dự đoán undetermined. Có tên phù hợp nhưng còn nội dung chưa được xác minh.
- R036: chuẩn contradicted, dự đoán insufficient. Chưa nhận dạng được tên riêng đủ cụ thể để đối chiếu.
- R037: chuẩn supported, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R038: chuẩn contradicted, dự đoán undetermined. Câu có phủ định, nhiều mệnh đề hoặc vượt phạm vi quy tắc. Cần người kiểm tra quan hệ giữa các dữ kiện.
- R041: chuẩn supported, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
- R042: chuẩn contradicted, dự đoán undetermined. Tìm thấy mốc thời gian nhưng câu trả lời còn nội dung ngoài phạm vi đối chiếu.
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
| Đồng tham chiếu lược chủ ngữ | 1 | 0.0000 |
| Đổi vai trò trong câu | 1 | 0.0000 |
| Độ chi tiết thời gian | 2 | 1.0000 |

Chỉ số từng nhãn:

```json
{
  "supported": {
    "precision": 0.75,
    "recall": 0.9375,
    "f1-score": 0.8333333333333334,
    "support": 16.0
  },
  "contradicted": {
    "precision": 0.9411764705882353,
    "recall": 0.9411764705882353,
    "f1-score": 0.9411764705882353,
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
[[15, 1, 0, 0], [0, 16, 1, 0], [5, 0, 8, 0], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R007: chuẩn contradicted, dự đoán insufficient. Chưa có đủ mệnh đề có thể đối chiếu với nguồn đã xác minh.
- R008: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 2 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R009: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 1 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R010: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 1 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R011: chuẩn insufficient, dự đoán supported. Có bằng chứng hỗ trợ 3 mệnh đề được nhận dạng và không phát hiện phần vượt phạm vi bộ quy tắc.
- R018: chuẩn supported, dự đoán contradicted. Phát hiện ít nhất một mệnh đề có giá trị hoặc phủ định trái với bằng chứng. Xem từng mệnh đề bên dưới.
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
    "precision": 0.9411764705882353,
    "recall": 0.9411764705882353,
    "f1-score": 0.9411764705882353,
    "support": 17.0
  },
  "insufficient": {
    "precision": 1.0,
    "recall": 0.8461538461538461,
    "f1-score": 0.9166666666666666,
    "support": 13.0
  }
}
```

Ma trận (hàng chuẩn/cột dự đoán, thứ tự supported, contradicted, insufficient, undetermined):

```json
[[15, 1, 0, 0], [0, 16, 0, 1], [0, 0, 11, 2], [0, 0, 0, 0]]
```

### Các ca sai hoặc từ chối

- R007: chuẩn contradicted, dự đoán undetermined. Có phần chưa thể xử lý tự động; các mệnh đề đã kiểm tra được liệt kê riêng.
- R009: chuẩn insufficient, dự đoán undetermined. Cần kiểm tra tiền đề câu hỏi trước khi đối chiếu câu trả lời.
- R010: chuẩn insufficient, dự đoán undetermined. Cần kiểm tra tiền đề câu hỏi trước khi đối chiếu câu trả lời.
- R018: chuẩn supported, dự đoán contradicted. Phát hiện ít nhất một mệnh đề có giá trị hoặc phủ định trái với bằng chứng. Xem từng mệnh đề bên dưới.

## Giới hạn diễn giải

Bộ thử thách được tạo sau đóng băng mã nhưng cùng trợ lý thiết kế cả mã và dữ liệu; không phải đánh giá mù hoặc độc lập. V1 evaluation đã xem nên chỉ làm hồi quy. Nguồn và nhãn cần người thật thẩm định.
Đây là kho đóng và ngữ pháp hữu hạn, chưa giải quyết mọi câu trả lời AI, mọi phép phủ định hoặc vai trò ngữ nghĩa. Không báo kết quả của người gán nhãn hay thử nghiệm học sinh khi chưa có dữ liệu thật.
Mã còn khớp bản đóng băng tại lúc đo: True.
