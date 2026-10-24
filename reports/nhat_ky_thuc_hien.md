# Nhật ký thực hiện và mẫu nhật ký học sinh

## Ghi nhận thực sự trong phiên xây dựng 24/10/2026

Các mục dưới đây là hoạt động do trợ lý lập trình thực hiện trong phiên này, không phải nhật ký nghiên cứu nhiều tháng của học sinh:

- Đọc tài liệu yêu cầu người dùng và kiểm tra thư mục D:\KHKT ban đầu chưa có dự án.
- Đọc các skill coding-standards, frontend-design, verification-loop; triển khai Python/Streamlit.
- Mở và đối chiếu 7 trang nguồn lịch sử, biên soạn tóm lược và dữ kiện có cấu trúc. Một số URL tìm được không mở thành công đã không đưa vào danh mục nguồn.
- Tạo/cài môi trường Python 3.12, thư viện, core xử lý, sáu trang, dữ liệu tổng hợp và kiểm thử.
- Lần chạy pytest đầu vướng quyền Temp trong sandbox; sau khi được cấp quyền, chạy lại. Một kiểm thử phát hiện ‘vị’ bị đồng nhất với từ nối ‘vì’ khi bỏ dấu; sửa nhận diện câu phức tạp theo unit test. Không điều chỉnh ngưỡng để tăng điểm evaluation.
- Chạy development và evaluation bằng chương trình thật, lưu CSV/JSON/Markdown. Mọi ca từ chối vẫn được tính sai so với nhãn chuẩn.
- Khởi động Streamlit trên 127.0.0.1:8501; endpoint health phản hồi 200/ok. Công cụ trình duyệt từ chối quyền mở localhost, nên chưa thực hiện kiểm tra trực quan/ảnh chụp bằng trình duyệt. Các luồng ứng dụng được kiểm tra bằng Streamlit AppTest.
- Viết tài liệu kỹ thuật, kịch bản demo, câu hỏi phản biện, hướng dẫn và đóng gói source. Kết quả cổng kiểm thử cuối được ghi tại kiem_thu.md; không suy diễn kết quả trước khi chạy.

## Mẫu để học sinh tự ghi

### Nâng cấp nghiên cứu v2 trong cùng ngày 24/10/2026

- Theo yêu cầu người dùng, đã bổ sung kiểm chứng từng mệnh đề theo quan hệ, dấu vết ký tự, chốt tiền đề/vai trò/phần dư và kiểm tra nguồn xung đột.
- Bổ sung luồng nguồn có nháp, người dùng tự khai duyệt/từ chối/thu hồi, phiên bản và nhật ký hash cục bộ; kiểm thử luồng này bằng AppTest với fixture tạm.
- Lưu bản kết quả v1 trước khi nâng cấp. Đóng băng mã lõi, cấu hình và dữ liệu tham chiếu trước khi tạo 46 ca thử thách v2. Cùng trợ lý tạo mã và ca/nhãn nên không gọi là đánh giá độc lập.
- Chạy bốn cấu hình: từ vựng học ba nhãn trên development, luật một dữ kiện v1, trích mệnh đề bỏ nhóm chốt, trích mệnh đề đủ chốt. Giữ nguyên bốn ca v2 chưa đạt nhãn chuẩn sau khi xem điểm.
- Chạy phân tích hậu nghiệm về dạng câu hỏi do phát hiện khác dạng câu hỏi ở tập fit; lưu riêng, không thay kết quả chính hay gọi là một tập độc lập.
- Bổ sung phiếu ẩn kết quả, hiển thị đúng điều kiện kho bị rút, nhập ca người dùng và gán nhãn/đồng thuận. Không tạo nhãn người dùng hoặc người tham gia giả.
- Kiểm thử phát hiện lỗi chuyển kiểu số khi đọc CSV có ô trống trên giao diện; sửa tại lớp UI, không thay mã lõi đã đóng băng hoặc nhãn thử thách.
- Chạy 104 kiểm thử đạt; lặp hai lượt v2 có 184 dòng dự đoán/dấu vết giống nhau và bootstrap lặp được. Số liệu chi tiết trong research_v2/verification.json và research_v2/pytest.xml.

### Mẫu ghi chép tiếp của học sinh

Chỉ ghi điều đã thực sự làm. Không điền ngày giả hay các buổi khảo sát chưa xảy ra.

| Ngày/giờ thực tế | Người thực hiện | Mục tiêu | Việc đã làm | Bằng chứng/tệp/commit | Vấn đề phát hiện | Kết quả quan sát | Bước tiếp theo |
|---|---|---|---|---|---|---|---|
| [tự điền] | [tự điền] | [tự điền] | [tự điền] | [tự điền] | [tự điền] | [tự điền] | [tự điền] |

## Khi kiểm tra một nguồn

- Tên nguồn/URL; ngày mở thực tế; tác giả/cơ quan và ngày công bố.
- Dữ kiện nào được kiểm tra; đoạn/trang; có chỗ mâu thuẫn hay lỗi đánh máy không.
- Ai đã đọc lại; quyết định giữ/bỏ/sửa và lý do, lưu bản trước/sau.

## Khi chạy thực nghiệm

- Phiên bản dữ liệu, thuật toán, máy và lệnh chạy.
- Tập development hay evaluation; đã xem điểm evaluation này trước đó chưa.
- Tệp kết quả, lỗi và cách giải thích. Nếu đổi thuật toán sau khi xem điểm, ghi rõ và tạo bộ đánh giá mới cho kết luận tiếp theo.
