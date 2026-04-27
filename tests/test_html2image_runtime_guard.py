from core.html2image_engine import RenderDiagnostics, RenderError
from tools import html2image
from tools.html2image import normalize_conversion_error


def test_normalize_conversion_error_with_playwright_keywords():
    normalized = normalize_conversion_error(Exception("Executable doesn't exist at /chromium"))
    assert "HTML 转图依赖不可用" in normalized


def test_normalize_conversion_error_generic():
    normalized = normalize_conversion_error(Exception("some random error"))
    assert normalized.startswith("转换失败:")


def test_normalize_conversion_error_navigation_timeout():
    diagnostics = RenderDiagnostics(
        elapsed_ms=30000,
        page_url="file:///app/uploads/demo.html",
        ready_state="interactive",
        html_file_size=1024,
        html_metrics={},
        resource_hosts=["fonts.googleapis.com"],
        external_resource_count=1,
        failed_requests=[],
        http_errors=[],
        console_errors=[],
    )
    normalized = normalize_conversion_error(RenderError("navigation_timeout", "timeout", diagnostics))
    assert "外链资源加载超时" in normalized


def test_check_playwright_chromium_cached(monkeypatch):
    calls = {"count": 0}

    class _Result:
        ok = True
        message = "Chromium 可用"

    def fake_check():
        calls["count"] += 1
        return _Result()

    monkeypatch.setattr(html2image, "check_playwright_chromium", fake_check)
    monkeypatch.setattr(html2image, "_playwright_check_cached_result", None)
    monkeypatch.setattr(html2image, "_playwright_check_cached_at", 0.0)

    first = html2image.check_playwright_chromium_cached()
    second = html2image.check_playwright_chromium_cached()

    assert first.ok is True
    assert second.ok is True
    assert calls["count"] == 1
