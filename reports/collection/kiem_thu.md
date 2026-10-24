# Kiểm thử bộ thu thập và giao diện CSV

Thời điểm chạy: 2026-10-24T10:48:52+00:00. Python 3.12.10, Streamlit 1.66.1, Windows.

## Kết quả đo

- **157/157 test đạt**, không lỗi hoặc bỏ qua; gồm 47 ca test module/bộ lệnh thu thập và 6 AppTest mới cho CSV.
- Coverage toàn bộ src: **91.18%**. Đây là độ bao phủ mã khi kiểm thử, không phải độ chính xác kiểm chứng lịch sử.
- Ruff sạch; Pyright 0 lỗi/0 cảnh báo; compileall đạt.
- validate_freeze() = True; không sửa bộ kiểm chứng, dữ kiện hay giao thức nghiên cứu đã đóng băng.
- src/collection.py, hai script và hai CSV được cung cấp giữ nguyên byte. Cơ sở dữ liệu runtime thật cũng giữ nguyên byte sau thử nghiệm.

## Phạm vi kiểm tra

CSV UTF-8/BOM, dấu phẩy/chấm phẩy và ô nhiều dòng; mã câu hỏi, sự kiện, metadata, ngày tháng và mẫu lỗi Excel; bảo vệ tệp đã điền; nhập không nhãn, chống trùng và nhật ký. CLI dry-run và tệp có một dòng lỗi được chạy trong runtime tạm.

AppTest tải CSV trực tiếp: xem trước ẩn xuất xứ, chỉ nhập sau nút bấm, nhập lại bỏ qua trùng; thay tệp hợp lệ bằng tệp lỗi không nhập cache cũ; chặn tệp lỗi/toàn trống/quá 5 MB/mã hóa sai; lỗi ghi nhật ký thông báo đúng rằng ca đã được xử lý. AppTest không thay thế kiểm tra hình ảnh trong trình duyệt.

Mọi câu trả lời và người thu thập trong test là dữ liệu kiểm thử phần mềm, không tính thành dữ liệu nghiên cứu. Mẫu gốc vẫn có 100 dòng chưa điền, từ 50 câu do trợ lý soạn. Không tạo nhãn hoặc người tham gia giả.

## Bằng chứng và tái lập

[verification.json](verification.json) lưu lệnh, môi trường và SHA-256 nguồn; [pytest.xml](pytest.xml) lưu kết quả từng test; [coverage.json](coverage.json) lưu coverage chi tiết. Chạy các lệnh trong verification.json từ thư mục dự án.

Báo cáo này bổ sung kiểm thử tính năng thu thập; các kết quả nghiên cứu v1/v2 cũ giữ nguyên. Xem [hướng dẫn thu thập](../huong_dan_thu_thap.md) để lấy dữ liệu thật. Quy tắc kiểm tra toàn bộ trước nhập không phải cam kết hoàn tác mọi lỗi hệ thống giữa quá trình ghi SQLite.
