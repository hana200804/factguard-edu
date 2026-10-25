# Prompt làm video demo FactGuard EDU

> Dán nguyên phần trong khung "PROMPT CHÍNH" vào Claude Code (mở tại `D:\KHKT`, đã cài plugin HyperFrames).
> Phần cuối có bản rút gọn cho các công cụ AI video khác (Veo, Sora, Runway, Kling…).

---

## PROMPT CHÍNH (Claude Code + skill HyperFrames)

```text
/hyperframes Làm video demo giới thiệu dự án KHKT "FactGuard EDU — Bằng chứng trước kết luận".

## Bước 0 — Tải và kiểm tra công cụ, skill (làm TRƯỚC mọi thứ, báo tôi kết quả từng lệnh)
Thiếu cái gì thì cài cái đó; lệnh nào lỗi thì dừng lại báo tôi nguyên văn lỗi, không tự đoán workflow từ trí nhớ.

1. Công cụ nền (Windows):
   - Node.js LTS (cần có `node` và `npx`): `node -v`, `npx --version`
     → nếu thiếu: `winget install OpenJS.NodeJS.LTS`
   - FFmpeg (để render và xử lý âm thanh): `ffmpeg -version`
     → nếu thiếu: `winget install Gyan.FFmpeg`
   - Mở terminal mới sau khi cài để PATH nhận.
2. Xác định kiểu cài HyperFrames: tìm `plugin.json` / `.claude-plugin/plugin.json` ở thư mục
   cách SKILL.md của /hyperframes hai cấp.
   - Nếu là PLUGIN: KHÔNG chạy `skills update` / `npx skills add`; đọc workflow trong plugin,
     thay `npx hyperframes` bằng `node "<PLUGIN_ROOT>/skills/hyperframes/scripts/plugin-cli.mjs"`.
   - Nếu là skill STANDALONE (trong ~/.claude/skills): làm tiếp bước 3–5.
3. Kiểm tra và cập nhật bộ skill lõi (/hyperframes, hyperframes-*, /media-use):
     npx hyperframes skills check
     npx hyperframes skills update
4. Tải các workflow + skill sẽ dùng cho video này:
     npx hyperframes skills update product-launch-video hyperframes-registry hyperframes-keyframes hyperframes-audio media-use
   Nếu CLI hyperframes không chạy được, dùng phương án dự phòng:
     npx skills add heygen-com/hyperframes --skill product-launch-video
   (hoặc `npx skills add heygen-com/hyperframes --all` để tải toàn bộ).
5. Chạy `npx hyperframes doctor` và `npx hyperframes usage --json`; báo tôi hạn mức còn lại.
6. Chuẩn bị app để chụp màn hình:
     cd D:\KHKT\factguard-edu
     .\.venv\Scripts\python.exe -m pip install -r requirements-web.txt
     .\.venv\Scripts\python.exe scripts\serve_web.py --port 8765
   Chạy server ở chế độ nền, kiểm tra http://127.0.0.1:8765 mở được rồi mới chụp.
7. Nếu sau khi cài, skill mới chưa hiện trong danh sách skill thì báo tôi mở lại phiên (reload)
   rồi làm tiếp từ bước 1 của phần dưới.

## Chuỗi skill phải dùng (theo đúng thứ tự)
1. /hyperframes → route sang /product-launch-video (showcase một web app từ URL).
   Các câu trả lời interview đã có sẵn bên dưới, ghi thẳng vào BRIEF.md,
   không hỏi lại trừ khi thiếu thật.
2. Đọc SKILL.md của /product-launch-video vừa tải ở Bước 0 rồi làm theo workflow đó.
3. /hyperframes-creative → design spec (palette, font), beat plan, viết lời thoại.
4. /hyperframes-registry → TÌM TRƯỚC khi tự dựng: khung trình duyệt, highlight/underline chữ,
   stat counter, bar chart, check/cross badge, transition. Chỉ tự viết khi registry không có.
5. /hyperframes-animation + /hyperframes-keyframes → punch-in vào ô kết quả, Ken Burns trên ảnh chụp
   màn hình, tô màu từng mệnh đề trong câu, chuyển cảnh.
6. /media-use → giọng đọc tiếng Việt (TTS, giọng nữ trẻ, rõ, tốc độ vừa), nhạc nền nhẹ kiểu
   edu/tech, SFX "tick" khi hiện kết quả; tạo phụ đề tiếng Việt từ voiceover.
7. /hyperframes-audio → duck nhạc nền dưới giọng đọc, fade in/out đầu–cuối.
8. /hyperframes-cli → `check`, `snapshot` từng cảnh để tôi duyệt, mở Studio preview trước khi render,
   rồi render MP4.

## Trả lời sẵn cho intent interview
- Sell hay show: SHOW là chính (dùng ảnh chụp màn hình thật của app), có một chút "sell" ở mở đầu/kết.
- Góc kể: "AI trả lời rất tự tin — nhưng có đúng không? FactGuard cho học sinh xem bằng chứng trước khi tin."
- Độ dài: ~90 giây (cho phép 75–110s).
- Đích: thuyết trình hội thi KHKT + YouTube → 16:9, 1920×1080, 30fps.
- VO_MODE: restructured (được sửa câu chữ cho tự nhiên, nhưng KHÔNG đổi số liệu và giới hạn).
- Capture: có. Chụp app chạy CỤC BỘ để ổn định:
    cd D:\KHKT\factguard-edu
    .\.venv\Scripts\python.exe scripts\serve_web.py --port 8765
  rồi mở http://127.0.0.1:8765 . (Bản tĩnh ở D:\KHKT\factguard-web\dist cũng dùng được.)
  Không dùng link công khai vì đường hầm tạm có thể tắt.
- Nên chụp: trang kiểm chứng (3 ca: đúng / sai / chưa đủ bằng chứng), ca "đúng ngày nhưng sai nhân vật"
  có tô màu vị trí trong câu, kho nguồn, Không gian lớp học (luyện kiểm chứng + màn giáo viên),
  bảng kết quả Phòng nghiên cứu.

## Nhận diện thương hiệu (lấy từ factguard-web/dist/style.css)
- Tiêu đề: Georgia (serif) — gợi cảm giác sách sử, học thuật. Thân chữ: Segoe UI / sans.
- Màu chính: xanh #2858c8. Nền sáng #f3f6fa / #edf1f5. Chữ phụ #91a0af.
- Màu trạng thái: hỗ trợ = xanh lá nhạt #e5f3e9; mâu thuẫn = hồng/đỏ nhạt #fbe9ec;
  chưa đủ bằng chứng = vàng nhạt #fff1d9.
- Phong cách: sạch, nhiều khoảng trắng, chuyển động gọn (ease-out), không glitch/neon.

## Storyboard (gợi ý — được chỉnh nhịp, giữ nội dung)
1. (0–8s) HOOK — Một khung chat AI gõ ra: "Chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1955."
   Chữ "1955" rung nhẹ, dấu "?" đỏ hiện lên.
   VO: "AI trả lời rất nhanh và rất tự tin. Nhưng nếu nó sai một con số thì sao?"
2. (8–16s) GIỚI THIỆU — Logo/tên FactGuard EDU + khẩu hiệu "Bằng chứng trước kết luận".
   VO: "FactGuard EDU giúp học sinh THPT đối chiếu câu trả lời của AI về Lịch sử Việt Nam với kho dữ kiện có nguồn."
3. (16–34s) DEMO 1: ĐÚNG — Ảnh chụp trang kiểm chứng. Câu hỏi "Chủ tịch Hồ Chí Minh đọc Tuyên ngôn
   Độc lập vào ngày nào?" – trả lời "Ngày 2 tháng 9 năm 1945" → badge xanh "Có bằng chứng hỗ trợ",
   punch-in vào dữ kiện F001 + URL nguồn Bảo tàng TP.HCM.
   VO: "Nhập câu hỏi và câu trả lời. Hệ thống tách mệnh đề, chuẩn hóa ngày tháng và chỉ ra đúng dữ kiện, đúng nguồn."
4. (34–48s) DEMO 2: SAI — Câu Điện Biên Phủ 7/5/1955 → badge đỏ "Mâu thuẫn", hiện bằng chứng 7/5/1954.
   VO: "Sai một năm? FactGuard chỉ ra mâu thuẫn — kèm bằng chứng, không phải đoán theo độ giống chữ."
5. (48–58s) DEMO 3: TỪNG MỆNH ĐỀ — ca "đúng ngày nhưng sai nhân vật": câu gốc được tô màu từng đoạn,
   ngày ✔ xanh, nhân vật ✘ đỏ. Thêm ca "chưa đủ bằng chứng" (chỉ có năm khi câu hỏi hỏi ngày) badge vàng.
   VO: "Mỗi ý được kiểm riêng. Thiếu bằng chứng thì hệ thống nói thật là chưa đủ, thay vì đoán bừa."
6. (58–70s) LỚP HỌC — Không gian lớp học: 15 bài luyện có nguồn, học sinh chọn kết luận và căn cứ;
   màn giáo viên có ma trận nhầm lẫn, xuất CSV/PDF.
   VO: "Trong lớp, học sinh luyện kiểm chứng với 15 bài có nguồn; giáo viên giao bài và xem thống kê."
7. (70–84s) KẾT QUẢ NGHIÊN CỨU — bar chart động so sánh 4 phương pháp trên bộ thử thách 46 ca / 10 cụm sự kiện:
   Accuracy: khớp từ học máy 0,37 · luật v1 0,02 · mệnh đề không chốt 0,87 · mệnh đề có chốt 0,91.
   F1 macro bản đầy đủ 0,94; hỗ trợ sai: 0 trên 30 ca không được hỗ trợ.
   Chú thích nhỏ cố định trên màn hình: "Dữ liệu tổng hợp do nhóm xây dựng, chưa gán nhãn độc lập."
   VO: "Trên bộ thử thách 46 ca, cách kiểm từng mệnh đề có chốt an toàn đạt độ chính xác 0,91 và không đưa ra kết luận hỗ trợ sai nào."
8. (84–92s) KẾT — chip: "Chạy offline trên CPU" · "Không cần API key" · "33 dữ kiện · 7 nguồn chính thức" ·
   "Mã nguồn có kiểm thử". Logo + khẩu hiệu.
   VO: "FactGuard EDU — kiểm chứng để hiểu đúng."

## Ràng buộc nội dung (BẮT BUỘC)
- Chỉ dùng số liệu ở trên (nguồn: factguard-edu/README.md và reports/research_v2/bao_cao_nghien_cuu.md).
  Không làm tròn thành "93%", không gọi là "độ tin cậy", không nói "chính xác tuyệt đối".
- Không nói đã thử nghiệm với học sinh thật hay chứng minh cải thiện học tập — chưa có dữ liệu đó.
- Không nói câu trả lời ví dụ do ChatGPT/Gemini tạo ra; đó là ví dụ tự dựng.
- Không có tên học sinh, trường, logo tổ chức thật nào trừ khi tôi cung cấp.
- Phụ đề tiếng Việt có dấu đầy đủ, nằm trong safe zone, không che nút/badge đang được nhấn mạnh.

## Đầu ra
- Dự án HyperFrames trong D:\KHKT\video-demo\ (mỗi cảnh là một sub-composition, một track phụ đề).
- Gửi tôi snapshot từng cảnh để duyệt trước khi render.
- Render: D:\KHKT\video-demo\renders\factguard-edu-demo.mp4, kèm file .srt phụ đề.
```

---

## Bản rút gọn cho công cụ AI video khác (Veo / Sora / Runway / Kling)

Các công cụ này không đọc được app thật, nên chỉ dùng để tạo **đoạn mở đầu (hook) 8–10 giây** rồi ghép với phần demo quay màn hình:

```text
Clean, modern educational tech explainer, 16:9, soft daylight. A Vietnamese high-school student
at a desk looks at a laptop showing an AI chat bubble with a confident answer about a historical date.
The year in the answer glows faint red and a small question mark appears. Camera slowly pushes in.
Cut to the laptop screen: a minimalist white web app with a blue (#2858c8) header shows three result
badges sliding in — green "supported", red "contradicted", yellow "not enough evidence" — each linked
to a source card. Calm, trustworthy mood, serif headline typography, plenty of white space,
no real logos, no readable brand names, smooth ease-out motion, light piano + soft electronic music.
```

Gợi ý: phần chữ tiếng Việt trên màn hình nên thêm sau bằng HyperFrames/CapCut, vì AI video thường viết sai dấu tiếng Việt.
