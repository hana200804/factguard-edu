# Sản phẩm web FactGuard EDU

## Địa chỉ và tình trạng

Giao diện công khai: https://factguard-edu-hana-2026.choicelamp8.chatgpt.site

Giao diện HTML/CSS/JavaScript có thiết kế riêng; API Python gọi trực tiếp luật v2 và NLI v3 đã đóng băng. Không có bộ trả kết quả giả ở frontend. `web/catalog.json` là bản sao 33 dữ kiện và bảy nguồn gốc để người xem vẫn đọc được kho khi API chưa kết nối.

Giao diện đã được xuất bản trên Sites. API hiện chạy trên máy Windows này, được nối ra ngoài bằng Cloudflare Quick Tunnel. **Đây là kết nối tạm, không phải một máy chủ hoạt động 24/7.** Máy, Internet, API và tiến trình tunnel phải tiếp tục chạy. Dừng tunnel hoặc khởi động lại có thể đổi URL; khi đó cần cập nhật `web/config.js` và xuất bản lại frontend. Cloudflare mô tả mục đích và giới hạn tại [Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## Những luồng đã có

- **Kiểm chứng:** nhập câu hỏi/câu trả lời, chọn luật v2, v3 hoặc so sánh; đọc mệnh đề tô màu, giá trị mâu thuẫn, phần chưa xác minh, quyết định NLI và bằng chứng gốc. Ví dụ minh họa được ghi rõ; không phải câu trả lời đã thu từ chatbot.
- **Kho bằng chứng:** tìm kiếm và lọc dữ kiện, xem đáp án/tham chiếu/vị trí, mở URL nguồn.
- **Lịch sử:** tối đa 30 lượt trong trình duyệt; xem lại, tải JSON hoặc tự xóa. Không được tính thành dữ liệu nghiên cứu.
- **Phòng nghiên cứu:** mã truy cập riêng; tải mẫu CSV, xem trước ẩn xuất xứ, xác nhận nhập, gán nhãn thủ công, đánh giá năm phương pháp và tải Markdown/CSV/JSON. Cần ít nhất hai tên đồng thuận; tên vẫn là tự khai, chưa xác thực danh tính.
- **Ghi vết:** mỗi lần đánh giá lưu thư mục riêng; giữ đầu vào/nhãn dưới dạng mã băm, số ca chờ và số câu hỏi phân biệt. Giao diện báo khi kết quả đã cũ vì nhãn thay đổi. Mã băm tệp xuất phát hiện thay đổi ngoài lần lưu, không thay chữ ký số hoặc xác thực người dùng.

## Chạy trên Windows

```powershell
cd D:\KHKT\factguard-edu
.\.venv\Scripts\python.exe -m pip install -r requirements-web.txt
.\.venv\Scripts\python.exe scripts\serve_web.py --port 8765
```

Hoặc nhấp `run-web.bat`. Mở http://127.0.0.1:8765. Bản đang cấu hình gọi API qua URL công khai trong `web/config.js`; để chạy hoàn toàn cục bộ, đặt `apiBase: ""` trong file đó. Chạy NLI cần bốn tệp đúng SHA-256 dưới `models/mdeberta-xnli/`; máy hiện tại đã có, không cần tải lại.

## Vào khu vực nghiên cứu

Mã tự sinh nằm trong **`runtime/web/admin-key.txt`**. Mở file cục bộ và nhập mã tại Phòng nghiên cứu. Mã không nằm trong source, frontend hoặc Sites. Đóng truy cập sẽ xóa mã khỏi bộ nhớ trang; tải lại trang cần nhập lại. Có thể đặt `FACTGUARD_ADMIN_KEY` qua biến môi trường của máy chủ, ít nhất 24 ký tự. Không đưa mã vào URL, Git, ảnh chụp hay báo cáo.

API web có kho vận hành riêng ở `runtime/web/`, không tự lấy các ca từ cơ sở dữ liệu Streamlit cũ. Phiếu, CSV tải lên và kết quả nghiên cứu web đều ở đây; sao lưu thư mục này nếu cần giữ dữ liệu. CSV đã điền và dữ liệu cá nhân không được đóng gói cùng source.

Nhập tệp không tự tạo nhãn. Xem trước không tự nhập; có bất kỳ lỗi kiểm tra dòng nào thì chặn toàn tệp. Nhập lại bỏ qua ca đã có. Kiểm tra toàn bộ trước nhập không phải giao dịch SQLite hoàn tác mọi lỗi hệ thống giữa quá trình ghi.

## Triển khai API lâu dài

`Dockerfile.web` và `.dockerignore` chuẩn bị một image Python có model được tải từ revision cố định và kiểm SHA-256. Cấu hình Docker này chưa được chạy thử trên một VPS khác trong phiên hiện tại.

```powershell
docker build -f Dockerfile.web -t factguard-edu-web .
docker run --rm -p 8765:8765 -v factguard-data:/app/runtime --env FACTGUARD_WEB_ORIGINS=https://factguard-edu-hana-2026.choicelamp8.chatgpt.site factguard-edu-web
```

Đặt API sau HTTPS trên máy chủ do nhóm quản lý, lưu volume bền vững, quản lý mã truy cập như secret. Sau đó thay `apiBase` trong `web/config.js` bằng URL HTTPS của API và xuất bản lại frontend. Không cần sửa thuật toán đã đóng băng. Chưa cấu hình tài khoản máy chủ hoặc tên miền API cố định cho nhóm.

## Hợp đồng API

| Đường dẫn | Truy cập | Mục đích |
| --- | --- | --- |
| GET `/api/health`, `/api/catalog` | Công khai | Tình trạng dịch vụ, kho gốc |
| POST `/api/verify` | Công khai, giới hạn lượt | JSON question/answer/engine; không lưu vào nghiên cứu |
| GET `/api/admin/status`, `/api/admin/template` | Bearer quản trị | Hàng đợi/phiếu và mẫu trống |
| POST `/api/admin/cases`, `/api/admin/annotations` | Bearer quản trị | Nhập ca, lưu nhãn người dùng |
| POST `/api/admin/imports` | Bearer quản trị | CSV base64, tối đa 5 MB; chỉ xem trước |
| POST `/api/admin/imports/{id}/commit` | Bearer quản trị | Kiểm tra lại rồi nhập |
| POST `/api/admin/study` | Bearer quản trị | Đánh giá các ca đồng thuận bằng hàm v3 đã đóng băng |
| GET `/api/admin/study/{name}` | Bearer quản trị | report.md, results.csv hoặc summary.json |

Public API không trả dữ liệu nghiên cứu. CORS chỉ cho origin đã cấu hình; Bearer vẫn bắt buộc cho mọi endpoint quản trị. Có giới hạn kích thước, lượt kiểm chứng và một tác vụ nặng tại một thời điểm. Đây chưa phải hệ thống tài khoản nhiều trường học hoặc dịch vụ sản xuất chịu tải lớn.

## Cách hiểu kết quả

Kho hẹp; nguồn chưa được giáo viên thẩm định độc lập; kết quả hồi quy chỉ từ bộ tổng hợp đã xem. Kết quả cao không tự chứng minh lợi ích học tập hoặc rủi ro bằng 0. Web/giao diện/xuất báo cáo được bổ sung sau đóng băng, còn lõi v3, ngưỡng, mô hình và hàm đánh giá giữ nguyên. Chỉ báo cáo ca và phiếu thật mà nhóm đã nhập; không gọi dữ liệu phần mềm kiểm thử là dữ liệu người tham gia.
