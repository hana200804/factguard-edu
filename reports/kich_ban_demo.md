# Kịch bản demo khoảng 5–7 phút

Mở ứng dụng trước buổi thi, đọc README và kiểm tra đủ thư viện. Sau khi đã cài, có thể ngắt mạng để chứng minh kiểm chứng không cần API; nút mở URL nguồn cần mạng. Các câu trả lời dưới đây là ví dụ tự dựng, không nói rằng đã được ChatGPT tạo thực sự.

## 1. Vấn đề và phạm vi

“Chúng em xây công cụ hỗ trợ học sinh đối chiếu dữ kiện lịch sử trong câu trả lời AI với một kho có nguồn. Bản hiện tại tập trung ngày tháng, nhân vật, địa điểm. Kho còn nhỏ; đây không phải máy quyết định đúng sai cho mọi câu hỏi lịch sử.”

Mở Tổng quan, giới thiệu số dữ kiện và nguồn. Bộ đếm lượt sử dụng là SQLite thực tế; đừng nói đó là số người dùng hay học sinh tham gia nghiên cứu.

## 2. Câu trả lời đúng

Chọn Kiểm chứng → “Mốc thời gian đúng”.

- Câu hỏi: Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?
- Trả lời: Ngày 2 tháng 9 năm 1945.
- Bấm Kiểm chứng. Dự kiến: Có bằng chứng hỗ trợ.

Chỉ ra cách chuẩn hóa, dữ kiện F001, đoạn tóm lược, vị trí mở đầu và URL Bảo tàng Thành phố Hồ Chí Minh. Nói rõ tóm lược không phải lời trích nguyên văn.

## 3. Câu trả lời sai

Chọn “Mốc thời gian sai”: Chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1955.

Bấm Kiểm chứng. Dự kiến: mâu thuẫn với bằng chứng ngày 7/5/1954. Đây là sai mốc có thể xác minh trong kho, không phải phán đoán từ điểm tương đồng.

## 4. Thiếu bằng chứng và từ chối

Chọn “Chưa đủ thông tin”: đáp án chỉ có năm 1945 khi câu hỏi hỏi ngày. Dự kiến: Chưa đủ bằng chứng.

Chọn “Câu hỏi ngoài kho” hoặc “Câu hỏi cần tự phân tích”. Giải thích ngoài kho không đồng nghĩa thông tin sai; câu hỏi mở cần người phân tích và đọc nguồn.

## 5. Hai phương pháp

Mở So sánh phương pháp, chọn câu F001 và nhập “Không phải ngày 2/9/1945.”. Baseline khớp từ v1 có thể báo supported; bộ kiểm chứng mệnh đề v2 nhận mâu thuẫn từ phủ định đơn trên ngày đúng. Phủ định tác động nhiều quan hệ vẫn có thể bị từ chối.

## 6. Chạy thực nghiệm thật

Mở Thực nghiệm → Tập đánh giá → Chạy thực nghiệm. Chờ bảng/biểu đồ sinh từ code. Chỉ vào Accuracy, F1 macro, ma trận và danh sách lỗi. Nêu số ca, dữ liệu tổng hợp, baseline yếu, chưa gán nhãn độc lập. Đọc số từ lần chạy trên màn hình, không đọc một con số ghi nhớ nếu dữ liệu đã đổi.

Xuất CSV và Markdown. Cho thấy các ca undetermined vẫn tính sai so với ba nhãn chuẩn và tỷ lệ từ chối được báo riêng. Không gọi điểm này là “độ tin cậy 93%” của một câu trả lời.

## 7. Kho và kết thúc

Mở một nguồn, tìm dữ kiện bằng từ khóa. Nếu thử tải tài liệu, dùng TXT của nhóm được phép sử dụng. Chỉ ra nhãn chưa xác minh; PDF scan phải báo chưa có OCR.

“Đóng góp thực tế của bản hiện tại là một quy trình có thể đọc lại căn cứ và đo lại kết quả. Bước tiếp theo cần giáo viên rà soát dữ liệu, bổ sung tập độc lập và thực nghiệm học sinh trước khi kết luận hiệu quả giáo dục.”

## Phần trình diễn nghiên cứu v2

1. Chọn tình huống ‘Đúng ngày nhưng sai nhân vật’. Chỉ ra ba check riêng: ngày/địa điểm được hỗ trợ, nhân vật mâu thuẫn. Chỉ vào vị trí tô màu trên câu nguyên bản.
2. Chọn ‘Tiền đề câu hỏi sai’: tên người trả lời đúng không làm địa điểm Sao Hỏa trong câu hỏi trở thành đúng.
3. Mở Phòng nghiên cứu → Chạy nghiên cứu bốn phương pháp. Phân biệt baseline ba nhãn với khớp từ v1, và bản bỏ chốt với bản đầy đủ.
4. Chỉ ra số hỗ trợ sai, mức bao phủ/rủi ro và bốn ca chưa đạt chuẩn. Không dùng 0 lỗi quan sát được để khẳng định an toàn tuyệt đối.
5. Nói rõ bộ tổng hợp do cùng tác giả tạo; phân tích dạng câu hỏi là hậu nghiệm. Cho xem mã/hash đóng băng và dữ liệu gốc.
6. Nếu có tài liệu được phép dùng và đã đọc, trình diễn lập nháp → duyệt → kiểm chứng → thu hồi. Người thực hiện phải thực sự đọc và chịu trách nhiệm; không nhấp xác nhận như bước trang trí.
7. Phiếu gán nhãn ban đầu trống. Giới thiệu cách thu thập ca thật và hai người gán nhãn, không tạo nhãn/người tham gia giả trong buổi thuyết trình.
