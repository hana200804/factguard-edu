# Hướng dẫn thu thập câu trả lời AI thật

## Mục đích và dữ liệu hiện có

Quy trình này giúp thu câu trả lời **thực sự nhận được từ chatbot**, giữ thông tin xuất xứ và đưa vào hàng đợi để hai người gán nhãn độc lập trong Phòng nghiên cứu. Việc tạo mẫu hoặc nhập CSV không sinh câu trả lời, không gán nhãn và không tự tạo kết quả thực nghiệm.

Ngân hàng [cau_hoi.csv](../data/collection/cau_hoi.csv) có **50 câu hỏi do trợ lý soạn**, ghi `nguon_cau_hoi = tro_ly`. [mau_ghi_cau_tra_loi.csv](../data/collection/mau_ghi_cau_tra_loi.csv) có **100 dòng trống câu trả lời**: 50 câu × ChatGPT, Gemini. Đây là công cụ chuẩn bị thu thập, chưa phải 100 đầu ra chatbot đã thu được. Không trộn các câu trả lời tổng hợp trong bộ đánh giá cũ vào dữ liệu thu thập thật.

## Bảy loại câu hỏi

| `loai` | Ý nghĩa |
| --- | --- |
| `don` | Hỏi một dữ kiện. |
| `ket_hop` | Hỏi kết hợp nhiều dữ kiện. |
| `tien_de_sai` | Câu hỏi chứa tiền đề sai có chủ đích. |
| `kiem_tra` | Hỏi xác nhận, chẳng hạn “có đúng là… không?”. |
| `mo` | Câu hỏi mở, có thể dẫn tới câu trả lời chứa nhiều ý. |
| `ngoai_kho` | Hỏi về sự kiện ngoài kho tham chiếu; dùng `ma_su_kien = outside`. |
| `thieu_du_kien` | Sự kiện có trong kho nhưng kho không có dữ kiện được hỏi. |

**Loại câu hỏi không phải nhãn câu trả lời.** Người gán nhãn phải đọc câu trả lời và nguồn khả dụng để tự quyết định. Không suy ra nhãn từ `loai`, tên chatbot hoặc việc câu hỏi có tiền đề sai. Quy tắc nhãn nằm trong [hướng dẫn gán nhãn](huong_dan_gan_nhan.md).

## Chuẩn bị một lượt thu

1. Chọn công cụ và một `kieu_lenh` cố định cho cả lượt thu. Quy định trước cách xử lý việc công cụ không dùng được hoặc không trả lời; ghi nhận tình huống đó, không tự điền câu trả lời thay thế.
2. Dùng mã người thu thập để hạn chế thông tin cá nhân. Người thu thập nên khác người gán nhãn. Giữ bản ghi gốc và ghi ngày lấy ngay khi thực hiện.
3. Mở PowerShell tại thư mục dự án `D:\KHKT\factguard-edu`, đã cài thư viện theo README. Tạo tệp riêng cho lượt thu:

```powershell
.\.venv\Scripts\python.exe scripts\build_collection_kit.py --tools ChatGPT Gemini Copilot --output data\collection\dot1.csv
```

Với ngân hàng hiện tại, lệnh này tạo 150 dòng trống: 50 câu × ba công cụ. Có thể đổi danh sách sau `--tools` và tên sau `--output`. Không truyền `--tools` thì mặc định là ChatGPT và Gemini. Script từ chối ghi đè tệp đã có ít nhất một câu trả lời; tệp còn trống có thể bị ghi lại, nên dùng tên mới cho mỗi lượt.

## Cách hỏi chatbot

- Mỗi câu hỏi mở **một cuộc trò chuyện mới**, tránh ngữ cảnh từ câu trước. Tắt custom instructions và memory nếu công cụ có các tùy chọn này. Nếu không thể kiểm soát thiết lập, ghi rõ trong `ghi_chu`.
- Không chủ động bật tìm kiếm web trong lượt thu thông thường. Nếu sử dụng web hoặc công cụ tự dùng web mà giao diện có hiển thị, ghi trạng thái đó trong `ghi_chu`; không gộp các điều kiện khác nhau mà bỏ thông tin.
- Với `kieu_lenh = ngan_gon`, gửi nguyên câu hỏi rồi thêm đúng: **“Trả lời ngắn gọn trong 1–2 câu.”** Với `tu_do`, chỉ gửi câu hỏi. Cột `cau_hoi` trong CSV vẫn giữ nguyên nội dung của ngân hàng, không thêm câu chỉ dẫn vào cột này.
- Giữ một kiểu lệnh cố định cho cả lượt. Muốn so sánh hai kiểu lệnh thì tạo các lượt riêng và ghi đủ thông tin điều kiện.
- Chỉ lấy **câu trả lời đầu tiên**. Không bấm tạo lại, sửa câu hỏi hoặc hỏi tiếp để chọn câu trả lời thuận lợi. Nếu đã hỏi khác ngân hàng, giữ bản gốc và thêm mã câu hỏi mới trước khi nhập.
- Dán nguyên văn câu trả lời vào `cau_tra_loi`, kể cả khi chatbot từ chối, sai hoặc đưa thêm ý ngoài kho. Không sửa lỗi kiến thức, rút gọn hoặc thêm lời giải thích của người thu thập. Giữ bản gốc để đối chiếu khi dữ liệu bảng tính có vấn đề.
- Ghi tên/phiên bản mô hình hiển thị trong giao diện vào `phien_ban`; không suy đoán phiên bản, ghi `không rõ` nếu không thấy. Ghi ngày thực sự lấy bằng `YYYY-MM-DD` vào `ngay_lay`.

Câu trả lời dài thường có thêm khẳng định ngoài kho; điều này có thể dẫn tới nhãn “chưa đủ bằng chứng”. Không loại các câu đó chỉ vì gây khó cho hệ thống.

## Điền các cột trong mẫu

| Cột | Cách điền |
| --- | --- |
| `ma_cau_hoi` | Giữ mã trong ngân hàng, chẳng hạn `Q01`. |
| `ma_su_kien` | Giữ sự kiện gắn với câu hỏi trong ngân hàng. |
| `cau_hoi` | Giữ nguyên câu hỏi; kiểm tra nhập cho phép khác biệt chỉ ở khoảng trắng. |
| `cong_cu` | Tên công cụ thực sự dùng; mẫu đã điền theo danh sách `--tools`. |
| `phien_ban` | Phiên bản/tên mô hình quan sát được, hoặc `không rõ`. |
| `ngay_lay` | Khuyến nghị `YYYY-MM-DD`; bộ nhập cũng nhận `DD/MM/YYYY` và `DD-MM-YYYY`. Không nhập ngày tương lai hoặc trước 2022-11-30. |
| `kieu_lenh` | Chỉ nhận `ngan_gon` hoặc `tu_do`. |
| `nguoi_thu_thap` | Mã người thực sự thu thập. |
| `cau_tra_loi` | Nguyên văn đầu ra đầu tiên, tối đa 12.000 ký tự. Chưa thu thì để trống. |
| `ghi_chu` | Thông tin điều kiện thu như web, thiết lập không kiểm soát được hoặc sự cố; có thể để trống. |

Giữ tên các cột. Dòng chưa có `cau_tra_loi` được đếm là chưa điền và bỏ qua, không phải lỗi. Với dòng đã điền, công cụ, phiên bản, ngày, kiểu lệnh và người thu thập phải hợp lệ. Hai dòng cùng câu hỏi và nguyên văn câu trả lời bị báo trùng trong cùng tệp, kể cả khi tên công cụ khác nhau. Không sửa nội dung để né kiểm tra trùng; giữ bản ghi gốc và ghi nhật ký nếu loại dòng trùng khỏi tệp nhập. Nhập qua tệp khác vẫn bỏ qua ca đã có theo cặp câu hỏi/câu trả lời, không tạo mẫu độc lập mới. Hàng đợi hiện tại không phải sổ đếm mọi lượt gọi chatbot.

## Dùng Excel và giữ nguyên văn bản

1. Trước khi dán, định dạng cột `ngay_lay` và `cau_tra_loi` là **Text**. Sau khi Excel đã đổi dữ liệu, đổi định dạng ô sang Text không khôi phục được bản gốc; phải dán lại từ bản ghi gốc.
2. Nếu câu trả lời bắt đầu bằng `-`, `=` hoặc `+`, nhập dấu nháy đơn `'` ở đầu ô để Excel coi nội dung là văn bản. Đây là ký hiệu nhập của bảng tính; sau khi lưu, kiểm tra CSV bằng trình soạn thảo để chắc rằng không thêm dấu nháy đơn vào nguyên văn câu trả lời. Không dùng cách này như phép sửa nội dung trong CSV đã xuất.
3. Lưu bằng **CSV UTF-8 (Comma delimited)**. Bộ đọc chấp nhận UTF-8 có hoặc không BOM và nhận dấu phân tách `,`, `;` hoặc tab từ hàng tiêu đề. CSV có dấu `;` do thiết lập vùng của Excel được hỗ trợ.
4. Bộ nhập từ chối tệp không giải mã được bằng UTF-8 và phát hiện **một số** mẫu ô có vẻ bị đổi thành số, ngày ISO hoặc lỗi công thức, ví dụ `45000`, `1945-09-02`, `#NAME?`. Đây không phải kiểm tra đầy đủ mọi mất mát do Excel; một chuỗi thuần số/ngày thật cũng có thể bị cảnh báo. Đối chiếu bản ghi gốc, không tự thêm nội dung để qua kiểm tra.
5. Kiểm tra dấu tiếng Việt, dấu xuống dòng và nguyên văn sau khi lưu. Có thể dùng Google Sheets hoặc LibreOffice, vẫn cần chọn xuất UTF-8 và kiểm tra lại. Luôn giữ một bản gốc trước khi mở/chỉnh trong bảng tính.

## Kiểm tra rồi nhập

Chạy kiểm tra toàn bộ tệp trước:

```powershell
.\.venv\Scripts\python.exe scripts\import_collected.py data\collection\dot1.csv --dry-run
```

Lệnh in số dòng hợp lệ, lỗi và chưa điền. `--dry-run` không đưa ca vào hàng đợi và không tạo cơ sở dữ liệu nghiên cứu. Sửa mọi lỗi được báo theo số dòng rồi chạy lại. Nếu tất cả câu trả lời còn trống thì chưa có ca nào để nhập.

Khi không còn lỗi kiểm tra dữ liệu, nhập thật:

```powershell
.\.venv\Scripts\python.exe scripts\import_collected.py data\collection\dot1.csv
```

Script **kiểm tra toàn bộ dữ liệu trước khi bắt đầu nhập**: có lỗi kiểm tra ở bất kỳ dòng đã điền nào thì không nhập dòng nào trong lượt đó. Quy tắc này không phải cam kết hoàn tác mọi lỗi ghi đĩa hoặc I/O phát sinh giữa quá trình nhập. Nếu việc ghi bị ngắt, giữ tệp gốc, kiểm tra thông báo và hàng đợi rồi chạy lại; các ca đã có được bỏ qua theo nội dung.

Nhập lại cùng tệp không tạo ca trùng. Ca mới được lưu **chưa có nhãn** trong `runtime\research.sqlite3`; nhật ký CSV theo lượt ở `runtime\collection_imports\`, gồm `row`, `qid`, `case_id`, `status` (`đã nhập` hoặc `đã có, bỏ qua`). Nếu đã đặt `FACTGUARD_RUNTIME_DIR`, cơ sở dữ liệu và nhật ký nằm dưới thư mục đó. Thông tin xuất xứ như công cụ, phiên bản, ngày và ghi chú được giữ trong bản ghi; cần sao lưu dữ liệu cục bộ nếu muốn bảo toàn hồ sơ thu thập.

## Nhập CSV ngay trong giao diện

Có thể dùng **Phòng nghiên cứu → Gán nhãn độc lập → Nhập nhiều câu trả lời từ tệp CSV** thay cho lệnh nhập:

1. Bấm **Tải mẫu ghi câu trả lời CSV** nếu cần mẫu trống mặc định, rồi điền và lưu UTF-8 theo hướng dẫn trên.
2. Chọn CSV tối đa **5 MB**. Giao diện kiểm tra cả tệp, hiện số dòng hợp lệ/chưa điền và từng lỗi nếu có. Bảng xem trước chỉ chứa số dòng, mã câu hỏi, câu hỏi và câu trả lời; không hiện thông tin công cụ hay người thu thập.
3. Khi không còn lỗi, bấm **Nhập vào hàng đợi gán nhãn**. Chỉ tải lên hoặc xem trước chưa thêm ca; tệp toàn dòng trống không có ca để nhập. Quy tắc chống trùng và trạng thái chưa có nhãn giống lệnh nhập.

Bản CSV gốc tải lên được giữ dưới tên `upload_*.csv`, nhật ký sau khi bấm nhập dưới tên `import_*.csv`, trong `runtime/collection_imports/` (hoặc thư mục do `FACTGUARD_RUNTIME_DIR` chỉ định). Tệp gốc vẫn chứa xuất xứ và thông tin người thu thập; việc ẩn bảng xem trước không bảo vệ quyền truy cập các tệp cục bộ. Nếu nhập bị ngắt hoặc không ghi được nhật ký, kiểm tra hàng đợi trước khi thử lại.

## Gán nhãn độc lập và phép đo

Mở ứng dụng → **Phòng nghiên cứu → Gán nhãn độc lập**. Hai người dùng mã riêng, đọc nguồn và tự gán nhãn trước khi xem đầu ra FactGuard; xem [quy trình gán nhãn](huong_dan_gan_nhan.md). Người thu thập nên bàn giao phiếu mà không gợi ý nhãn hoặc tiết lộ công cụ cho người chấm. Việc ẩn thông tin trên giao diện không thay thế việc tổ chức đánh giá độc lập.

Một ca cần nhãn từ **ít nhất hai tên khác nhau và tất cả phiếu hiện hành trên cùng nội dung đồng nhãn** mới vào phép đo ca thu thập; thiếu người hoặc còn bất đồng thì giữ chờ. Tên là tự khai, phần mềm không xác thực danh tính hay chứng minh đó là hai người độc lập. Kappa chỉ tính từ nhãn đã nhập thật, không tự tạo người hoặc nhãn để có kết quả. Nếu kappa không xác định, giữ trạng thái đó. Kết quả ca thu thập được lưu riêng trong `runtime\collected_study`, không thay thế báo cáo challenge v2.

## Bổ sung câu hỏi của giáo viên/học sinh

Nên có thêm câu hỏi do giáo viên/học sinh thực sự đặt để giảm phụ thuộc vào bộ do trợ lý soạn. Trong `data\collection\cau_hoi.csv`, thêm mã duy nhất từ **Q51 trở đi** (dạng `Q` kèm 2–4 chữ số), điền đủ năm cột `ma_cau_hoi`, `ma_su_kien`, `loai`, `cau_hoi`, `nguon_cau_hoi`; cột cuối ghi tên hoặc mã người đặt thực sự.

Chỉ chọn sự kiện được `eligible_events` chấp nhận: sự kiện có trong kho đi kèm và **không thuộc development**, hoặc `outside` cho câu ngoài kho. Không dùng `departure1911`, `return1941`, `conference1941`. Nếu sự kiện có trong kho nhưng thiếu dữ kiện được hỏi, giữ mã sự kiện đó và dùng `loai = thieu_du_kien`. Không đổi mã thành `outside` chỉ để lách giới hạn sự kiện.

Giữ nguyên các tệp đã đóng băng liệt kê trong `reports\research_v2\engine_freeze.json`, gồm kho dữ kiện, tập đánh giá và mã lõi. Không sửa chúng để thêm câu hỏi thu thập hoặc cải thiện điểm. Sau khi bổ sung ngân hàng, chạy lại `scripts\build_collection_kit.py` với **`--output` là tên tệp mới**, chẳng hạn `data\collection\dot2.csv`. Số dòng mẫu lúc đó bằng số câu hiện có × số công cụ; lưu riêng bản ngân hàng đã dùng cho mỗi lượt để truy lại câu hỏi.

## Quyền riêng tư và giới hạn diễn giải

Không đưa thông tin cá nhân hoặc dữ liệu nhạy cảm vào câu hỏi, câu trả lời và ghi chú. Dùng mã người thay cho thông tin nhận diện khi có thể. Khi có người tham gia, thực hiện theo hướng dẫn của giáo viên/nhà trường. Bản ghi cục bộ chưa có cơ chế phân quyền hoặc mã hóa cho nghiên cứu nhiều người.

`runtime/` được loại khỏi ZIP source mặc định, nhưng **`scripts/package_project.py` hiện có đóng gói `data/collection/`**. Tệp mẫu đã điền đặt trong thư mục này có thể đi vào ZIP hoặc được đưa lên Git. Mẫu gốc hiện còn trống; không tự commit/push tệp đã điền cùng mã nguồn. Trước khi chia sẻ, kiểm tra từng tệp; có thể giữ tệp đã điền và bản ghi gốc trong `runtime/` hoặc ngoài source nếu không định công bố, đồng thời truyền đúng đường dẫn đó cho lệnh nhập.

Một lượt thu tại một thời điểm chỉ phản ánh câu hỏi, điều kiện và phiên bản đã ghi; không đại diện cho mọi phiên bản hoặc mọi cách dùng chatbot. Đầu ra có thể thay đổi theo thời gian. Nhãn đánh giá mức hỗ trợ từ kho tham chiếu khả dụng, không phải phán quyết về mọi kiến thức trên Internet. Bộ câu hỏi do trợ lý soạn và quy trình chọn mẫu vẫn có thể gây thiên lệch; không suy ra hiệu quả học tập hay khả năng khái quát rộng từ một lượt thu.
