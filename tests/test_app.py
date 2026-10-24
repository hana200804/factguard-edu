import pytest
from streamlit.testing.v1 import AppTest

from src.ui import PAGE_NAMES
from src.utils import PROJECT_ROOT


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("FACTGUARD_RUNTIME_DIR", str(tmp_path))
    return AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=20).run()


@pytest.mark.parametrize("page", PAGE_NAMES)
def test_all_pages_render_without_exception(app, page):
    app.radio(key="navigation").set_value(page).run()
    assert not app.exception


def test_start_button_navigates(app):
    next(button for button in app.button if button.label == "Bắt đầu kiểm chứng").click().run()
    assert not app.exception
    assert app.radio(key="navigation").value == PAGE_NAMES[1]


def test_verification_form_and_samples(app):
    app.radio(key="navigation").set_value(PAGE_NAMES[1]).run()
    app.button[0].click().run()
    assert app.warning
    for sample, expected in [("Mốc thời gian đúng", "Có bằng chứng hỗ trợ"),
                             ("Mốc thời gian sai", "Mâu thuẫn với bằng chứng"),
                             ("Chưa đủ thông tin", "Chưa đủ bằng chứng"),
                             ("Câu hỏi ngoài kho", "Chưa đủ bằng chứng"),
                             ("Câu hỏi cần tự phân tích", "Không thể tự động kết luận")]:
        app.selectbox(key="sample").set_value(sample).run()
        next(button for button in app.button if button.label == "Kiểm chứng").click().run()
        assert not app.exception
        assert app.session_state["last_result"]["verdict"].label
        result_messages = [node.value for nodes in [app.success, app.error, app.warning, app.info] for node in nodes]
        assert any(expected in message for message in result_messages)


def test_experiment_button_generates_actual_results(app):
    app.radio(key="navigation").set_value(PAGE_NAMES[4]).run()
    next(button for button in app.button if button.label == "Chạy thực nghiệm").click().run()
    assert not app.exception
    assert any("Đã chạy xong" in s.value for s in app.success)
    assert len(app.dataframe) >= 4
