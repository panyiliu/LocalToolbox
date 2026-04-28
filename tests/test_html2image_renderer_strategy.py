import pytest

from core.html2image_engine import PlaywrightRendererAdapter, RenderError, RenderPolicy


class _FakePage:
    def __init__(self, goto_error: Exception | None = None):
        self.url = "file:///app/uploads/demo.html"
        self._goto_error = goto_error

    def on(self, *_args, **_kwargs):
        return None

    def goto(self, *_args, **_kwargs):
        if self._goto_error:
            raise self._goto_error

    def wait_for_timeout(self, *_args, **_kwargs):
        return None

    def wait_for_load_state(self, *_args, **_kwargs):
        return None

    def evaluate(self, script):
        if script == "document.readyState":
            return "interactive"
        if "document.body ? document.body.scrollWidth" in script:
            return 1280
        if "document.body ? document.body.scrollHeight" in script:
            return 2000
        if "location.href" in script:
            return {
                "url": self.url,
                "title": "demo",
                "scrollWidth": 1280,
                "scrollHeight": 2000,
                "images": 0,
                "stylesheets": 2,
            }
        if "querySelectorAll" in script:
            return ["https://fonts.googleapis.com/css2?family=Inter"]
        return 0

    def set_viewport_size(self, *_args, **_kwargs):
        return None

    def screenshot(self, *_args, **_kwargs):
        return b"fake-image-bytes"


class _FakeBrowser:
    def __init__(self, page):
        self._page = page

    def new_page(self, **_kwargs):
        return self._page

    def close(self):
        return None


class _FakeChromium:
    def __init__(self, page):
        self._page = page

    def launch(self, **_kwargs):
        return _FakeBrowser(self._page)


class _FakePlaywright:
    def __init__(self, page):
        self.chromium = _FakeChromium(page)


class _FakePlaywrightContext:
    def __init__(self, page):
        self._playwright = _FakePlaywright(page)

    def __enter__(self):
        return self._playwright

    def __exit__(self, *_args):
        return False


def test_render_uses_partial_fallback_on_navigation_timeout(monkeypatch, tmp_path):
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body>demo</body></html>", encoding="utf-8")

    timeout_error = Exception("Page.goto: Timeout 30000ms exceeded.")
    fake_page = _FakePage(goto_error=timeout_error)

    monkeypatch.setattr(
        "core.html_export_engine.sync_playwright",
        lambda: _FakePlaywrightContext(fake_page),
    )

    renderer = PlaywrightRendererAdapter(
        policy=RenderPolicy(allow_partial_on_navigation_timeout=True)
    )

    image_bytes = renderer.render(str(html_path))
    assert image_bytes == b"fake-image-bytes"


def test_render_raises_structured_error_when_fallback_disabled(monkeypatch, tmp_path):
    html_path = tmp_path / "sample.html"
    html_path.write_text("<html><body>demo</body></html>", encoding="utf-8")

    timeout_error = Exception("Page.goto: Timeout 30000ms exceeded.")
    fake_page = _FakePage(goto_error=timeout_error)

    monkeypatch.setattr(
        "core.html_export_engine.sync_playwright",
        lambda: _FakePlaywrightContext(fake_page),
    )

    renderer = PlaywrightRendererAdapter(
        policy=RenderPolicy(allow_partial_on_navigation_timeout=False)
    )

    with pytest.raises(RenderError) as exc_info:
        renderer.render(str(html_path))

    assert exc_info.value.code == "navigation_timeout"
