# Giới hạn và hướng phát triển

## Giới hạn hiện tại

1. Kho chỉ có 33 dữ kiện thuộc một số sự kiện 1911–1954; không đại diện toàn bộ Lịch sử THPT.
2. Nguồn đã được mở/đối chiếu bởi trợ lý, chưa có giáo viên thẩm định. Nguồn chính thức vẫn có thể có lỗi đánh máy; đã phát hiện chú thích ‘2945’ ở S02 và dùng phần văn xuôi 1945 có ngữ cảnh.
3. Dữ liệu trả lời và nhãn do trợ lý tự xây dựng từ dữ kiện; chưa có gán nhãn độc lập, độ đồng thuận hoặc câu trả lời thu thực tế từ LLM/học sinh. Điểm cao trên tập tổng hợp không bảo đảm ứng dụng ngoài thực tế.
4. Câu hỏi được nhận diện bằng kiểu và neo từ vựng. Không có parser quan hệ/chủ thể tổng quát; câu hỏi đổi tiền đề, đảo quan hệ hoặc diễn đạt mới có thể chưa được xử lý đúng. Người dùng cần đặt câu hỏi ngắn, chính xác và đọc lại nguồn.
5. Câu trả lời chỉ kiểm tra một thuộc tính được hỏi. Chưa tự tách mọi mệnh đề; phủ định, nhiều thời điểm, lập luận và suy diễn thường bị từ chối. Không công bố ‘toàn bộ câu trả lời đã đúng’.
6. Tên riêng phụ thuộc aliases và danh sách trong kho. Địa danh lịch sử, thay đổi tên hành chính, đồng danh hoặc tên ngoài danh sách có thể không nhận diện được.
7. TF-IDF là truy xuất từ vựng, có thể bỏ sót từ đồng nghĩa hoặc đưa đoạn liên quan hời hợt. Điểm tương đồng không chứng minh sự thật.
8. Baseline không có nhãn mâu thuẫn nên là đối chứng yếu. Chênh lệch không chứng minh vượt mọi hệ thống khác. Chưa có ablation tách đóng góp truy xuất, chuẩn hóa và quy tắc.
9. PDF chỉ trích văn bản, chưa OCR; trang không có text trong PDF hỗn hợp có thể bị bỏ qua. Cần kiểm tra đủ nội dung trước khi dùng. Giới hạn 5 MB và 100 trang.
10. Uploads chưa xác minh chỉ dùng tìm đoạn; chưa có giao diện thẩm định/chỉnh sửa trực tiếp facts.csv. Thêm đáp án chuẩn cần sửa file theo hướng dẫn và kiểm thử lại.
11. SQLite và tệp JSON phục vụ một máy; chưa có đăng nhập, mã hóa, chia sẻ nhóm, quản trị phiên bản dữ kiện hay dịch vụ Internet công cộng.
12. Chưa có bằng chứng cải thiện tư duy phản biện, điểm học tập hoặc giảm tin sai của học sinh; các tác động này cần nghiên cứu có người tham gia.

## Những phần chủ động chưa tích hợp

LLM sinh văn bản, mô hình Transformer/NLI, GPU, API trả phí, OCR, quét web tự động trong ứng dụng, ứng dụng .exe độc lập, đăng nhập và triển khai cloud. Chúng không cần cho bản trình diễn offline và không được mô tả là đã hoàn thành.

## Hướng phát triển có thể kiểm tra

- Giáo viên kiểm tra nguồn và cùng người gán nhãn thứ hai chuẩn hóa nhãn, đo độ đồng thuận.
- Xây tập đánh giá mới, câu hỏi được diễn đạt độc lập, có nhiều nguồn và nhiều kiểu sai.
- Thêm baseline mạnh hơn, tách thử nghiệm từng thành phần và đo truy xuất riêng.
- Kiểm tra tiền đề câu hỏi, trích quan hệ và nhiều mệnh đề; chỉ dùng mô hình mới khi đo được lợi ích trên tập chưa xem.
- Nghiên cứu người dùng có thiết kế/đồng ý phù hợp, đánh giá khả năng trích nguồn và tự kiểm chứng thay vì chỉ khảo sát mức hài lòng.
