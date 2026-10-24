"""Build current handoff documents exclusively from measured v2 artifacts."""
import json
import platform
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.research_evaluator import code_fingerprints, validate_freeze
from src.review import ReviewRepository
from src.utils import PROJECT_ROOT, atomic_json, runtime_dir, utc_now


def main():
    reports = PROJECT_ROOT / "reports"
    output = reports / "research_v2"
    summary = json.loads((output / "latest.json").read_text(encoding="utf-8"))
    suite = ET.parse(output / "pytest.xml").getroot().find("testsuite")
    if suite is None:
        raise RuntimeError("Missing actual pytest evidence")
    coverage = json.loads((output / "coverage.json").read_text(encoding="utf-8"))["totals"]["percent_covered"]
    commands = {"compile": [sys.executable, "-m", "compileall", "-q", "src", "app.py", "scripts"],
                "lint": [sys.executable, "-m", "ruff", "check", "."],
                "types": [sys.executable, "-m", "pyright"],
                "dependencies": [sys.executable, "-m", "pip", "check"]}
    checks = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        checks[name] = {"exit_code": result.returncode, "output": result.stdout.strip() + result.stderr.strip()}
    with urllib.request.urlopen("http://127.0.0.1:8501/_stcore/health", timeout=10) as response:
        health = {"status": response.status, "body": response.read().decode()}
    reproduction = json.loads((output / "reproducibility.json").read_text(encoding="utf-8"))
    repository = ReviewRepository(runtime_dir())
    actual = {"annotations": len(repository.annotations()), "collected_cases": len(repository.collected_cases()),
              "source_drafts": len(repository.records()), "audit_chain_ok": repository.verify_audit()}
    verification = {"verified_at": utc_now(), "python": platform.python_version(), "pytest": dict(suite.attrib),
                    "coverage_percent": coverage, "checks": checks, "health": health,
                    "reproducibility": reproduction, "actual_local_review_records_at_handoff": actual,
                    "engine_matches_freeze": validate_freeze(),
                    "visual_browser_review": "Not performed: prior localhost browser-origin permission was denied; no bypass attempted"}
    atomic_json(output / "verification.json", verification)
    lines = ["# Kiểm thử phiên bản nghiên cứu v2", "", f"Thời điểm ghi nhận: {verification['verified_at']} (UTC).",
             f"Pytest: {suite.get('tests')} ca; failures={suite.get('failures')}; errors={suite.get('errors')}; skipped={suite.get('skipped')}.",
             f"Coverage src: {coverage:.2f}%. Python {platform.python_version()} / Windows.", "",
             "| Cổng kiểm tra | Kết quả |", "|---|---|"]
    for name, result in checks.items():
        lines.append(f"| {name} | {'PASS' if result['exit_code'] == 0 else 'FAIL'} |")
    lines += [f"| HTTP localhost | {health['status']} / {health['body']} |",
              f"| Lặp dự đoán/mệnh đề/interval | {reproduction['identical_predictions_and_traces']} / {reproduction['identical_event_intervals']} |",
              f"| Mã lõi khớp đóng băng | {validate_freeze()} |", "",
              "## Các luồng mới đã chạy", "",
              "- Tách ba giá trị trong một câu, gắn đúng vị trí nguyên bản và nguồn; trộn đúng/sai; hai quan hệ thời gian.",
              "- Phủ định đơn, tiền đề sai/không xác minh, đổi vai trò, phần thêm ngoài nguồn, dữ kiện đã duyệt mâu thuẫn.",
              "- Dữ kiện nháp chưa có hiệu lực → duyệt → kiểm chứng thật qua AppTest → thu hồi; nhật ký/hash phát hiện thay đổi ngoài luồng.",
              "- Bốn phương pháp cùng ca, đối chứng chỉ fit development, chỉ số mệnh đề/bằng chứng, bootstrap theo cụm lặp được.",
              "- Giao diện Phòng nghiên cứu chạy thực nghiệm thật, phiếu chưa có nhãn không tự điền; dữ liệu thu thập cần hai tên đồng thuận, giữ ca bất đồng, không tạo số liệu người dùng.",
              "- Luồng kiểm chứng hoạt động khi helper kết nối socket/HTTP bị chặn bằng monkeypatch. Đây không phải thử nghiệm ngắt mạng cấp hệ điều hành.", "",
              "## Phạm vi còn thiếu", "",
              "Chưa kiểm tra trực quan bằng trình duyệt/ảnh chụp vì quyền mở localhost trước đó bị từ chối; đã dùng AppTest kiểm tra chức năng 7 trang. Chưa thử máy Windows khác hoặc phiên bản Python khác.",
              "Chưa có người dùng/giáo viên được trợ lý tự tạo để điền nghiên cứu. Các dữ liệu trong tests là fixture tạm và không đưa vào nghiên cứu thật.", "",
              "## Số bản ghi cục bộ thực tế lúc bàn giao", "", "```json", json.dumps(actual, ensure_ascii=False, indent=2), "```", ""]
    (reports / "kiem_thu.md").write_text("\n".join(lines), encoding="utf-8")
    atomic_json(reports / "verification.json", verification)
    atomic_json(output / "handoff_code_manifest.json", code_fingerprints())
    overview = "# Báo cáo kỹ thuật và nghiên cứu FactGuard EDU v2\n\n"
    overview += "Người thực hiện, trường, lớp và người hướng dẫn: **tự điền thông tin thật**.\n\n"
    for filename in ["nghien_cuu_v2.md", "research_v2/bao_cao_nghien_cuu.md", "gioi_han_nghien_cuu.md", "kiem_thu.md", "cong_bo_ho_tro_AI.md", "sources.md"]:
        overview += (reports / filename).read_text(encoding="utf-8") + "\n\n---\n\n"
    (reports / "bao_cao_ky_thuat.md").write_text(overview, encoding="utf-8")
    (reports / "ket_qua_nghien_cuu_v2.md").write_text((output / "bao_cao_nghien_cuu.md").read_text(encoding="utf-8"), encoding="utf-8")
    summary_lines = ["# Bàn giao phiên bản nghiên cứu v2", "", "## Ba module đã triển khai", "",
                     "1. Kiểm chứng mệnh đề theo quan hệ: giá trị, vị trí ký tự, nguồn, kết luận riêng và phần chưa xử lý.",
                     "2. Quản lý nguồn có thẩm định: nháp, duyệt, từ chối, thu hồi, lịch sử và hash; người duyệt tự khai.",
                     "3. Phòng nghiên cứu: bốn phương pháp, ablation, chỉ số theo giai đoạn, lặp lại, phiếu ẩn kết quả và ca người dùng tách riêng.", "",
                     "## Kết quả chính đo trên 46 ca tổng hợp", "", "| Phương pháp | Đúng / 46 | Accuracy | Hỗ trợ sai / 30 ca không được hỗ trợ |", "|---|---:|---:|---:|"]
    for method, metrics in summary["metrics"].items():
        summary_lines.append(f"| {method} | {round(metrics['accuracy'] * summary['cases'])} | {metrics['accuracy']:.4f} | {metrics['false_support_count']} |")
    summary_lines += ["", f"{suite.get('tests')} kiểm thử đạt; coverage {coverage:.2f}%. Mã lõi khớp đóng băng: {validate_freeze()}.",
                      "Kết quả tổng hợp cùng tác giả không chứng minh hiệu quả ngoài thực tế. Giữ bốn ca chưa đạt, phân tích dạng câu hỏi là hậu nghiệm và lưu riêng.",
                      "Chưa có nhãn/ca người dùng thật nếu các bộ đếm trong verification.json còn 0. Công cụ thu thập đã hoạt động nhưng không thay dữ liệu người dùng thực.", "",
                      "## Mở và chạy", "", "```powershell", "cd D:\\KHKT\\factguard-edu", ".\\.venv\\Scripts\\python.exe -m streamlit run app.py", "```", "",
                      "Mở http://127.0.0.1:8501. Các ví dụ mới ở Kiểm chứng; phép đo ở Phòng nghiên cứu; duyệt nguồn ở Kho kiến thức → Thẩm định dữ kiện.", ""]
    (reports / "ban_giao_v2.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print("V2 verification gates:", {k: v["exit_code"] for k, v in checks.items()})
    print("Pytest:", suite.get("tests"), "coverage:", round(coverage, 2), "actual review records:", actual)
    if any(result["exit_code"] for result in checks.values()) or suite.get("errors") != "0" or suite.get("failures") != "0" or not validate_freeze():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
