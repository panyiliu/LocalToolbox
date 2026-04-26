import os
import traceback
from core.response import file_response, error
from core.logger import get_logger
from core.runtime_checks import check_playwright_chromium
from core.html2image_engine import Html2ImageRequest, Html2ImageService, PlaywrightRendererAdapter

logger = get_logger('html2image')


def is_running_in_docker():
    return os.path.exists('/.dockerenv')


def build_playwright_repair_hint():
    if is_running_in_docker():
        return "容器环境缺少 Chromium，请重建镜像: docker compose build --no-cache && docker compose up -d"
    return "本地环境缺少 Chromium，请执行: python -m playwright install chromium"


def normalize_conversion_error(exc: Exception):
    message = str(exc)
    lowered = message.lower()
    playwright_keywords = ["playwright", "chromium", "executable", "browser", "install"]
    if any(keyword in lowered for keyword in playwright_keywords):
        repair_hint = build_playwright_repair_hint()
        return f"HTML 转图依赖不可用。{repair_hint}"
    return f"转换失败: {message}"

class PlaywrightHtmlRenderer:
    def render(self, html_path):
        return PlaywrightRendererAdapter().render(html_path)


def parse_options(form):
    output_format = form.get('format', 'JPEG')
    if output_format not in ('JPEG', 'PNG'):
        output_format = 'JPEG'
    quality_raw = form.get('quality', 95)
    try:
        quality = int(quality_raw)
    except (ValueError, TypeError):
        quality = 95
    quality = max(1, min(100, quality))
    return output_format, quality


def build_download_name(original_filename, output_format):
    base_name = os.path.splitext(original_filename)[0]
    return base_name + ('.jpg' if output_format == 'JPEG' else '.png')

def convert(html_path, output_format='JPEG', quality=95):
    """
    核心转换逻辑：将 HTML 文件转为图片
    """
    request = Html2ImageRequest(html_path=html_path, output_format=output_format, quality=quality)
    return Html2ImageService(PlaywrightRendererAdapter()).execute(request)

def process(request, upload_folder):
    logger.info('开始处理 HTML 转图片请求')

    if 'html_file' not in request.files:
        return error('请上传 HTML 文件', 400)
    file = request.files['html_file']
    if file.filename == '':
        return error('未选择文件', 400)

    html_path = os.path.join(upload_folder, file.filename)
    try:
        file.save(html_path)
    except Exception as e:
        logger.error(f'保存上传文件失败: {e}')
        return error('保存文件失败', 500)

    output_format, quality = parse_options(request.form)

    playwright_check = check_playwright_chromium()
    if not playwright_check.ok:
        logger.error(playwright_check.message)
        return error(f"HTML 转图环境检查失败。{build_playwright_repair_hint()}", 503)

    try:
        output_path = convert(html_path, output_format, quality)
        logger.info(f'转换成功，图片保存至: {output_path}')

        download_name = build_download_name(file.filename, output_format)

        # 响应发送完后自动清理缓存文件（输入 HTML + 输出图片）
        return file_response(
            output_path,
            download_name=download_name,
            cleanup_paths=[html_path, output_path],
        )
    except Exception as e:
        logger.error(f'转换失败: {traceback.format_exc()}')
        return error(normalize_conversion_error(e), 500)