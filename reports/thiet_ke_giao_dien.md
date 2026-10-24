# Thiết kế giao diện

## Phương án được chọn trước khi xây giao diện

Đối tượng: học sinh THPT và giáo viên/giám khảo đọc bằng chứng khi trình diễn. Công việc chính: nhập một dữ kiện, đọc kết luận và mở lại căn cứ.

| Thành phần | Giá trị | Vai trò |
|---|---|---|
| Navy | #102B50 | Điều hướng, tiêu đề |
| Xanh dương | #2158B0 | Nút hành động chính, phương pháp đề xuất |
| Nền | #F7F9FD | Nền nội dung |
| Trắng | #FFFFFF | Khu nhập và đọc căn cứ |
| Xanh xám | #94A8C7 | Baseline |
| Chữ phụ | #50627B | Chú thích, dữ liệu bổ sung |

Typography: Segoe UI, dự phòng Tahoma/Arial, có sẵn trên Windows và hỗ trợ tiếng Việt, không tải font mạng. Tiêu đề rõ, thân bài khoảng cách dòng rộng. Căn trái; không animation.

```text
Sidebar navy     Nội dung sáng
                Tiêu đề + phạm vi
6 trang         [Câu hỏi / trả lời] [Kết luận + giá trị chuẩn]
                [Nút kiểm chứng]   [Đoạn bằng chứng + nguồn]
Trạng thái       [Lịch sử / xuất kết quả]
offline
```

Tổng quan có một biểu trưng khiên/check nhẹ bằng SVG và lời mời đọc nguồn; không dùng ảnh mạng. Khối đếm là dữ liệu thật từ CSV/SQLite, không số minh họa. Trang kiểm chứng ưu tiên input và bằng chứng cạnh nhau, thu gọn trên màn hình hẹp. Nút/focus và thông báo có chữ mô tả, không chỉ phụ thuộc màu. Không thêm thành phần trang trí chuyển động.

## Rà soát so với đề bài

Giữ nền sáng, navy/xanh, sidebar và bảng/biểu đồ rõ. Tránh thẻ trang trí giống nhau cho mọi đoạn, không đưa số phần trăm ‘tin cậy’ vào kết luận. Tình huống demo ghi rõ là ví dụ. Chỉ thông báo sẵn sàng offline sau khi chương trình đã cài được dependencies, dữ liệu có sẵn.

Luồng sáu trang được kiểm tra bằng AppTest. Chưa có ảnh chụp giao diện thực tế vì cổng quyền công cụ trình duyệt từ chối mở localhost; học sinh cần kiểm tra màn hình trình chiếu trước khi thi.
