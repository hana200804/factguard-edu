# Đề cương nghiên cứu

**Bổ sung phiên bản nghiên cứu v2:** bộ kiểm chứng nhiều mệnh đề theo quan hệ, quản lý nguồn có thẩm định và phòng thực nghiệm bốn cấu hình đã được triển khai. Thiết kế, bộ thử thách, đối chứng ba nhãn, ablation và giới hạn có tại [nghien_cuu_v2.md](nghien_cuu_v2.md). Bộ v1 dưới đây được giữ làm cơ sở/hồi quy; không thay kết quả v1 bằng v2.

## Tên đề tài

FactGuard EDU – Nghiên cứu phương pháp kiểm chứng thông tin trong câu trả lời của AI tạo sinh dựa trên bằng chứng phục vụ học tập môn Lịch sử THPT.

Người thực hiện, trường, lớp, giáo viên hướng dẫn: **học sinh điền thông tin thật**. Ngày hoàn thiện bản phần mềm này: 24/10/2026. Hạn 25/10/2026 là mốc do người dùng cung cấp, chưa được đối chiếu với thông báo của ban tổ chức.

## Tính cấp thiết

Câu trả lời trôi chảy không tự chứng minh tính đúng. Với câu hỏi lịch sử có ngày tháng hoặc tên riêng, người học cần xem dữ kiện tham chiếu và nguồn. Dự án xây một công cụ hỗ trợ thao tác đó trên kho nhỏ; chưa tiến hành khảo sát để định lượng mức phổ biến của lỗi AI hay nhu cầu của học sinh.

## Câu hỏi nghiên cứu

Việc sử dụng dữ liệu tham chiếu có nguồn và cơ chế nhận diện thông tin chưa đủ bằng chứng có cải thiện khả năng kiểm chứng so với so khớp từ đơn giản trên bộ kiểm thử được xây dựng hay không?

## Giả thuyết

Trên các câu hỏi dữ kiện đơn thuộc kho, chuẩn hóa ngày/tên và quy tắc đối chiếu có thể phát hiện lỗi thay mốc hoặc tên tốt hơn baseline khớp từ. Câu phức tạp có thể làm tỷ lệ từ chối tăng. Đây là giả thuyết cần kiểm tra, không mặc định đúng trên mọi câu trả lời AI.

## Mục tiêu và phạm vi

- Tạo ứng dụng Windows dễ trình diễn, chạy CPU/offline sau cài đặt.
- Truy xuất đoạn liên quan và hiển thị nguồn rõ ràng.
- Đối chiếu các ngày/năm, nhân vật và địa điểm có đáp án đã kiểm tra.
- Không đồng nhất tương đồng từ với độ đúng; công khai việc chưa thể tự kết luận.
- Đo kết quả bằng chương trình trên dữ liệu có nhãn và công bố các ca thất bại.

Kho khởi tạo gồm 33 dữ kiện Lịch sử Việt Nam 1911–1954. Phạm vi hẹp hơn toàn bộ chương trình THPT. Không giải quyết câu hỏi đánh giá nhân vật, quan hệ nhân quả hoặc tranh luận sử học.

## Phương pháp

Đọc/đối chiếu nguồn chính thức, xây dựng dữ kiện có cấu trúc, truy xuất TF-IDF, đối chiếu quy tắc và thực nghiệm so sánh. Câu trả lời/nhãn là dữ liệu tổng hợp xây dựng có chủ đích. Chưa thu dữ liệu cá nhân, chưa thực hiện nghiên cứu có người tham gia.

## Thiết kế thực nghiệm

Tập phát triển 24 ca, tập đánh giá 87 ca; tách event_id. Kho tham chiếu là nguồn thông tin được phép sử dụng bởi cả hai phương pháp. Cùng một ca được đưa qua baseline và proposed. Có ba nhãn chuẩn: supported, contradicted, insufficient. Đầu ra undetermined được tính sai so với nhãn chuẩn, đồng thời báo riêng tỷ lệ từ chối. Chỉ số: Accuracy, Precision/Recall/F1 theo nhãn và macro, confusion matrix, thời gian xử lý.

Quy tắc/ngưỡng phải được quyết định trước khi dùng kết quả tập đánh giá. Khi phát triển phiên bản mới, tạo một tập đánh giá độc lập mới; không sửa dữ liệu để tăng điểm. Chưa có người gán nhãn thứ hai, chưa đo độ đồng thuận liên đánh giá.

## Kết quả và ứng dụng

Phần mềm và số liệu đo thực tế có trong báo cáo kỹ thuật và reports/experiment. Chênh lệch điểm trên bộ tổng hợp chỉ gợi ý tính khả thi, chưa chứng minh cải thiện năng lực học tập hay tính đúng trên câu trả lời AI ngoài thực tế. Ứng dụng có thể phục vụ buổi thực hành đọc nguồn, dưới hướng dẫn của giáo viên.

## Công việc nghiên cứu tiếp

Giáo viên kiểm tra nguồn và nhãn; bổ sung câu hỏi/đáp án từ nguồn độc lập; nếu tiến hành thử nghiệm học sinh, lập thiết kế nghiên cứu, quy trình đồng ý tham gia và cách bảo vệ dữ liệu phù hợp trước khi thu thập. Chỉ báo cáo những hoạt động và số liệu thực sự đã thực hiện.
