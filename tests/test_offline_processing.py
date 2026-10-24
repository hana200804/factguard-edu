import socket

import urllib3.util.connection

from src.claim_verifier import ClaimVerifier


def test_verification_needs_no_outbound_connection(monkeypatch, facts, retriever):
    def blocked(*args, **kwargs):
        raise AssertionError("Offline verification attempted an outbound network connection")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(urllib3.util.connection, "create_connection", blocked)
    engine = ClaimVerifier(facts, retriever)
    result = engine.verify("Kiểm chứng câu trả lời.", "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Quảng trường Ba Đình.")
    assert result.label == "supported" and len(result.checks) == 3
