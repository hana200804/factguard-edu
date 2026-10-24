# 15 câu hỏi phản biện dự kiến

## 1. Điểm mới của đề tài ở đâu?

Bản v2 trích một số mệnh đề theo quan hệ, gắn vị trí ký tự và bằng chứng, giữ phần chưa xác minh và quản lý nguồn có duyệt/thu hồi. Có ablation và đo lỗi hỗ trợ sai. Các kỹ thuật nền đều có sẵn; đóng góp là thiết kế/tích hợp và thực nghiệm trong phạm vi kho lịch sử Việt Nam, chưa khẳng định thuật toán mới hay sản phẩm đầu tiên.

## 2. Khác với hỏi ChatGPT ‘câu này đúng không’ thế nào?

Phần mềm kiểm tra trên một kho cụ thể, hiển thị dữ kiện và vị trí nguồn để người học đọc lại. Không sinh lời giải thích bằng LLM. ChatGPT có khả năng rộng hơn; không có thực nghiệm trong dự án này chứng minh FactGuard tốt hơn ChatGPT.

## 3. Độ chính xác là bao nhiêu?

Đọc số mới nhất ở Phòng nghiên cứu và reports/research_v2/latest.json. V2 đầy đủ chốt đạt 42/46 ca tổng hợp trong lần đo được lưu, còn v1 có bộ 87 ca riêng. Không so hai phần trăm như cùng tập dữ liệu và không diễn giải là xác suất đúng của một câu bất kỳ.

## 4. Dữ liệu lấy ở đâu?

33 dữ kiện đối chiếu từ 7 trang của bảo tàng và cổng thông tin chính thức; URL, vị trí và ngày đối chiếu nằm trong dữ liệu. Nội dung offline là tóm lược tự biên soạn. Chưa có thẩm định độc lập của giáo viên, cần bổ sung trước khi dùng trong hồ sơ dự thi.

## 5. ‘Nguồn chính thức’ có bảo đảm luôn đúng không?

Không. Nguồn có thể có lỗi đánh máy hoặc cần xem ngữ cảnh. Ví dụ trang S02 có chú thích ảnh ‘2945’, trong khi đề mục và văn xuôi là 1945. Dự án ghi lại cách chọn phần bằng chứng và giữ URL để kiểm tra, không coi uy tín nguồn là bảo đảm tuyệt đối.

## 6. Có dùng điểm tương đồng làm độ tin cậy không?

Không. TF-IDF/cosine chỉ xếp hạng đoạn. Kết luận dữ kiện dùng giá trị ngày hoặc tên được đối chiếu với bản ghi đã có nguồn. Không hiển thị phần trăm tin cậy cho từng câu.

## 7. Vì sao không có LLM trong sản phẩm kiểm chứng AI?

Đầu vào là câu trả lời từ một AI bất kỳ hoặc văn bản tự nhập. Nhiệm vụ là kiểm chứng, không cần sinh câu trả lời. Luồng offline đáp ứng yêu cầu miễn phí, CPU và minh bạch. Tích hợp LLM là hướng tương lai và chưa được triển khai.

## 8. Khi có ngày đúng nhưng phần khác sai thì sao?

V2 có thể kiểm tra riêng nhân vật, ngày và địa điểm trong một mẫu quan hệ. Chỉ một giá trị sai đủ làm kết quả chung báo mâu thuẫn, trong khi các giá trị đúng vẫn hiện riêng. Nội dung không gắn được với mẫu phải báo chưa xác minh. Chưa đủ khả năng hiểu mọi quan hệ để bảo đảm toàn đoạn đúng.

## 9. ‘Chưa đủ bằng chứng’ có nghĩa thông tin sai không?

Không. Có thể kho thiếu sự kiện, câu trả lời thiếu chi tiết hoặc tên chưa có trong danh sách. Nhãn mâu thuẫn chỉ dùng khi nhận diện được một giá trị xác định khác đáp án của dữ kiện.

## 10. Vì sao có bốn đầu ra nhưng chỉ ba nhãn chuẩn?

Ba nhãn chuẩn mô tả nội dung so với kho. Undetermined mô tả việc thuật toán không đủ năng lực kết luận. Đầu ra này tính sai trong accuracy, báo thêm tỷ lệ riêng. Như vậy từ chối không bị đổi thành thành tích đúng nhãn.

## 11. Baseline có công bằng không?

V2 có đối chứng Logistic Regression đủ ba nhãn chỉ fit development, cùng kho và cùng ca thử thách. Có thêm bản bỏ nhóm chốt để phân tích tác dụng của nhóm đó. Tuy nhiên tập fit chỉ 24 ca tổng hợp, chưa là đối chứng NLI/LLM mạnh. Dạng câu hỏi làm thay đổi điểm đối chứng; phép đo hậu nghiệm đã công khai riêng.

## 12. Tập kiểm thử có bị ‘học thuộc’ không?

Không huấn luyện mô hình phân loại và không chỉnh ngưỡng theo evaluation. Tách development/evaluation theo sự kiện; quy tắc/ngưỡng được ghi trong protocol. Nhưng đáp án sự kiện đánh giá nằm sẵn trong kho tham chiếu, vì đây là bài toán tra/đối chiếu kho đóng. Chưa đánh giá khả năng khái quát sang sự kiện không có trong kho.

## 13. Ai tạo nhãn và có thiên lệch không?

Trợ lý tạo 111 ca v1 và 46 ca v2 cùng nhãn có chủ đích. Đây là thiên lệch cùng tác giả đáng kể. V2 có công cụ thu thập và phiếu ẩn kết quả cho người thật, nhưng chưa có thẩm định người dùng tại lúc bàn giao. Bootstrap theo sự kiện chỉ có tính thăm dò và không thay thế một bộ độc lập.

## 14. Có chứng minh học sinh học tốt hơn không?

Chưa. Dự án hiện chứng minh phần mềm chạy được và đo kết quả đối chiếu trên bộ nhỏ. Muốn kết luận tác động học tập cần thiết kế thử nghiệm người dùng phù hợp, đo kỹ năng đọc nguồn và tư duy phản biện thực tế, thu dữ liệu có đồng ý và bảo vệ riêng tư.

## 15. Tác động thực tế và bước tiếp theo là gì?

Có thể dùng để thực hành thao tác hỏi dữ kiện, đọc bằng chứng và nhận ra giới hạn của tự động hóa. Ưu tiên tiếp theo: giáo viên kiểm tra nguồn/nhãn, mở rộng kho, tập đánh giá độc lập, baseline mạnh hơn và kiểm tra nhiều mệnh đề. Không nên đưa bản này làm công cụ chấm đúng/sai duy nhất cho học sinh.
