import os
import time
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image
from playwright.sync_api import sync_playwright
from core.logger import get_logger

logger = get_logger('html2image.renderer')


@dataclass
class Html2ImageRequest:
    html_path: str
    output_format: str = "JPEG"
    quality: int = 95


@dataclass
class RenderPolicy:
    wait_until: str = "domcontentloaded"
    goto_timeout_ms: int = 15000
    settle_time_ms: int = 800
    use_networkidle: bool = False
    networkidle_timeout_ms: int = 2000
    allow_partial_on_navigation_timeout: bool = True
    screenshot_timeout_ms: int = 10000


@dataclass
class RenderDiagnostics:
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


class RenderError(Exception):
    def __init__(self, code: str, message: str, diagnostics: RenderDiagnostics):
        super().__init__(message)
        self.code = code
        self.diagnostics = diagnostics

    def __str__(self) -> str:
        return f"{self.code}: {super().__str__()}"


class PlaywrightRendererAdapter:
    def __init__(self, policy: RenderPolicy | None = None):
        self.policy = policy or RenderPolicy()

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
        if "screenshot" in message:
            return "screenshot_failed"
        return "render_failed"

    @staticmethod
    def _measure_dimensions(page) -> tuple[int, int]:
        width = page.evaluate("document.body ? document.body.scrollWidth : 1280")
        height = page.evaluate("document.body ? document.body.scrollHeight : 720")
        return int(width), int(height)

    @staticmethod
    def _collect_page_diagnostics(page, elapsed_ms: int, html_file_size: int, failed_requests: list[dict], response_errors: list[dict], console_errors: list[str]) -> RenderDiagnostics:
        ready_state = "unknown"
        html_metrics: dict = {}
        external_resources: list[str] = []
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
        except Exception:
            pass

        resource_hosts = sorted({urlparse(url).netloc for url in external_resources if urlparse(url).netloc})
        return RenderDiagnostics(
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
        )

    def render(self, html_path: str) -> bytes:
        abs_html_path = os.path.abspath(html_path)
        file_url = self._build_file_url(abs_html_path)
        html_file_size = os.path.getsize(abs_html_path) if os.path.exists(abs_html_path) else -1
        started_at = time.perf_counter()
        failed_requests = []
        response_errors = []
        console_errors = []

        logger.info(
            f"[render-start] html_path={html_path} abs_html_path={abs_html_path} "
            f"file_size={html_file_size} file_url={file_url}"
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

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
                page.goto(
                    file_url,
                    wait_until=self.policy.wait_until,
                    timeout=self.policy.goto_timeout_ms,
                )
                goto_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                logger.info(f"[render-goto-ok] elapsed_ms={goto_elapsed_ms} url={page.url}")

                if self.policy.settle_time_ms > 0:
                    page.wait_for_timeout(self.policy.settle_time_ms)

                if self.policy.use_networkidle:
                    page.wait_for_load_state("networkidle", timeout=self.policy.networkidle_timeout_ms)
                    idle_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    logger.info(f"[render-networkidle-ok] elapsed_ms={idle_elapsed_ms} url={page.url}")

                width, height = self._measure_dimensions(page)
                page.set_viewport_size({
                    "width": min(width, 3000),
                    "height": min(height, 10000)
                })

                screenshot_bytes = page.screenshot(full_page=True, timeout=self.policy.screenshot_timeout_ms)
                total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                logger.info(
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
                logger.error(
                    f"[render-failed] code={error_code} elapsed_ms={diagnostics.elapsed_ms} error={exc} "
                    f"page_url={diagnostics.page_url} ready_state={diagnostics.ready_state} "
                    f"html_file_size={diagnostics.html_file_size} html_metrics={diagnostics.html_metrics} "
                    f"resource_hosts={diagnostics.resource_hosts} "
                    f"external_resource_count={diagnostics.external_resource_count} "
                    f"failed_requests={diagnostics.failed_requests} "
                    f"http_errors={diagnostics.http_errors} console_errors={diagnostics.console_errors}"
                )

                if error_code == "navigation_timeout" and self.policy.allow_partial_on_navigation_timeout:
                    logger.warning("[render-fallback] navigation timeout, attempt partial screenshot")
                    width, height = self._measure_dimensions(page)
                    page.set_viewport_size({
                        "width": min(width, 3000),
                        "height": min(height, 10000)
                    })
                    screenshot_bytes = page.screenshot(full_page=True, timeout=self.policy.screenshot_timeout_ms)
                    total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                    logger.info(
                        f"[render-fallback-success] elapsed_ms={total_elapsed_ms} width={width} "
                        f"height={height} screenshot_bytes={len(screenshot_bytes)}"
                    )
                    return screenshot_bytes

                raise RenderError(error_code, str(exc), diagnostics) from exc
            finally:
                browser.close()


class Html2ImageService:
    def __init__(self, renderer: PlaywrightRendererAdapter):
        self.renderer = renderer

    def execute(self, request: Html2ImageRequest) -> str:
        output_ext = '.jpg' if request.output_format == 'JPEG' else '.png'
        output_path = os.path.splitext(request.html_path)[0] + output_ext
        screenshot_bytes = self.renderer.render(request.html_path)

        image = Image.open(BytesIO(screenshot_bytes))
        if request.output_format == 'JPEG':
            image = image.convert('RGB')
            image.save(output_path, 'JPEG', quality=request.quality, subsampling=0)
        else:
            image.save(output_path, 'PNG')
        return output_path
