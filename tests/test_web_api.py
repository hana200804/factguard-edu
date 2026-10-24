"""Web/API tests use temporary data and fake inference, never publish study fixtures."""
import base64
import csv
import io
from datetime import date

import pytest
from starlette.testclient import TestClient

from src import annotation_study_v3, collected_workspace_v3
from src.collection import QUESTION_BANK, TEMPLATE_COLUMNS, read_table
from src.nli import NliScore
from src.web_api import create_app

TEST_KEY = "software-test-admin-key-123456789"
HEADERS = {"Authorization": "Bearer " + TEST_KEY}


class FakeNli:
    def __init__(self):
        self.calls = []

    def score(self, pairs):
        self.calls.extend(pairs)
        return [NliScore(.95, .03, .02) for _ in pairs]


@pytest.fixture
def client(tmp_path, monkeypatch):
    fake = FakeNli()
    monkeypatch.setattr(collected_workspace_v3, "validate_v3_freeze", lambda: True)
    monkeypatch.setattr(annotation_study_v3, "validate_v3_freeze", lambda: True)
    app = create_app(tmp_path, nli_loader=lambda: fake, freeze_check=lambda: True, admin_key=TEST_KEY)
    app.state.fake = fake
    with TestClient(app) as connection:
        yield connection


def add_case(client):
    result = client.post("/api/admin/cases", headers=HEADERS, json={
        "question": "Tuyên ngôn Độc lập được đọc vào ngày nào?", "answer": "Ngày 2/9/1945.",
        "event_id": "independence1945", "origin": "Software fixture, not a chatbot response", "submitter": "Software tester"})
    assert result.status_code == 201
    return result.json()["id"]


def test_public_catalog_and_verification_never_collect_user_cases(client):
    assert client.get("/api/health").json()["facts"] == 33
    catalog = client.get("/api/catalog").json()
    assert len(catalog["facts"]) == 33 and len(catalog["sources"]) == 7
    response = client.post("/api/verify", json={"question": "Kiểm chứng câu trả lời.",
                           "answer": "Chiến dịch Điện Biên Phủ diễn ra tại Điện Biên Phủ.", "engine": "compare"})
    assert response.status_code == 200
    assert response.json()["results"]["v2"]["label"] == "insufficient"
    assert response.json()["results"]["v3"]["label"] == "supported" and client.app.state.fake.calls
    assert client.app.state.repository.collected_cases() == []
    assert client.app.state.repository.annotations() == []


@pytest.mark.parametrize("body", [[], {"question": 5, "answer": "A"}, {"question": "Q", "answer": "A", "engine": "bad"},
                                  {"question": "Q", "answer": "x" * 12001}])
def test_verify_rejects_invalid_inputs(client, body):
    assert client.post("/api/verify", json=body).status_code == 422


def test_json_size_format_and_origin_boundaries(client):
    assert client.post("/api/verify", content="{}", headers={"Content-Type": "text/plain"}).status_code == 415
    assert client.post("/api/verify", content="{bad", headers={"Content-Type": "application/json"}).status_code == 400
    assert client.post("/api/verify", json={"answer": "x" * 70000}).status_code == 413
    assert "access-control-allow-origin" not in client.get("/api/health", headers={"Origin": "https://unrelated.example"}).headers
    allowed = "https://factguard-edu-hana-2026.choicelamp8.chatgpt.site"
    assert client.get("/api/health", headers={"Origin": allowed}).headers["access-control-allow-origin"] == allowed


def test_research_endpoints_require_key_and_do_not_expose_data(client):
    add_case(client)
    assert client.get("/api/admin/status").status_code == 401
    assert client.get("/api/admin/template").status_code == 401
    assert client.post("/api/admin/cases", json={}).status_code == 401
    assert client.post("/api/admin/study", json={}).status_code == 401
    assert client.get("/api/admin/status", headers=HEADERS).json()["accepted"] == 0
    assert client.post("/api/admin/cases", headers=HEADERS, json={"event_id": "departure1911"}).status_code == 422


def test_two_ratings_to_five_method_report_and_stale_result(client):
    identifier = add_case(client)
    for reviewer in ["Software test rater 1", "Software test rater 2"]:
        response = client.post("/api/admin/annotations", headers=HEADERS, json={"case_id": identifier, "reviewer": reviewer,
                               "label": "supported", "evidence_ids": ["F001"], "note": "Software annotation fixture.", "confirmed": True})
        assert response.status_code == 201
    assert client.get("/api/admin/status", headers=HEADERS).json()["accepted"] == 1
    response = client.post("/api/admin/study", headers=HEADERS, json={})
    assert response.status_code == 200 and response.json()["cases"] == 1
    assert len(response.json()["metrics"]) == 5
    report = client.get("/api/admin/study/report.md", headers=HEADERS)
    assert report.status_code == 200 and "đánh giá 1 ca đồng thuận" in report.text
    assert client.get("/api/admin/study/unknown.txt", headers=HEADERS).status_code == 404
    client.post("/api/admin/annotations", headers=HEADERS, json={"case_id": identifier, "reviewer": "Software test rater 2",
                "label": "insufficient", "evidence_ids": [], "note": "Software label edited to test stale results.", "confirmed": True})
    status = client.get("/api/admin/status", headers=HEADERS).json()
    assert status["accepted"] == 0 and status["study_stale"]


def test_annotation_validation_does_not_invent_ratings(client):
    identifier = add_case(client)
    row = {"case_id": identifier, "reviewer": "Software test rater", "label": "supported", "evidence_ids": ["BAD"],
           "note": "Software fixture.", "confirmed": True}
    assert client.post("/api/admin/annotations", headers=HEADERS, json=row).status_code == 422
    row.update(evidence_ids=["F001"], confirmed=False)
    assert client.post("/api/admin/annotations", headers=HEADERS, json=row).status_code == 422
    assert client.app.state.repository.annotations() == []


def sheet_bytes(invalid=False):
    question = read_table(QUESTION_BANK)[0]
    row = {"ma_cau_hoi": question["ma_cau_hoi"], "ma_su_kien": question["ma_su_kien"], "cau_hoi": question["cau_hoi"],
           "cong_cu": "Software test tool", "phien_ban": "Software fixture", "ngay_lay": date.today().isoformat(),
           "kieu_lenh": "ngan_gon", "nguoi_thu_thap": "Software tester", "cau_tra_loi": "Ngày 2/9/1945.", "ghi_chu": "Software fixture"}
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, TEMPLATE_COLUMNS)
    writer.writeheader()
    writer.writerow(row)
    if invalid:
        writer.writerow({**row, "phien_ban": "", "cau_tra_loi": "Software response to test invalid rows."})
    return handle.getvalue().encode("utf-8-sig")


def test_import_preview_is_blind_and_commit_is_idempotent(client):
    result = client.post("/api/admin/imports", headers=HEADERS, json={"content_base64": base64.b64encode(sheet_bytes()).decode()})
    assert result.status_code == 200
    preview = result.json()
    assert preview["valid"] == 1 and set(preview["rows"][0]) == {"row", "qid", "question", "answer"}
    assert client.app.state.repository.collected_cases() == []
    target = "/api/admin/imports/" + preview["id"] + "/commit"
    assert client.post(target, headers=HEADERS, json={}).json()["added"] == 1
    assert client.post(target, headers=HEADERS, json={}).json()["added"] == 0
    assert client.app.state.repository.annotations() == [] and client.app.state.repository.verify_audit()


def test_import_one_invalid_row_blocks_all_and_limits_upload(client):
    result = client.post("/api/admin/imports", headers=HEADERS, json={"content_base64": base64.b64encode(sheet_bytes(True)).decode()})
    assert result.status_code == 422 and result.json()["details"]
    assert client.app.state.repository.collected_cases() == []
    large = base64.b64encode(b"x" * (5 * 1024 * 1024 + 1)).decode()
    assert client.post("/api/admin/imports", headers=HEADERS, json={"content_base64": large}).status_code == 413


def test_public_rate_limit_prevents_unbounded_inference(client):
    statuses = [client.post("/api/verify", json={"question": "Q", "answer": "A", "engine": "rules"}).status_code for _ in range(16)]
    assert statuses[:15] == [200] * 15 and statuses[-1] == 429


def test_static_product_routes_and_no_private_files(client):
    assert "FactGuard EDU" in client.get("/").text
    assert client.get("/app.js").status_code == 200
    assert client.get("/runtime/web/admin-key.txt").status_code == 404
    assert client.get("/src/nli.py").status_code == 404
