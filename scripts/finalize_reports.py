"""Assemble documentation from measured artifacts. Never synthesize scores."""
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    reports = ROOT / "reports"
    summary = json.loads((reports / "experiment" / "latest.json").read_text(encoding="utf-8"))
    sources = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    source_lines = ["# Nguồn dữ liệu đã đối chiếu", "", "Ngày kiểm tra trực tuyến: 24/10/2026.",
                    "Tất cả URL dưới đây đã được mở và đọc bằng công cụ web trong phiên xây dựng; không dùng URL chỉ tìm thấy nhưng mở lỗi.",
                    "Bản cục bộ là tóm lược tự biên soạn, không phải nguyên văn. Cần giáo viên/học sinh thẩm định lại trước khi nộp.", ""]
    for source in sources:
        source_lines += [f"## {source['id']}. {source['title']}", "",
                         f"- Cơ quan: {source['publisher']}.", f"- Ngày đăng/ban hành: {source['published_at']}.",
                         f"- [Đọc trang gốc]({source['url']}).", f"- Đối chiếu ngày: {source['checked_at']}.",
                         f"- Cách kiểm tra: {source['verification_method']}.",
                         f"- Tóm lược cục bộ: data/sources/{source['file']}; vị trí từng dữ kiện: data/facts.csv.", ""]
    source_lines += ["## Tài liệu kỹ thuật đã tham khảo", "",
                     "- [Streamlit AppTest](https://docs.streamlit.io/1.54.0/develop/api-reference/app-testing/st.testing.v1.apptest): kiểm tra luồng ứng dụng.",
                     "- [scikit-learn classification_report](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html): chỉ số theo nhãn và quy ước zero_division.",
                     "", "Các tài liệu kỹ thuật không phải nguồn dữ kiện lịch sử. Không liệt kê nghiên cứu hay tài liệu chưa đọc như thể đã tham khảo.", ""]
    (reports / "sources.md").write_text("\n".join(source_lines), encoding="utf-8")
    b, p = summary["metrics"]["baseline"], summary["metrics"]["proposed"]
    intro = ("# Tóm tắt kết quả đo thực tế\n\n"
             f"87 ca đánh giá / {summary['question_count']} câu hỏi phân biệt. Câu trả lời tổng hợp có chủ đích; chưa có thẩm định nhãn độc lập.\n\n"
             "| Phương pháp | Accuracy | F1 macro | Tỷ lệ từ chối tự kết luận |\n|---|---:|---:|---:|\n"
             f"| Baseline | {b['accuracy']:.2%} | {b['f1_macro']:.4f} | {b['abstention_rate']:.2%} |\n"
             f"| Proposed | {p['accuracy']:.2%} | {p['f1_macro']:.4f} | {p['abstention_rate']:.2%} |\n\n"
             f"Thời điểm chạy: {summary['created_at']} (UTC). Các ca từ chối được tính sai, không bỏ khỏi mẫu số. "
             "Chưa kiểm định hiệu quả học tập hoặc độ chính xác trên dữ liệu ngoài thực tế. Không diễn giải precision 1.0 trên bộ nhỏ là bảo đảm không có false positive.\n\n"
             "Báo cáo đầy đủ, từng nhãn, ma trận, nhóm và ca thất bại bên dưới.\n\n")
    full = (reports / "experiment" / "ket_qua_thuc_nghiem.md").read_text(encoding="utf-8")
    (reports / "ket_qua_thuc_nghiem.md").write_text(intro + full, encoding="utf-8")
    technical = "# Báo cáo kỹ thuật FactGuard EDU\n\n"
    technical += "Tên học sinh, trường, lớp, giáo viên hướng dẫn: **chủ nhiệm đề tài tự điền**.\n\n"
    for filename in ["de_cuong.md", "phuong_phap.md", "ket_qua_thuc_nghiem.md", "gioi_han_nghien_cuu.md", "sources.md"]:
        technical += (reports / filename).read_text(encoding="utf-8") + "\n\n---\n\n"
    (reports / "bao_cao_ky_thuat.md").write_text(technical, encoding="utf-8")
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
    (ROOT / "requirements-lock.txt").write_text("# Measured Windows/Python 3.12 environment; includes development tools.\n" + freeze.stdout, encoding="utf-8")
    for name in ["run.bat", "setup.bat"]:
        path = ROOT / name
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    suite = ET.parse(reports / "pytest.xml").getroot().find("testsuite")
    if suite is None:
        raise ValueError("Missing pytest suite evidence")
    coverage = json.loads((reports / "coverage.json").read_text(encoding="utf-8"))["totals"]["percent_covered"]
    reproducibility = json.loads((reports / "reproducibility.json").read_text(encoding="utf-8"))
    commands = {
        "compile": [sys.executable, "-m", "compileall", "-q", "src", "app.py", "scripts"],
        "lint": [sys.executable, "-m", "ruff", "check", "."],
        "types": [sys.executable, "-m", "pyright"],
        "dependencies": [sys.executable, "-m", "pip", "check"],
    }
    checks = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        checks[name] = {"exit_code": result.returncode, "output": result.stdout.strip() + result.stderr.strip()}
    import urllib.request

    with urllib.request.urlopen("http://127.0.0.1:8501/_stcore/health", timeout=10) as response:
        health = {"status": response.status, "body": response.read().decode()}
    evidence = {"created_at": summary["created_at"], "python": platform.python_version(),
                "pytest": dict(suite.attrib), "coverage_percent": coverage, "checks": checks,
                "health": health, "reproducible_predictions": reproducibility["identical_predictions"],
                "browser_visual_review": "Not performed: browser origin permission rejected localhost navigation"}
    (reports / "verification.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Kết quả kiểm thử thực tế", "", f"Python {platform.python_version()} trên Windows. JUnit: reports/pytest.xml.",
             f"Pytest: {suite.get('tests')} ca, lỗi {suite.get('errors')}, thất bại {suite.get('failures')}, bỏ qua {suite.get('skipped')}.",
             f"Coverage src: {coverage:.2f}% (bao gồm UI); dữ liệu chi tiết: reports/coverage.json.", "",
             "| Cổng kiểm tra | Kết quả đã chạy |", "|---|---|"]
    for name, result in checks.items():
        lines.append(f"| {name} | {'PASS' if result['exit_code'] == 0 else 'FAIL'} |")
    lines += [f"| Streamlit localhost health | HTTP {health['status']} / {health['body']} |",
              f"| Tái lập dự đoán 2 lần | {'PASS' if reproducibility['identical_predictions'] else 'FAIL'}; {reproducibility['rows_per_run']} dòng/lần |", "",
              "## Phạm vi đã chạy", "",
              "- Dữ liệu: schema, trùng ID/câu hỏi, ngày sai, nguồn không tồn tại/chưa xác minh, trùng ca, kiểm soát tách sự kiện.",
              "- Kiểm chứng: ngày đúng/sai/thiếu, tên/địa điểm, ngoài kho, câu hỏi mở, phủ định, nhiều mốc, rỗng, nội dung dài.",
              "- Tệp: TXT/Markdown UTF-8, chunk dài, sai encoding, tệp rỗng/quá cỡ, PDF lỗi, PDF scan, PDF khóa, PDF văn bản có số trang.",
              "- Lưu trữ: SQLite đếm lượt thật, tách uploads khỏi lượt, tên tệp an toàn, chặn trùng hash.",
              "- Chỉ số: tính nhãn từ chối là sai; cùng dữ liệu cho hai phương pháp; CSV Unicode/BOM và chống công thức Excel; xuất JSON/Markdown.",
              "- AppTest: sáu trang, nút bắt đầu, form rỗng, năm tình huống demo, nút chạy thực nghiệm và bảng sinh từ kết quả thật.", "",
              "## Phần chưa được xác nhận", "",
              "Kiểm tra trực quan bằng trình duyệt/ảnh chụp: CHƯA THỰC HIỆN vì công cụ trình duyệt bị từ chối quyền mở origin localhost. Không dùng AppTest để tuyên bố đã kiểm tra pixel, tương phản hay màn hình máy chiếu.",
              "Chưa kiểm thử trên máy Windows khác hoặc Python khác, chưa chạy đo với kết nối mạng bị chặn ở cấp hệ điều hành, chưa khảo sát học sinh. Luồng core không gọi mạng; health và AppTest đã được chạy thật.", "",
              "Quét chuỗi bí mật được thực hiện riêng bằng rg; không có API key được yêu cầu hay lưu trong mã nguồn. Đây không phải kiểm toán bảo mật chuyên sâu.", ""]
    (reports / "kiem_thu.md").write_text("\n".join(lines), encoding="utf-8")
    code = [ROOT / "app.py", *sorted((ROOT / "src").glob("*.py")), ROOT / "reports" / "protocol.json"]
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in code}
    (reports / "code_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    shutil.copyfile(reports / "experiment" / "results.csv", reports / "ket_qua_chi_tiet.csv")
    print("Measured reports assembled. Verification:", {k: v["exit_code"] for k, v in checks.items()})
    if any(v["exit_code"] for v in checks.values()) or suite.get("failures") != "0" or suite.get("errors") != "0":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
