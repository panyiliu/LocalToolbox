from dataclasses import dataclass
from io import BytesIO

from PIL import Image
from core.html_export_engine import (
    ExportDiagnostics as RenderDiagnostics,
    ExportError as RenderError,
    ExportPolicy as RenderPolicy,
    PlaywrightHtmlExportEngine,
)


@dataclass
class Html2ImageRequest:
    html_path: str
    output_format: str = "JPEG"
    quality: int = 95


class PlaywrightRendererAdapter:
    def __init__(self, policy: RenderPolicy | None = None):
        self.engine = PlaywrightHtmlExportEngine(policy=policy, logger_name="html2image.renderer")

    def render(self, html_path: str) -> bytes:
        return self.engine.render_image(html_path)


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
