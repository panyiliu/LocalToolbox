from tools.html2image import normalize_conversion_error


def test_normalize_conversion_error_with_playwright_keywords():
    normalized = normalize_conversion_error(Exception("Executable doesn't exist at /chromium"))
    assert "HTML 转图依赖不可用" in normalized


def test_normalize_conversion_error_generic():
    normalized = normalize_conversion_error(Exception("some random error"))
    assert normalized.startswith("转换失败:")
