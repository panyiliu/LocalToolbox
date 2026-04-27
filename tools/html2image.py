import os
import traceback
import time
from core.response import file_response, error
from core.logger import get_logger
from core.runtime_checks import check_playwright_chromium
from core.html2image_engine import Html2ImageRequest, Html2ImageService, PlaywrightRendererAdapter, RenderError, RenderPolicy

logger = get_logger('html2image')

_PLAYWRIGHT_CHECK_CACHE_SECONDS = 300
_playwright_check_cached_at = 0.0
_playwright_check_cached_result = None


def is_running_in_docker():
    return os.path.exists('/.dockerenv')


def build_playwright_repair_hint():
    if is_running_in_docker():
        return "容器环境缺少 Chromium，请重建镜像: docker compose build --no-cache && docker compose up -d"
    return "本地环境缺少 Chromium，请执行: python -m playwright install chromium"


def normalize_conversion_error(exc: Exception):
    if isinstance(exc, RenderError):
        if exc.code == "navigation_timeout":
            return "转换失败: 页面外链资源加载超时。已记录诊断日志，请优先检查外网资源可达性。"
        if exc.code == "network_idle_timeout":
            return "转换失败: 页面网络空闲等待超时。建议减少外链资源或使用本地资源。"
        if exc.code == "screenshot_failed":
            return "转换失败: 页面截图阶段失败。请检查页面脚本与样式兼容性。"
        return f"转换失败: {exc}"

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
    领域边界：将业务参数转换为渲染请求，并交给渲染引擎执行。
    """
    render_policy = RenderPolicy(
        wait_until="domcontentloaded",
        goto_timeout_ms=15000,
        settle_time_ms=1000,
        use_networkidle=False,
        networkidle_timeout_ms=2000,
        allow_partial_on_navigation_timeout=True,
        screenshot_timeout_ms=10000,
    )
    request = Html2ImageRequest(html_path=html_path, output_format=output_format, quality=quality)
    return Html2ImageService(PlaywrightRendererAdapter(policy=render_policy)).execute(request)


def check_playwright_chromium_cached():
    global _playwright_check_cached_at
    global _playwright_check_cached_result
    now = time.time()
    if _playwright_check_cached_result is not None and (now - _playwright_check_cached_at) < _PLAYWRIGHT_CHECK_CACHE_SECONDS:
        return _playwright_check_cached_result
    result = check_playwright_chromium()
    _playwright_check_cached_result = result
    _playwright_check_cached_at = now
    return result

def process(request, upload_folder):
    # 应用边界：负责 HTTP 参数/文件处理与错误映射，不承载渲染细节。
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
    playwright_check = check_playwright_chromium_cached()
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