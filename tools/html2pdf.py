import os
import time
import traceback

from core.html_export_engine import ExportError, ExportPolicy, PdfExportRequest, PlaywrightHtmlExportEngine
from core.logger import get_logger
from core.response import error, file_response
from core.runtime_checks import check_playwright_chromium

logger = get_logger("html2pdf")

_PLAYWRIGHT_CHECK_CACHE_SECONDS = 300
_playwright_check_cached_at = 0.0
_playwright_check_cached_result = None


def is_running_in_docker():
    return os.path.exists("/.dockerenv")


def build_playwright_repair_hint():
    if is_running_in_docker():
        return "容器环境缺少 Chromium，请重建镜像: docker compose build --no-cache && docker compose up -d"
    return "本地环境缺少 Chromium，请执行: python -m playwright install chromium"


def normalize_conversion_error(exc: Exception):
    if isinstance(exc, ExportError):
        if exc.code == "navigation_timeout":
            return "转换失败: 页面加载超时。已记录诊断日志，请优先检查外链资源可达性。"
        if exc.code == "content_not_found":
            return "转换失败: 无法自动识别页面主体内容，请检查 HTML 结构。"
        if exc.code == "pdf_export_failed":
            return "转换失败: PDF 导出阶段失败。请检查页面样式与布局。"
        return f"转换失败: {exc}"

    message = str(exc)
    lowered = message.lower()
    playwright_keywords = ["playwright", "chromium", "executable", "browser", "install"]
    if any(keyword in lowered for keyword in playwright_keywords):
        return f"HTML 转 PDF 依赖不可用。{build_playwright_repair_hint()}"
    return f"转换失败: {message}"


def parse_bool(value, default):
    if value is None:
        return default
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def parse_options(form):
    mode = form.get("mode", "single_page")
    if mode not in {"single_page", "paged"}:
        mode = "single_page"

    media = form.get("media", "screen")
    if media not in {"screen", "print"}:
        media = "screen"

    return {
        "mode": mode,
        "media": media,
        "remove_outer_background": parse_bool(form.get("remove_outer_background"), True),
        "print_background": parse_bool(form.get("print_background"), True),
        "landscape": parse_bool(form.get("landscape"), False),
    }


def build_download_name(original_filename):
    return os.path.splitext(original_filename)[0] + ".pdf"


def convert(html_path, *, mode="single_page", media="screen", remove_outer_background=True, print_background=True, landscape=False):
    policy = ExportPolicy(
        wait_until="domcontentloaded",
        goto_timeout_ms=15000,
        settle_time_ms=1000,
        use_networkidle=False,
        networkidle_timeout_ms=2000,
        allow_partial_on_navigation_timeout=False,
        screenshot_timeout_ms=10000,
        pdf_timeout_ms=12000,
    )
    request = PdfExportRequest(
        html_path=html_path,
        mode=mode,
        media=media,
        remove_outer_background=remove_outer_background,
        print_background=print_background,
        landscape=landscape,
    )
    output_path = os.path.splitext(html_path)[0] + ".pdf"
    pdf_bytes = PlaywrightHtmlExportEngine(policy=policy, logger_name="html2pdf.renderer").render_pdf(request)
    with open(output_path, "wb") as file_obj:
        file_obj.write(pdf_bytes)
    return output_path


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
    logger.info("开始处理 HTML 转 PDF 请求")

    if "html_file" not in request.files:
        return error("请上传 HTML 文件", 400)
    file = request.files["html_file"]
    if file.filename == "":
        return error("未选择文件", 400)

    html_path = os.path.join(upload_folder, file.filename)
    try:
        file.save(html_path)
    except Exception as exc:
        logger.error(f"保存上传文件失败: {exc}")
        return error("保存文件失败", 500)

    playwright_check = check_playwright_chromium_cached()
    if not playwright_check.ok:
        logger.error(playwright_check.message)
        return error(f"HTML 转 PDF 环境检查失败。{build_playwright_repair_hint()}", 503)

    options = parse_options(request.form)
    html_size = os.path.getsize(html_path) if os.path.exists(html_path) else -1
    logger.info(
        f"HTML 转 PDF 请求参数: filename={file.filename} html_path={html_path} "
        f"html_size={html_size} options={options}"
    )

    try:
        output_path = convert(html_path, **options)
        logger.info(f"转换成功，PDF 保存至: {output_path}")
        return file_response(
            output_path,
            download_name=build_download_name(file.filename),
            cleanup_paths=[html_path, output_path],
        )
    except Exception as exc:
        logger.error(f"转换失败: {traceback.format_exc()}")
        return error(normalize_conversion_error(exc), 500)
