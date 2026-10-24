# Công việc học sinh cần trực tiếp hoàn tất trước khi nộp

1. Điền đúng tên người thực hiện, trường, lớp, giáo viên hướng dẫn và thông tin hồ sơ. Kiểm tra hạn nộp và biểu mẫu qua ban tổ chức; 25/10/2026 là mốc từ yêu cầu người dùng.
2. Cùng giáo viên mở đủ 7 URL trong sources.md; kiểm tra từng dữ kiện, vị trí, cách viết tên và aliases. Dữ kiện đã được trợ lý đối chiếu trực tuyến, chưa thay thế thao tác thẩm định này.
3. Đọc 111 ca v1 và 46 ca thử thách v2, đặc biệt ngoài kho, phủ định, tiền đề sai và câu có ý thêm. Không gọi dữ liệu tự dựng là câu trả lời do ChatGPT/học sinh cung cấp thực tế.
4. Đọc báo cáo thật, phân biệt 6 ca từ chối của v1 với 4 ca chưa đạt nhãn trong challenge v2; giải thích ablation và giới hạn đối chứng. Không mô tả accuracy tổng hợp là ‘độ tin cậy’ của toàn hệ thống hoặc hiệu quả học tập.
5. Mở giao diện bằng trình duyệt trên máy dự thi, kiểm tra chữ Việt, bố cục, màn hình trình chiếu và thao tác tải tệp. Kiểm tra trực quan bằng trình duyệt chưa thực hiện trong phiên trợ lý vì công cụ bị từ chối quyền mở localhost.
6. Chạy đủ ba ví dụ đúng/sai/thiếu, một câu ngoài kho, một câu phủ định; đọc lại bằng chứng. Thử không có mạng sau khi cài xong thư viện, lưu kết quả chạy trên chính máy thi.
7. Đọc hướng dẫn nguồn gốc/giới hạn, hiểu và có thể giải thích TF-IDF, luật ngày/tên, baseline, confusion matrix và macro F1. Ghi rõ mức hỗ trợ của công cụ AI trong quá trình xây dựng theo quy định cuộc thi.
8. Tự ghi nhật ký hoạt động thực tế tiếp theo; không biến nhật ký trợ lý thành các hoạt động học sinh đã làm từ trước. Chưa có khảo sát hay thực nghiệm học sinh nào được tiến hành trong dự án này.
9. Lưu ZIP source, README, bản báo cáo, CSV kết quả và ảnh chụp demo thực tế của bạn vào nơi dự phòng. Máy khác cần Python và cài dependencies; ZIP không chứa venv.
10. Nếu muốn công bố kết luận khoa học mạnh hơn, cần tập đánh giá mới do giáo viên/người khác xây dựng và nghiên cứu người dùng có thiết kế phù hợp. Không thể thay việc này bằng số liệu tự dựng trước hạn nộp.

## Dữ liệu chưa kiểm chứng

- Dữ kiện khởi tạo chưa đối chiếu URL: **không có** trong danh mục đi kèm.
- Dữ kiện chưa được giáo viên thẩm định độc lập: **toàn bộ 33 dữ kiện**.
- Nhãn chưa có người gán nhãn độc lập: **toàn bộ 111 ca v1 và 46 ca v2** tại thời điểm bàn giao.
- Mọi tài liệu người dùng tải thêm: mặc định **chưa xác minh**, chỉ dùng tìm đoạn. Không đưa vào thống kê hiệu quả như nguồn đã thẩm định.
