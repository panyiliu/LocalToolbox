import os
from dataclasses import dataclass
from io import BytesIO

from PIL import Image
from playwright.sync_api import sync_playwright


@dataclass
class Html2ImageRequest:
    html_path: str
    output_format: str = "JPEG"
    quality: int = 95


class PlaywrightRendererAdapter:
    def render(self, html_path: str) -> bytes:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"file:///{os.path.abspath(html_path)}")
            page.wait_for_load_state("networkidle")

            width = page.evaluate("document.body.scrollWidth")
            height = page.evaluate("document.body.scrollHeight")
            page.set_viewport_size({
                "width": min(width, 3000),
                "height": min(height, 10000)
            })

            screenshot_bytes = page.screenshot(full_page=True)
            browser.close()
            return screenshot_bytes


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
