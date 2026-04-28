import pytest

from core.html_export_engine import ExportError, PdfExportRequest, PlaywrightHtmlExportEngine


class _FakePage:
    def __init__(self, auto_selector=".resume"):
        self.url = "file:///app/uploads/demo.html"
        self.auto_selector = auto_selector
        self.media = None
        self.style_tags = []
        self.pdf_calls = []

    def on(self, *_args, **_kwargs):
        return None

    def goto(self, *_args, **_kwargs):
        return None

    def wait_for_timeout(self, *_args, **_kwargs):
        return None

    def emulate_media(self, media):
        self.media = media

    def add_style_tag(self, content):
        self.style_tags.append(content)

    def evaluate(self, script, arg=None):
        if "document.readyState" == script:
            return "interactive"
        if "document.body ? document.body.scrollWidth" in script:
            return 1280
        if "document.body ? document.body.scrollHeight" in script:
            return 2200
        if "location.href" in script:
            return {
                "url": self.url,
                "title": "demo",
                "scrollWidth": 1280,
                "scrollHeight": 2200,
                "images": 0,
                "stylesheets": 2,
            }
        if "querySelectorAll('link[href],script[src],img[src]')" in script:
            return ["https://fonts.googleapis.com/css2?family=Inter"]
        if "for (const selector of candidates)" in script:
            return self.auto_selector
        if "const el = document.querySelector(selector);" in script:
            if self.auto_selector is None:
                return None
            return {"width": 800, "height": 1200}
        return None

    def pdf(self, **kwargs):
        self.pdf_calls.append(kwargs)
        return b"%PDF-1.4"


class _FakeBrowser:
    def __init__(self, page):
        self.page = page

    def new_page(self, **_kwargs):
        return self.page

    def close(self):
        return None


class _FakeChromium:
    def __init__(self, page):
        self.page = page

    def launch(self, **_kwargs):
        return _FakeBrowser(self.page)


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


def test_render_pdf_single_page_uses_measured_dimensions(monkeypatch, tmp_path):
    html_path = tmp_path / "demo.html"
    html_path.write_text("<html><body><main>demo</main></body></html>", encoding="utf-8")
    fake_page = _FakePage(auto_selector=".resume")

    monkeypatch.setattr(
        "core.html_export_engine.sync_playwright",
        lambda: _FakePlaywrightContext(fake_page),
    )

    engine = PlaywrightHtmlExportEngine()
    pdf_bytes = engine.render_pdf(PdfExportRequest(html_path=str(html_path), mode="single_page"))

    assert pdf_bytes.startswith(b"%PDF")
    assert fake_page.media == "screen"
    assert fake_page.pdf_calls[0]["width"] == "824px"
    assert fake_page.pdf_calls[0]["height"] == "1224px"
    assert fake_page.pdf_calls[0]["page_ranges"] == "1"


def test_render_pdf_paged_uses_a4_defaults(monkeypatch, tmp_path):
    html_path = tmp_path / "demo.html"
    html_path.write_text("<html><body><main>demo</main></body></html>", encoding="utf-8")
    fake_page = _FakePage(auto_selector="body")

    monkeypatch.setattr(
        "core.html_export_engine.sync_playwright",
        lambda: _FakePlaywrightContext(fake_page),
    )

    engine = PlaywrightHtmlExportEngine()
    pdf_bytes = engine.render_pdf(PdfExportRequest(html_path=str(html_path), mode="paged", media="print", landscape=True))

    assert pdf_bytes.startswith(b"%PDF")
    assert fake_page.media == "print"
    assert fake_page.pdf_calls[0]["format"] == "A4"
    assert fake_page.pdf_calls[0]["landscape"] is True


def test_render_pdf_raises_structured_error_when_content_not_found(monkeypatch, tmp_path):
    html_path = tmp_path / "demo.html"
    html_path.write_text("<html><body><main>demo</main></body></html>", encoding="utf-8")
    fake_page = _FakePage(auto_selector=None)

    monkeypatch.setattr(
        "core.html_export_engine.sync_playwright",
        lambda: _FakePlaywrightContext(fake_page),
    )

    engine = PlaywrightHtmlExportEngine()

    with pytest.raises(ExportError) as exc_info:
        engine.render_pdf(PdfExportRequest(html_path=str(html_path), mode="single_page"))

    assert exc_info.value.code == "content_not_found"
