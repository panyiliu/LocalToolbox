import os
import traceback
from playwright.sync_api import sync_playwright
from PIL import Image
from io import BytesIO
from core.response import file_response, error
from core.logger import get_logger

logger = get_logger('html2image')

def convert(html_path, output_format='JPEG', quality=95):
    """
    核心转换逻辑：将 HTML 文件转为图片
    """
    output_ext = '.jpg' if output_format == 'JPEG' else '.png'
    output_path = os.path.splitext(html_path)[0] + output_ext

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

    image = Image.open(BytesIO(screenshot_bytes))
    if output_format == 'JPEG':
        image = image.convert('RGB')
        image.save(output_path, 'JPEG', quality=quality, subsampling=0)
    else:
        image.save(output_path, 'PNG')

    return output_path

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

    output_format = request.form.get('format', 'JPEG')
    quality = int(request.form.get('quality', 95))

    try:
        output_path = convert(html_path, output_format, quality)
        logger.info(f'转换成功，图片保存至: {output_path}')

        # 构造下载文件名：与源文件同名，仅扩展名改变
        original_filename = file.filename
        base_name = os.path.splitext(original_filename)[0]  # 去掉扩展名
        download_name = base_name + ('.jpg' if output_format == 'JPEG' else '.png')

        # 响应发送完后自动清理缓存文件（输入 HTML + 输出图片）
        return file_response(
            output_path,
            download_name=download_name,
            cleanup_paths=[html_path, output_path],
        )
    except Exception as e:
        logger.error(f'转换失败: {traceback.format_exc()}')
        return error(f'转换失败: {str(e)}', 500)