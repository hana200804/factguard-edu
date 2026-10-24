"""Public verification API with a separate, authenticated research workspace."""
import base64
import csv
import json
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, Mount, Route
from starlette.staticfiles import StaticFiles

from src.annotation_study import consensus_cases
from src.claim_verifier import ClaimVerifier
from src.collected_workspace_v3 import (
    load_latest_study_v3,
    run_collected_study_v3,
    save_collected_study_v3,
    study_input_digest,
)
from src.collection import (
    QUESTION_BANK,
    TEMPLATE,
    eligible_events,
    import_cases,
    load_question_bank,
    parse_answers,
    read_table,
)
from src.hybrid_verifier import HYBRID_VERSION, HybridVerifier
from src.loader import DataError, load_evaluation, load_facts, load_sources, source_documents
from src.models import GOLD_LABELS
from src.nli import MODEL_DIR, MODEL_FILES, MODEL_REVISION, NliModel, shared_model
from src.retriever import Retriever
from src.review import ReviewRepository
from src.utils import PROJECT_ROOT, runtime_dir, utc_now
from src.v3_freeze import validate_v3_freeze


class ApiError(Exception):
    def __init__(self, status: int, message: str, details=None):
        self.status, self.message, self.details = status, message, details


async def payload(request: Request, limit: int = 65536) -> dict:
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise ApiError(415, "Gửi dữ liệu JSON UTF-8.")
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise ApiError(413, "Tệp hoặc nội dung vượt giới hạn cho phép.")
        chunks.append(chunk)
    try:
        result = json.loads(b"".join(chunks))
    except (ValueError, UnicodeError) as error:
        raise ApiError(400, "Dữ liệu JSON không hợp lệ.") from error
    if not isinstance(result, dict):
        raise ApiError(422, "Nội dung cần là một đối tượng JSON.")
    return result


def text(row, key, maximum=12000):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ApiError(422, f"Trường {key} cần văn bản từ 1 đến {maximum} ký tự.")
    return value


@lru_cache(maxsize=1)
def checked_freeze(signature):
    return validate_v3_freeze()


def ready_freeze():
    manifest = PROJECT_ROOT / "reports/research_v3/engine_freeze.json"
    try:
        record = json.loads(manifest.read_text(encoding="utf-8"))
        paths = [manifest, *(PROJECT_ROOT / name for name in record["files"]), *(MODEL_DIR / name for name in MODEL_FILES)]
        signature = tuple((str(path), path.stat().st_size, path.stat().st_mtime_ns) for path in paths)
        return checked_freeze(signature)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def create_app(root: Path | None = None, *, nli_loader=shared_model, freeze_check=ready_freeze, admin_key: str | None = None):
    root = root or runtime_dir() / "web"
    root.mkdir(parents=True, exist_ok=True)
    key_file = root / "admin-key.txt"
    if admin_key is None:
        admin_key = os.environ.get("FACTGUARD_ADMIN_KEY")
        if not admin_key:
            if not key_file.exists():
                key_file.write_text(secrets.token_urlsafe(32), encoding="ascii")
            admin_key = key_file.read_text(encoding="ascii").strip()
    if len(admin_key) < 24:
        raise ValueError("Mã quản trị cần ít nhất 24 ký tự.")
    repository = ReviewRepository(root)
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    documents = source_documents(base, sources, facts)
    development = load_evaluation(base / "evaluation.csv", facts)
    development = development.loc[development["split"] == "development"].copy()
    retriever = Retriever(documents)
    rules = ClaimVerifier(facts, retriever)
    events = eligible_events(facts, development)
    busy, limiter_lock = threading.Semaphore(1), threading.Lock()
    requests_by_ip = defaultdict(deque)

    class LazyNli(NliModel):
        def __init__(self):
            pass

        def score(self, pairs):
            return nli_loader().score(pairs)

    hybrid = HybridVerifier(facts, retriever, LazyNli())

    def authorise(request):
        supplied = request.headers.get("authorization", "")
        if not secrets.compare_digest(supplied.encode("utf-8"), ("Bearer " + admin_key).encode("utf-8")):
            raise ApiError(401, "Mã truy cập khu vực nghiên cứu không đúng hoặc chưa được nhập.")

    def limited(request):
        identity = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")
        now = time.monotonic()
        with limiter_lock:
            for key in list(requests_by_ip):
                if not requests_by_ip[key] or requests_by_ip[key][-1] < now - 60:
                    requests_by_ip.pop(key, None)
            queue = requests_by_ip[identity]
            while queue and queue[0] < now - 60:
                queue.popleft()
            if len(queue) >= 15 or sum(map(len, requests_by_ip.values())) >= 100:
                raise ApiError(429, "Đã có nhiều lượt kiểm chứng. Chờ một phút rồi thử lại.")
            queue.append(now)

    def exclusive(function):
        if not busy.acquire(blocking=False):
            raise ApiError(429, "Máy chủ đang đối chiếu một yêu cầu khác. Thử lại sau vài giây.")
        try:
            return function()
        finally:
            busy.release()

    async def health(request):
        return JSONResponse({"status": "ok", "version": HYBRID_VERSION, "facts": len(facts), "sources": len(sources),
                             "model_revision": MODEL_REVISION, "model_files_present": all((MODEL_DIR / name).is_file() for name in MODEL_FILES)})

    async def catalog(request):
        return JSONResponse({"facts": [asdict(fact) for fact in facts], "sources": list(sources.values())})

    async def verify(request):
        limited(request)
        data = await payload(request)
        question, answer = text(data, "question"), text(data, "answer")
        engine = data.get("engine", "compare")
        if engine not in {"rules", "hybrid", "compare"}:
            raise ApiError(422, "Phương pháp kiểm chứng không hợp lệ.")

        def execute():
            if engine != "rules" and not freeze_check():
                raise ApiError(503, "Dịch vụ NLI chưa sẵn sàng hoặc khác bản đóng băng. Bạn vẫn có thể dùng Luật v2.")
            result = {"id": uuid4().hex, "created_at": utc_now(), "question": question, "answer": answer,
                      "engine": engine, "results": {}, "purpose": "interactive; not automatically collected study data"}
            if engine in {"rules", "compare"}:
                result["results"]["v2"] = rules.verify(question, answer).to_dict()
            if engine in {"hybrid", "compare"}:
                result["results"]["v3"] = hybrid.verify(question, answer).to_dict()
            return result

        return JSONResponse(await run_in_threadpool(exclusive, execute))

    async def admin_status(request):
        authorise(request)
        collected, annotations = repository.collected_cases(), repository.annotations()
        accepted, pending = consensus_cases(collected, annotations)
        latest = load_latest_study_v3(root)
        return JSONResponse({"collected": collected, "annotations": annotations, "accepted": len(accepted), "pending": len(pending),
                             "events": sorted(events), "study": latest[2] if latest else None,
                             "study_stale": bool(latest and latest[2]["input_sha256"] != study_input_digest(collected, annotations))})

    async def add_case(request):
        authorise(request)
        row = await payload(request)
        event = text(row, "event_id", 100)
        if event not in events:
            raise ApiError(422, "Sự kiện không hợp lệ hoặc thuộc bộ phát triển.")
        identifier = repository.add_case(question=text(row, "question"), answer=text(row, "answer"),
                                         origin=text(row, "origin", 2000), submitter=text(row, "submitter", 100), event_id=event)
        return JSONResponse({"id": identifier, "message": "Đã lưu ca chưa có nhãn."}, status_code=201)

    async def annotation(request):
        authorise(request)
        row = await payload(request)
        case = next((case for case in repository.collected_cases() if case["id"] == row.get("case_id")), None)
        if case is None:
            raise ApiError(404, "Không tìm thấy ca thu thập.")
        evidence = row.get("evidence_ids", [])
        if not isinstance(evidence, list) or any(identifier not in {fact.id for fact in facts} for identifier in evidence):
            raise ApiError(422, "ID bằng chứng không có trong kho.")
        if row.get("label") not in GOLD_LABELS or row.get("confirmed") is not True:
            raise ApiError(422, "Chọn nhãn và xác nhận đã tự đọc bằng chứng.")
        repository.annotate(case_id=case["id"], question=case["question"], answer=case["answer"],
                            reviewer=text(row, "reviewer", 100), label=row["label"], evidence_ids=evidence,
                            note=text(row, "note", 3000), confirmed=True)
        return JSONResponse({"message": "Đã lưu phiếu và lịch sử thay đổi."}, status_code=201)

    def parse_sheet(path):
        bank = load_question_bank(QUESTION_BANK, events)
        collected, errors, blank = parse_answers(read_table(path), bank)
        if errors:
            raise ApiError(422, "CSV còn lỗi; chưa nhập dòng nào.", errors)
        return collected, blank

    async def preview_import(request):
        authorise(request)
        row = await payload(request, 8 * 1024 * 1024)
        try:
            content = base64.b64decode(text(row, "content_base64", 7 * 1024 * 1024), validate=True)
        except ValueError as error:
            raise ApiError(422, "Dữ liệu tệp không hợp lệ.") from error
        if len(content) > 5 * 1024 * 1024:
            raise ApiError(413, "CSV vượt giới hạn 5 MB.")
        identifier = uuid4().hex
        directory = root / "collection_imports"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"upload_{identifier}.csv"
        path.write_bytes(content)
        rows, blank = parse_sheet(path)
        return JSONResponse({"id": identifier, "valid": len(rows), "blank": blank,
                             "rows": [{key: row[key] for key in ["row", "qid", "question", "answer"]} for row in rows]})

    async def commit_import(request):
        authorise(request)
        identifier = request.path_params["identifier"]
        if not re.fullmatch(r"[a-f0-9]{32}", identifier):
            raise ApiError(404, "Không tìm thấy bản xem trước.")
        path = root / "collection_imports" / f"upload_{identifier}.csv"
        if not path.is_file():
            raise ApiError(404, "Không tìm thấy bản xem trước; tải lại CSV.")
        rows, _ = parse_sheet(path)
        log = import_cases(repository, rows)
        destination = path.parent / f"import_{uuid4().hex}.csv"
        try:
            with destination.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, ["row", "qid", "case_id", "status"])
                writer.writeheader()
                writer.writerows(log)
        except OSError as error:
            raise ApiError(500, "Các ca đã được xử lý nhưng chưa ghi được nhật ký. Kiểm tra hàng đợi trước khi nhập lại.") from error
        return JSONResponse({"added": sum(row["status"] == "đã nhập" for row in log), "log": log})

    async def template(request):
        authorise(request)
        return Response(TEMPLATE.read_bytes(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="mau_ghi_cau_tra_loi.csv"'})

    async def run_study(request):
        authorise(request)

        def execute():
            frame, summary = run_collected_study_v3(facts, documents, development, repository.collected_cases(), repository.annotations(), LazyNli())
            save_collected_study_v3(frame, summary, root)
            return summary

        return JSONResponse(await run_in_threadpool(exclusive, execute))

    async def study_file(request):
        authorise(request)
        name = request.path_params["name"]
        media = {"report.md": "text/markdown", "summary.json": "application/json", "results.csv": "text/csv"}
        if name not in media:
            raise ApiError(404, "Tệp xuất không hợp lệ.")
        latest = load_latest_study_v3(root)
        if latest is None:
            raise ApiError(404, "Chưa có kết quả đánh giá.")
        return Response((latest[0] / name).read_bytes(), media_type=media[name], headers={"Content-Disposition": f'attachment; filename="{name}"'})

    async def api_error(request, error):
        return JSONResponse({"error": error.message, "details": error.details}, status_code=error.status)

    async def data_error(request, error):
        return JSONResponse({"error": str(error)}, status_code=422)

    async def unavailable(request, error):
        return JSONResponse({"error": "Dịch vụ chưa hoàn tất yêu cầu. Thử lại sau hoặc liên hệ người quản trị."}, status_code=503)

    origins = os.environ.get("FACTGUARD_WEB_ORIGINS", "https://factguard-edu-hana-2026.choicelamp8.chatgpt.site,http://127.0.0.1:8765,http://localhost:8765").split(",")
    routes: list[BaseRoute] = [Route("/api/health", health), Route("/api/catalog", catalog), Route("/api/verify", verify, methods=["POST"]),
              Route("/api/admin/status", admin_status), Route("/api/admin/cases", add_case, methods=["POST"]),
              Route("/api/admin/annotations", annotation, methods=["POST"]), Route("/api/admin/imports", preview_import, methods=["POST"]),
              Route("/api/admin/imports/{identifier}/commit", commit_import, methods=["POST"]), Route("/api/admin/template", template),
              Route("/api/admin/study", run_study, methods=["POST"]), Route("/api/admin/study/{name}", study_file)]
    if (PROJECT_ROOT / "web").is_dir():
        routes.append(Mount("/", StaticFiles(directory=PROJECT_ROOT / "web", html=True)))
    app = Starlette(routes=routes, middleware=[Middleware(CORSMiddleware, allow_origins=origins,
                    allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])],
                    exception_handlers={ApiError: api_error, DataError: data_error, ImportError: unavailable, RuntimeError: unavailable, OSError: unavailable})
    app.state.repository = repository
    return app
