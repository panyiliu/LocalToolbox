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


class PlaywrightRendererAdapter:
    def render(self, html_path: str) -> bytes:
        abs_html_path = os.path.abspath(html_path)
        file_url = f"file:///{abs_html_path}"
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
                page.goto(file_url, wait_until="load")
                goto_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                logger.info(f"[render-goto-ok] elapsed_ms={goto_elapsed_ms} url={page.url}")

                page.wait_for_load_state("networkidle")
                idle_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                logger.info(f"[render-networkidle-ok] elapsed_ms={idle_elapsed_ms} url={page.url}")

                width = page.evaluate("document.body.scrollWidth")
                height = page.evaluate("document.body.scrollHeight")
                page.set_viewport_size({
                    "width": min(width, 3000),
                    "height": min(height, 10000)
                })

                screenshot_bytes = page.screenshot(full_page=True)
                total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                logger.info(
                    f"[render-success] elapsed_ms={total_elapsed_ms} width={width} height={height} "
                    f"screenshot_bytes={len(screenshot_bytes)} failed_requests={len(failed_requests)} "
                    f"http_errors={len(response_errors)} console_errors={len(console_errors)}"
                )
                return screenshot_bytes
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                ready_state = "unknown"
                html_metrics = {}
                external_resources = []
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
                logger.error(
                    f"[render-failed] elapsed_ms={elapsed_ms} error={exc} page_url={page.url} "
                    f"ready_state={ready_state} html_file_size={html_file_size} html_metrics={html_metrics} "
                    f"resource_hosts={resource_hosts} external_resource_count={len(external_resources)} "
                    f"failed_requests={failed_requests[:20]} http_errors={response_errors[:20]} "
                    f"console_errors={console_errors[:20]}"
                )
                raise
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
