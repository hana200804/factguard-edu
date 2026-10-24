# Bàn giao phiên bản nghiên cứu v2

## Ba module đã triển khai

1. Kiểm chứng mệnh đề theo quan hệ: giá trị, vị trí ký tự, nguồn, kết luận riêng và phần chưa xử lý.
2. Quản lý nguồn có thẩm định: nháp, duyệt, từ chối, thu hồi, lịch sử và hash; người duyệt tự khai.
3. Phòng nghiên cứu: bốn phương pháp, ablation, chỉ số theo giai đoạn, lặp lại, phiếu ẩn kết quả và ca người dùng tách riêng.

## Kết quả chính đo trên 46 ca tổng hợp

| Phương pháp | Đúng / 46 | Accuracy | Hỗ trợ sai / 30 ca không được hỗ trợ |
|---|---:|---:|---:|
| lexical_3way | 17 | 0.3696 | 2 |
| rules_single_v1 | 1 | 0.0217 | 1 |
| claims_no_guard | 40 | 0.8696 | 5 |
| claims_guarded | 42 | 0.9130 | 0 |

104 kiểm thử đạt; coverage 90.76%. Mã lõi khớp đóng băng: True.
Kết quả tổng hợp cùng tác giả không chứng minh hiệu quả ngoài thực tế. Giữ bốn ca chưa đạt, phân tích dạng câu hỏi là hậu nghiệm và lưu riêng.
Chưa có nhãn/ca người dùng thật nếu các bộ đếm trong verification.json còn 0. Công cụ thu thập đã hoạt động nhưng không thay dữ liệu người dùng thực.

## Mở và chạy

```powershell
cd D:\KHKT\factguard-edu
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở http://127.0.0.1:8501. Các ví dụ mới ở Kiểm chứng; phép đo ở Phòng nghiên cứu; duyệt nguồn ở Kho kiến thức → Thẩm định dữ kiện.
