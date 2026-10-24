# Hướng dẫn thu thập và gán nhãn bằng dữ liệu thật

## Phạm vi nhiệm vụ

Nhãn mô tả câu trả lời so với **kho tham chiếu khả dụng trong ca đó**, không phải kiến thức mọi nơi trên Internet. Một thông tin đúng ngoài thực tế vẫn có thể thiếu bằng chứng trong kho. Với ca rút nguồn, phiếu phải ghi sự kiện nào bị loại; không dùng nguồn bị rút để quyết định nhãn.

## Thu thập

Ghi câu hỏi và câu trả lời nguyên bản, công cụ/phiên bản và ngày lấy nếu thực sự lấy từ AI, hoặc ghi rõ tự xây dựng. Không gọi câu tự dựng là đầu ra đã thu từ ChatGPT. Dùng mã người thu thập, giữ dữ liệu gốc và thời điểm. Không trộn ca mới với các ca tổng hợp để tăng số người/mẫu.

Người gán nhãn cần đọc nguồn và tự quyết định trước khi xem dự đoán. Màn hình Phòng nghiên cứu ẩn nhãn tác giả và đầu ra máy trong phiếu, nhưng dữ liệu dự án có thể được truy cập ở nơi khác; đây không phải cơ chế bảo mật đánh giá mù. Người tổ chức phải bảo đảm quy trình độc lập nếu muốn công bố như vậy.

## Quy tắc nhãn

- **Có bằng chứng hỗ trợ:** các khẳng định kiểm chứng được trong phạm vi câu trả lời đều có căn cứ phù hợp, quan hệ/chủ thể/thời điểm đúng; không chỉ có một từ/ngày trùng.
- **Mâu thuẫn:** có ít nhất một khẳng định rõ ràng trái căn cứ. Đọc phạm vi phủ định và quan hệ; không gán chỉ vì từ vựng khác.
- **Chưa đủ bằng chứng:** thiếu dữ kiện cần hỏi, sự kiện/ý thêm ngoài kho, tiền đề chưa có căn cứ hoặc chưa tìm được bằng chứng để hỗ trợ/bác bỏ đầy đủ.
- **Không thể tự động kết luận** là đầu ra của thuật toán, không dùng làm nhãn chuẩn. Người đọc có thể xác định một nhãn chuẩn dù máy từ chối.

Với supported/contradicted, ghi ID dữ kiện khả dụng và vị trí nguồn, giải thích điều đã được kiểm tra. Không chọn ID thuộc sự kiện đã bị rút trong ca. Ghi nhận trường hợp mơ hồ để người hướng dẫn thống nhất chính sách trước khi chấm bộ cuối, không đổi nhãn theo kết quả máy.

## Hai người gán nhãn và bất đồng

Mỗi người dùng tên/mã của mình, gán độc lập. Hệ thống chỉ nhận một phiếu hiện hành trên cùng nội dung cho mỗi tên, giữ nhật ký chỉnh sửa. Hai tên trùng nhãn mới tạo ca đủ điều kiện cho phép đo đồng thuận; thiếu người hoặc bất đồng thì giữ chờ. Hai tên tự khai không chứng minh đó là hai người khác nhau; trách nhiệm tổ chức thuộc nhóm nghiên cứu.

Độ đồng thuận/kappa chỉ được tính từ nhãn đã nhập thật, trên cùng nội dung. Một nhãn duy nhất ở cả hai người làm kappa không xác định; không sửa thành 1. Không tự tạo tên, nhãn hoặc số lượng người tham gia để có biểu đồ.

## Đánh giá từ nhãn đồng thuận

Chỉ các ca người dùng nhập mới tham gia bảng kết quả ca thu thập, không lấy phiếu synthetic làm dữ liệu người học. Sự kiện không được trùng development. Phép đo này có nhãn toàn câu, chưa có gold mệnh đề độc lập nên chỉ báo chỉ số phân loại, không tự suy diễn gold từ bộ trích máy. Muốn nghiên cứu mệnh đề/bằng chứng độc lập, cần người đọc gán thêm chuẩn chi tiết.

Kết quả lưu riêng ở runtime/collected_study, không đưa dữ liệu người dùng vào ZIP source mặc định. Cần tuân thủ hướng dẫn của giáo viên/nhà trường nếu thu dữ liệu có người tham gia; không công bố hiệu quả học tập từ một phép đo kiểm chứng văn bản.
