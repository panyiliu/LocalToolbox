import os
import time
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from core.logger import get_logger


DEFAULT_CONTENT_SELECTORS = [
    ".resume",
    "main",
    "article",
    "#app",
    ".container",
    ".page",
    ".document",
]


@dataclass
class ExportPolicy:
    wait_until: str = "domcontentloaded"
    goto_timeout_ms: int = 15000
    settle_time_ms: int = 800
    use_networkidle: bool = False
    networkidle_timeout_ms: int = 2000
    allow_partial_on_navigation_timeout: bool = True
    screenshot_timeout_ms: int = 10000
    pdf_timeout_ms: int = 10000
    viewport_width: int = 1600
    viewport_height: int = 900


@dataclass
class ExportDiagnostics:
    elapsed_ms: int
    page_url: str
    ready_state: str
    html_file_size: int
    html_metrics: dict
    resource_hosts: list[str]
    external_resource_count: int
    failed_requests: list[dict]
    http_errors: list[dict]
    console_errors: list[str]
    image_sources: list[dict]
    content_selector: str | None = None


class ExportError(Exception):
    def __init__(self, code: str, message: str, diagnostics: ExportDiagnostics):
        super().__init__(message)
        self.code = code
        self.diagnostics = diagnostics

    def __str__(self) -> str:
        return f"{self.code}: {super().__str__()}"


@dataclass
class PdfExportRequest:
    html_path: str
    mode: str = "single_page"
    media: str = "screen"
    remove_outer_background: bool = True
    print_background: bool = True
    landscape: bool = False


class PlaywrightHtmlExportEngine:
    def __init__(self, policy: ExportPolicy | None = None, logger_name: str = "html.export.renderer"):
        self.policy = policy or ExportPolicy()
        self.logger = get_logger(logger_name)

    @staticmethod
    def _build_file_url(abs_html_path: str) -> str:
        normalized = abs_html_path.replace("\\", "/")
        return f"file://{normalized}"

    @staticmethod
    def _classify_error(exc: Exception) -> str:
        message = str(exc).lower()
        if "page.goto" in message and "timeout" in message:
            return "navigation_timeout"
        if "networkidle" in message and "timeout" in message:
            return "network_idle_timeout"
        if "content_not_found" in message:
            return "content_not_found"
        if "pdf" in message:
            return "pdf_export_failed"
        if "screenshot" in message:
            return "screenshot_failed"
        return "render_failed"

    @staticmethod
    def _measure_page_dimensions(page) -> tuple[int, int]:
        width = page.evaluate("document.body ? document.body.scrollWidth : 1280")
        height = page.evaluate("document.body ? document.body.scrollHeight : 720")
        return int(width), int(height)

    @staticmethod
    def _collect_page_diagnostics(page, elapsed_ms: int, html_file_size: int, failed_requests: list[dict], response_errors: list[dict], console_errors: list[str]) -> ExportDiagnostics:
        ready_state = "unknown"
        html_metrics: dict = {}
        external_resources: list[str] = []
        image_sources: list[dict] = []
        try:
            ready_state = page.evaluate("document.readyState")
            html_metrics = page.evaluate("""() => ({
                url: location.href,
                title: document.title,
                scrollWidth: document.body ? document.body.scrollWidth : -1,
                scrollHeight: document.body ? document.body.scrollHeight : -1,
                images: document.images ? document.images.length : 0,
                stylesheets: document.styleSheets ? document.styleSheets.length : 0
            })""")
            external_resources = page.evaluate("""() => {
                const urls = [];
                for (const el of document.querySelectorAll('link[href],script[src],img[src]')) {
                    const raw = el.getAttribute('href') || el.getAttribute('src');
                    if (!raw) continue;
                    if (raw.startsWith('http://') || raw.startsWith('https://')) {
                        urls.push(raw);
                    }
                }
                return urls.slice(0, 30);
            }""")
            image_sources = page.evaluate("""() => {
                const imgs = Array.from(document.images || []);
                return imgs.slice(0, 20).map((img, index) => ({
                    index,
                    src: img.currentSrc || img.src || '',
                    complete: Boolean(img.complete),
                    naturalWidth: Number(img.naturalWidth || 0),
                    naturalHeight: Number(img.naturalHeight || 0),
                    clientWidth: Number(img.clientWidth || 0),
                    clientHeight: Number(img.clientHeight || 0),
                    loading: img.getAttribute('loading') || '',
                    crossOrigin: img.getAttribute('crossorigin') || '',
                    referrerPolicy: img.getAttribute('referrerpolicy') || ''
                }));
            }""")
        except Exception:
            pass

        resource_hosts = sorted({urlparse(url).netloc for url in external_resources if urlparse(url).netloc})
        return ExportDiagnostics(
            elapsed_ms=elapsed_ms,
            page_url=getattr(page, "url", ""),
            ready_state=ready_state,
            html_file_size=html_file_size,
            html_metrics=html_metrics,
            resource_hosts=resource_hosts,
            external_resource_count=len(external_resources),
            failed_requests=failed_requests[:20],
            http_errors=response_errors[:20],
            console_errors=console_errors[:20],
            image_sources=image_sources,
        )

    @staticmethod
    def _auto_detect_content_selector(page) -> str:
        script = """(candidates) => {
            if (!document.body) return null;
            for (const selector of candidates) {
                const el = document.querySelector(selector);
                if (!el) continue;
                const rect = el.getBoundingClientRect();
                const area = Math.max(rect.width, el.scrollWidth || 0) * Math.max(rect.height, el.scrollHeight || 0);
                if (area > 0) return selector;
            }
            return document.body ? 'body' : null;
        }"""
        selector = page.evaluate(script, DEFAULT_CONTENT_SELECTORS)
        if not selector:
            raise ValueError("content_not_found: unable to detect export root")
        return selector

    @staticmethod
    def _measure_content_dimensions(page, content_selector: str) -> dict:
        script = """([selector]) => {
            const el = document.querySelector(selector);
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {
                width: Math.max(Math.ceil(rect.width), Math.ceil(el.scrollWidth || 0), Math.ceil(el.offsetWidth || 0)),
                height: Math.max(Math.ceil(rect.height), Math.ceil(el.scrollHeight || 0), Math.ceil(el.offsetHeight || 0))
            };
        }"""
        dims = page.evaluate(script, [content_selector])
        if not dims:
            raise ValueError(f"content_not_found: selector={content_selector}")
        return dims

    @staticmethod
    def _add_background_reset(page):
        page.add_style_tag(content="""
            html, body {
                background: white !important;
                margin: 0 !important;
                padding: 0 !important;
            }
        """)

    @staticmethod
    def _add_single_page_styles(page, content_selector: str, pdf_width: int, pdf_height: int):
        page.add_style_tag(content=f"""
            @page {{
                size: {pdf_width}px {pdf_height}px;
                margin: 0;
            }}

            html, body {{
                width: {pdf_width}px !important;
                height: {pdf_height}px !important;
                overflow: visible !important;
                background: white !important;
            }}

            body {{
                display: block !important;
            }}

            {content_selector} {{
                margin: 0 auto !important;
                box-shadow: none !important;
                border-radius: 0 !important;
            }}
        """)

    def _log_failure(self, error_code: str, exc: Exception, diagnostics: ExportDiagnostics):
        self.logger.error(
            f"[render-failed] code={error_code} elapsed_ms={diagnostics.elapsed_ms} error={exc} "
            f"page_url={diagnostics.page_url} ready_state={diagnostics.ready_state} "
            f"html_file_size={diagnostics.html_file_size} html_metrics={diagnostics.html_metrics} "
            f"resource_hosts={diagnostics.resource_hosts} "
            f"external_resource_count={diagnostics.external_resource_count} "
            f"failed_requests={diagnostics.failed_requests} "
            f"http_errors={diagnostics.http_errors} console_errors={diagnostics.console_errors} "
            f"content_selector={diagnostics.content_selector} image_sources={diagnostics.image_sources}"
        )

    def _log_pdf_diagnostics(self, stage: str, diagnostics: ExportDiagnostics):
        self.logger.info(
            f"[pdf-diagnostics] stage={stage} elapsed_ms={diagnostics.elapsed_ms} "
            f"page_url={diagnostics.page_url} ready_state={diagnostics.ready_state} "
            f"html_metrics={diagnostics.html_metrics} content_selector={diagnostics.content_selector} "
            f"resource_hosts={diagnostics.resource_hosts} failed_requests={diagnostics.failed_requests} "
            f"http_errors={diagnostics.http_errors} console_errors={diagnostics.console_errors} "
            f"image_sources={diagnostics.image_sources}"
        )

    def render_image(self, html_path: str) -> bytes:
        abs_html_path = os.path.abspath(html_path)
        file_url = self._build_file_url(abs_html_path)
        html_file_size = os.path.getsize(abs_html_path) if os.path.exists(abs_html_path) else -1
        started_at = time.perf_counter()
        failed_requests = []
        response_errors = []
        console_errors = []

        self.logger.info(
            f"[render-start] html_path={html_path} abs_html_path={abs_html_path} "
            f"file_size={html_file_size} file_url={file_url}"
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": self.policy.viewport_width, "height": self.policy.viewport_height},
                device_scale_factor=1,
            )

            def on_request_failed(request):
                failure = request.failure
                reason = failure.get("errorText") if failure else "unknown"
                failed_requests.append({
                    "url": request.url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                    "reason": reason,
                })

            def on_response(response):
                status = response.status
                if status >= 400:
                    response_errors.append({
                        "url": response.url,
                        "status": status,
                        "status_text": response.status_text,
                    })

            def on_console(message):
                if message.type == "error":
                    console_errors.append(message.text)

            page.on("requestfailed", on_request_failed)
            page.on("response", on_response)
            page.on("console", on_console)

            try:
                page.goto(file_url, wait_until=self.policy.wait_until, timeout=self.policy.goto_timeout_ms)
                goto_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                self.logger.info(f"[render-goto-ok] elapsed_ms={goto_elapsed_ms} url={page.url}")

                if self.policy.settle_time_ms > 0:
                    page.wait_for_timeout(self.policy.settle_time_ms)

                if self.policy.use_networkidle:
                    page.wait_for_load_state("networkidle", timeout=self.policy.networkidle_timeout_ms)
                    idle_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    self.logger.info(f"[render-networkidle-ok] elapsed_ms={idle_elapsed_ms} url={page.url}")

                width, height = self._measure_page_dimensions(page)
                page.set_viewport_size({"width": min(width, 3000), "height": min(height, 10000)})

                screenshot_bytes = page.screenshot(full_page=True, timeout=self.policy.screenshot_timeout_ms)
                total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                self.logger.info(
                    f"[render-success] elapsed_ms={total_elapsed_ms} width={width} height={height} "
                    f"screenshot_bytes={len(screenshot_bytes)} failed_requests={len(failed_requests)} "
                    f"http_errors={len(response_errors)} console_errors={len(console_errors)}"
                )
                return screenshot_bytes
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                diagnostics = self._collect_page_diagnostics(
                    page=page,
                    elapsed_ms=elapsed_ms,
                    html_file_size=html_file_size,
                    failed_requests=failed_requests,
                    response_errors=response_errors,
                    console_errors=console_errors,
                )
                error_code = self._classify_error(exc)
                self._log_failure(error_code, exc, diagnostics)

                if error_code == "navigation_timeout" and self.policy.allow_partial_on_navigation_timeout:
                    self.logger.warning("[render-fallback] navigation timeout, attempt partial screenshot")
                    width, height = self._measure_page_dimensions(page)
                    page.set_viewport_size({"width": min(width, 3000), "height": min(height, 10000)})
                    screenshot_bytes = page.screenshot(full_page=True, timeout=self.policy.screenshot_timeout_ms)
                    total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    self.logger.info(
                        f"[render-fallback-success] elapsed_ms={total_elapsed_ms} width={width} "
                        f"height={height} screenshot_bytes={len(screenshot_bytes)}"
                    )
                    return screenshot_bytes

                raise ExportError(error_code, str(exc), diagnostics) from exc
            finally:
                browser.close()

    def render_pdf(self, request: PdfExportRequest) -> bytes:
        abs_html_path = os.path.abspath(request.html_path)
        file_url = self._build_file_url(abs_html_path)
        html_file_size = os.path.getsize(abs_html_path) if os.path.exists(abs_html_path) else -1
        started_at = time.perf_counter()
        failed_requests = []
        response_errors = []
        console_errors = []

        self.logger.info(
            f"[pdf-start] html_path={request.html_path} abs_html_path={abs_html_path} "
            f"file_size={html_file_size} file_url={file_url} mode={request.mode}"
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": self.policy.viewport_width, "height": self.policy.viewport_height},
                device_scale_factor=1,
            )

            def on_request_failed(request_obj):
                failure = request_obj.failure
                reason = failure.get("errorText") if failure else "unknown"
                failed_requests.append({
                    "url": request_obj.url,
                    "method": request_obj.method,
                    "resource_type": request_obj.resource_type,
                    "reason": reason,
                })

            def on_response(response):
                status = response.status
                if status >= 400:
                    response_errors.append({
                        "url": response.url,
                        "status": status,
                        "status_text": response.status_text,
                    })

            def on_console(message):
                if message.type == "error":
                    console_errors.append(message.text)

            page.on("requestfailed", on_request_failed)
            page.on("response", on_response)
            page.on("console", on_console)

            try:
                page.goto(file_url, wait_until=self.policy.wait_until, timeout=self.policy.goto_timeout_ms)
                if self.policy.settle_time_ms > 0:
                    page.wait_for_timeout(self.policy.settle_time_ms)

                page.emulate_media(media=request.media)

                if request.remove_outer_background:
                    self._add_background_reset(page)

                content_selector = None
                if request.mode == "single_page":
                    content_selector = self._auto_detect_content_selector(page)
                    dims = self._measure_content_dimensions(page, content_selector)
                    pdf_width = int(dims["width"]) + 24
                    pdf_height = int(dims["height"]) + 24
                    pre_pdf_diagnostics = self._collect_page_diagnostics(
                        page=page,
                        elapsed_ms=int((time.perf_counter() - started_at) * 1000),
                        html_file_size=html_file_size,
                        failed_requests=failed_requests,
                        response_errors=response_errors,
                        console_errors=console_errors,
                    )
                    pre_pdf_diagnostics.content_selector = content_selector
                    self.logger.info(
                        f"[pdf-layout] mode=single_page content_selector={content_selector} "
                        f"content_dims={dims} pdf_width={pdf_width} pdf_height={pdf_height} "
                        f"remove_outer_background={request.remove_outer_background} "
                        f"print_background={request.print_background} landscape={request.landscape} "
                        f"media={request.media}"
                    )
                    self._log_pdf_diagnostics("before-pdf-single-page", pre_pdf_diagnostics)
                    self._add_single_page_styles(page, content_selector, pdf_width, pdf_height)
                    page.wait_for_timeout(300)
                    pdf_bytes = page.pdf(
                        print_background=request.print_background,
                        width=f"{pdf_width}px",
                        height=f"{pdf_height}px",
                        margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"},
                        prefer_css_page_size=False,
                        page_ranges="1",
                        landscape=request.landscape,
                    )
                else:
                    pre_pdf_diagnostics = self._collect_page_diagnostics(
                        page=page,
                        elapsed_ms=int((time.perf_counter() - started_at) * 1000),
                        html_file_size=html_file_size,
                        failed_requests=failed_requests,
                        response_errors=response_errors,
                        console_errors=console_errors,
                    )
                    pre_pdf_diagnostics.content_selector = "body"
                    self.logger.info(
                        f"[pdf-layout] mode=paged format=A4 margin=10mm "
                        f"remove_outer_background={request.remove_outer_background} "
                        f"print_background={request.print_background} landscape={request.landscape} "
                        f"media={request.media}"
                    )
                    self._log_pdf_diagnostics("before-pdf-paged", pre_pdf_diagnostics)
                    pdf_bytes = page.pdf(
                        format="A4",
                        print_background=request.print_background,
                        landscape=request.landscape,
                        margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
                        prefer_css_page_size=False,
                    )

                total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                self.logger.info(
                    f"[pdf-success] elapsed_ms={total_elapsed_ms} bytes={len(pdf_bytes)} "
                    f"failed_requests={len(failed_requests)} http_errors={len(response_errors)} "
                    f"console_errors={len(console_errors)}"
                )
                return pdf_bytes
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                diagnostics = self._collect_page_diagnostics(
                    page=page,
                    elapsed_ms=elapsed_ms,
                    html_file_size=html_file_size,
                    failed_requests=failed_requests,
                    response_errors=response_errors,
                    console_errors=console_errors,
                )
                diagnostics.content_selector = locals().get("content_selector")
                error_code = self._classify_error(exc)
                self._log_failure(error_code, exc, diagnostics)
                raise ExportError(error_code, str(exc), diagnostics) from exc
            finally:
                browser.close()
