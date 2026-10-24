# Dữ liệu FactGuard EDU

Nguồn được mở và đối chiếu ngày 24/10/2026. `verified=true` nghĩa là nội dung đã được trợ lý đối chiếu với trang gốc; chưa có xác nhận của giáo viên. Các file `sources/Sxx.md` là tóm lược tự biên soạn, không phải bản chụp toàn văn hay lời trích nguyên văn. Không đưa tóm lược vào ngoặc kép như một trích dẫn trực tiếp.

## Các file

- `facts.csv`: câu hỏi chuẩn, đáp án, kiểu dữ kiện, giá trị chuẩn hóa, aliases, nhóm neo câu hỏi, bằng chứng tóm lược và vị trí nguồn.
- `sources.json`: URL thật, cơ quan công bố, ngày đăng/ban hành, ngày kiểm tra và cách kiểm tra.
- `evaluation.csv`: cả tập phát triển và tập đánh giá, tách theo event_id.
- `dataset_card.json`: quy mô và nguồn gốc dữ liệu.
- `sources/`: bản tóm lược ngắn, dùng offline.
- `collection/cau_hoi.csv`: 50 câu hỏi do trợ lý soạn, ghi `nguon_cau_hoi = tro_ly`; bảy loại câu hỏi không phải nhãn câu trả lời.
- `collection/mau_ghi_cau_tra_loi.csv`: 100 dòng trống cho 50 câu × ChatGPT/Gemini, chưa có đầu ra chatbot đã thu. Giữ mẫu gốc trống, tạo tệp riêng như `collection/dot1.csv` để điền theo [hướng dẫn thu thập](../reports/huong_dan_thu_thap.md).

Chỉ hai tệp gốc trên trong `collection/` được theo dõi trên Git và đóng gói vào ZIP; mọi tệp khác, kể cả trong thư mục con, bị bỏ qua. Tệp đã điền cần sao lưu riêng; `git add -f` vẫn có thể vượt quy tắc bỏ qua của Git.

## Thêm dữ kiện có thể kiểm chứng

1. Chỉ dùng tài liệu được phép sử dụng. Đọc nguồn gốc và ghi URL, tên tài liệu, ngày kiểm tra.
2. Thêm nguồn vào `sources.json` cùng một file tóm lược trong `sources/`. Nếu chưa đọc được nguồn gốc, để `verified=false`.
3. Thêm một dòng vào `facts.csv` theo các dòng có sẵn. ID và câu hỏi chuẩn phải duy nhất. Loại: date, year, person hoặc place. Ngày canonical: YYYY-MM-DD. Không đưa ngày scan/OCR chưa kiểm tra vào đáp án chuẩn.
4. `aliases` là mảng JSON các cách viết đã rà soát. `anchors` là mảng các nhóm đồng nghĩa; phải khớp ít nhất một cụm trong TỪNG nhóm. Ví dụ `[["điện biên phủ"],["kết thúc","toàn thắng"]]`.
5. Thêm vị trí đoạn/trang cụ thể, tóm lược bằng chứng và kiểm tra thủ công. Chỉ bật verified khi cả nguồn lẫn dữ kiện được đối chiếu.
6. Chạy pytest và ứng dụng. Dữ liệu lỗi/trùng sẽ bị chặn với thông báo rõ. Có thể bấm ‘Tái lập chỉ mục’; chương trình đọc lại kho ở mỗi lần chạy trang.
7. Muốn đánh giá phiên bản mới, đóng băng quy tắc và tạo tập đánh giá độc lập MỚI. Không sửa nhãn/đáp án để tăng điểm sau khi xem kết quả.

## Nhãn kiểm thử

- supported: dữ kiện được hỏi khớp bằng chứng.
- contradicted: có phát biểu xác định trái bằng chứng, gồm thay năm/tên có chủ đích và phủ định đáp án đúng.
- insufficient: thiếu giá trị cần hỏi, ngoài kho hoặc thêm khẳng định không được tài liệu hỗ trợ.
- undetermined chỉ là nhãn đầu ra từ chối của hệ thống; không phải nhãn chuẩn. Tính sai trong accuracy và báo cáo tỷ lệ riêng.

Các đáp án sai chỉ là dữ liệu đối chứng, không phải sự kiện lịch sử. Chưa có dữ liệu câu trả lời thực sự từ học sinh hay AI tạo sinh. Không có dữ kiện khởi tạo chưa kiểm tra nguồn; mọi tài liệu tải thêm mặc định chưa xác minh và không tự trở thành đáp án chuẩn.
