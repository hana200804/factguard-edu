# Không gian lớp học FactGuard EDU

Phiên bản ngân hàng: `classroom-1.0.0`, ngày 25/10/2026.

## Giá trị sử dụng

Học sinh đọc nhận định, chọn kết luận, chỉ ra dữ kiện và tự ghi lý do trước khi xem đáp án. Giáo viên giao bộ bài từ ngân hàng, nhận phiếu ẩn danh và xem học sinh thường nhầm giữa nguồn của những sự kiện nào.

Mở [Luyện kiểm chứng](https://factguard-edu-hana-2026.choicelamp8.chatgpt.site/#practice) hoặc [Không gian giáo viên](https://factguard-edu-hana-2026.choicelamp8.chatgpt.site/#teacher).

Các luồng lớp học chạy trong trình duyệt, không gọi API AI hoặc ghi cơ sở dữ liệu nghiên cứu. Cần Internet để tải website ban đầu và mở bài nguồn gốc. Sau khi trang và kho đã tải, luyện tập không phụ thuộc API Python đang hoạt động. Không có bộ nhớ đệm ứng dụng bảo đảm mở website khi hoàn toàn mất mạng.

## Quy trình giao bài

1. Giáo viên mở **Không gian giáo viên**, đọc và kiểm tra bài với nguồn gốc. Ngân hàng do trợ lý soạn, chưa có thẩm định độc lập.
2. Đặt tên và mã riêng cho đợt giao bài; chọn 1–15 bài. Nhấn **Tải bộ bài JSON**. Mã, tên, phiên bản và thứ tự bài xác định bộ bài để tổng hợp.
3. Gửi tệp cho học sinh qua kênh của lớp. Học sinh mở **Luyện kiểm chứng**, chọn tệp và bắt đầu. Không yêu cầu họ tên, email, số điện thoại hay tài khoản.
4. Mỗi bài có ba trích lược dữ kiện kèm mã, vị trí và nút mở nguồn. Học sinh chọn nhãn, căn cứ, mức chắc chắn và viết lý do 20–600 ký tự.
5. Nộp từng bài để xem hướng dẫn. Không sửa câu vừa nộp trong cùng lượt; có thể tạo lượt mới để luyện lại. Tiến độ gần nhất và tối đa 20 phiếu hoàn tất lưu ở trình duyệt.
6. Hoàn tất để **Tải phiếu gửi giáo viên**. Học sinh kiểm tra lời giải thích có thông tin cá nhân không rồi chủ động gửi tệp JSON. Có thể in phiếu hoặc lưu PDF bằng hộp thoại in của trình duyệt.
7. Giáo viên chọn các phiếu cùng bộ bài tại **Đọc kết quả lớp**. Hệ thống tính lại điểm từ từng lựa chọn, bỏ phiếu trùng hoàn toàn và từ chối hai nội dung khác nhau cùng mã lượt.
8. Đọc tỷ lệ nhãn đúng, căn cứ đầy đủ, từng bài, ma trận nhầm lẫn và số câu sai ở mức chắc chắn từ 75%. Tải CSV hoặc in tổng hợp. Bảng không hiển thị số liệu khi chưa nhập phiếu.

Tối đa 200 phiếu/lần, 256 KB/tệp, tổng 10 MB. Tệp sai chặn cả lần nhập; nếu có tổng hợp trước đó thì giữ nguyên. Phiếu khác bộ bài hoặc khác phiên bản không gộp chung.

## Cách chấm

| Thành phần | Điểm | Quy tắc |
| --- | --- | --- |
| Kết luận | 0 hoặc 2 | Khớp nhãn hướng dẫn trong ngân hàng |
| Căn cứ | 0 hoặc 1 | Chọn đúng tập căn cứ cần thiết, không chọn thêm dữ kiện không trực tiếp |
| Lý do tự viết | Không tự chấm | Giữ nguyên để người học và giáo viên đọc lại |
| Mức chắc chắn | Không tính điểm | 50%, 75% hoặc 100%, do người học tự khai |

Mỗi bài tối đa 3 điểm. Một kết luận đúng nhưng chọn nguồn không liên quan có 2/3 điểm. Bài LT13 cần cả hai mốc thời gian. LT14 chỉ cần dữ kiện địa điểm mâu thuẫn để bác bỏ nhận định ghép. Với câu chưa đủ bằng chứng, học sinh chọn dữ kiện gần nhất để chỉ ra phần thông tin mà nguồn chưa cung cấp.

Ngân hàng có 5 bài hỗ trợ, 5 bài mâu thuẫn và 5 bài thiếu bằng chứng. Phân bố cân bằng này là thiết kế bài luyện, không đại diện phân bố câu trả lời chatbot thực tế. Các câu LT03/LT06/LT09/LT12/LT15 chứa chi tiết ngoài kho có chủ ý; không được coi các chi tiết đó là thông tin lịch sử đã xác thực.

## Gợi ý tiết học 25 phút

- 3 phút: phân biệt “mâu thuẫn” với “chưa đủ bằng chứng”, hướng dẫn tìm đúng sự kiện trong nguồn.
- 12 phút: làm bộ 6 bài mặc định, tự ghi lý do và mức chắc chắn.
- 5 phút: giáo viên cùng lớp đọc lại hai câu có tỷ lệ chọn sai/căn cứ thiếu cao nhất.
- 5 phút: học sinh tự viết điều sẽ kiểm tra trước khi dùng câu trả lời AI trong bài học.

Đây là kịch bản sử dụng đề xuất; chưa có lớp học thực tế nào được ghi nhận trong lần phát triển module này.

## Dữ liệu và giới hạn

- Phiếu không xác thực danh tính hoặc số người học. Một người có thể làm nhiều lượt; giao diện gọi là **lượt**, không gọi là số học sinh.
- Mã lượt ngẫu nhiên giúp tránh nhập trùng vô ý; không phải chữ ký số. Phiếu tự khai có thể bị sửa. Không dùng như sổ điểm hay bài thi bảo mật. Đáp án có trong mã frontend công khai.
- Tổng hợp được giữ trong bộ nhớ trang giáo viên, mất khi tải lại. Tải CSV nếu cần giữ. CSV đặt trong dấu nháy và trung hòa tiền tố công thức bảng tính.
- Tiến độ/phiếu trong trình duyệt có thể mất khi xóa dữ liệu trình duyệt hoặc đổi máy. Không có đồng bộ tài khoản. Lịch sử luyện tập tách với lịch sử kiểm chứng AI.
- Lời giải thích tự do có thể chứa thông tin cá nhân do người viết nhập; kiểm tra trước khi gửi phiếu hoặc chia sẻ CSV. Website không tự gửi những nội dung này lên máy chủ.
- Điểm dựa trên đáp án hướng dẫn đã soạn; chưa có giáo viên thẩm định độc lập và chưa chứng minh cải thiện học tập. Số liệu lớp là mô tả các phiếu đã nhập, không phải thử nghiệm có đối chứng.
- Bài luyện không đi vào tập đánh giá khoa học v2/v3. Mã luật, ngưỡng NLI, mô hình và manifest đóng băng được giữ nguyên.

## Kiểm tra phần mềm

```powershell
& 'C:\Program Files\nodejs\node.exe' --test tests\classroom.test.cjs
.\.venv\Scripts\python.exe -m pytest -q
```

Test JavaScript dùng phiếu giả có ghi rõ `software-fixture`, không tạo người tham gia nghiên cứu. Phủ chấm điểm độc lập hai thành phần, bằng chứng nhiều mệnh đề, nhập phiếu hỏng/trùng/khác bộ, tính lại điểm và trung hòa công thức CSV.
