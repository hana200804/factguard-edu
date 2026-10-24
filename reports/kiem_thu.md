# Kiểm thử phiên bản nghiên cứu v2

Thời điểm ghi nhận: 2026-10-24T10:13:40+00:00 (UTC).
Pytest: 104 ca; failures=0; errors=0; skipped=0.
Coverage src: 90.76%. Python 3.12.10 / Windows.

| Cổng kiểm tra | Kết quả |
|---|---|
| compile | PASS |
| lint | PASS |
| types | PASS |
| dependencies | PASS |
| HTTP localhost | 200 / ok |
| Lặp dự đoán/mệnh đề/interval | True / True |
| Mã lõi khớp đóng băng | True |

## Các luồng mới đã chạy

- Tách ba giá trị trong một câu, gắn đúng vị trí nguyên bản và nguồn; trộn đúng/sai; hai quan hệ thời gian.
- Phủ định đơn, tiền đề sai/không xác minh, đổi vai trò, phần thêm ngoài nguồn, dữ kiện đã duyệt mâu thuẫn.
- Dữ kiện nháp chưa có hiệu lực → duyệt → kiểm chứng thật qua AppTest → thu hồi; nhật ký/hash phát hiện thay đổi ngoài luồng.
- Bốn phương pháp cùng ca, đối chứng chỉ fit development, chỉ số mệnh đề/bằng chứng, bootstrap theo cụm lặp được.
- Giao diện Phòng nghiên cứu chạy thực nghiệm thật, phiếu chưa có nhãn không tự điền; dữ liệu thu thập cần hai tên đồng thuận, giữ ca bất đồng, không tạo số liệu người dùng.
- Luồng kiểm chứng hoạt động khi helper kết nối socket/HTTP bị chặn bằng monkeypatch. Đây không phải thử nghiệm ngắt mạng cấp hệ điều hành.

## Phạm vi còn thiếu

Chưa kiểm tra trực quan bằng trình duyệt/ảnh chụp vì quyền mở localhost trước đó bị từ chối; đã dùng AppTest kiểm tra chức năng 7 trang. Chưa thử máy Windows khác hoặc phiên bản Python khác.
Chưa có người dùng/giáo viên được trợ lý tự tạo để điền nghiên cứu. Các dữ liệu trong tests là fixture tạm và không đưa vào nghiên cứu thật.

## Số bản ghi cục bộ thực tế lúc bàn giao

```json
{
  "annotations": 0,
  "collected_cases": 0,
  "source_drafts": 0,
  "audit_chain_ok": true
}
```
