import os
import zipfile
import shutil
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ExifTags, ImageOps
from core.response import file_response, error
from core.logger import get_logger

logger = get_logger('photo_timestamp')

# 字体文件路径（绝对路径，请确保文件存在）
FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'fonts', 'digital-7 (mono).ttf'
)

def get_exif_datetime(image):
    """从图片 EXIF 中获取拍摄时间，返回 datetime 对象或 None"""
    try:
        exif = image._getexif()
        if exif is None:
            return None
        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            if tag_name == 'DateTimeOriginal':
                dt_str = value
                return datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"读取 EXIF 失败: {e}")
    return None

def get_file_modify_time(file_path):
    """获取文件修改时间"""
    ts = os.path.getmtime(file_path)
    return datetime.fromtimestamp(ts)

def orientate(image):
    """根据 EXIF 方向信息旋转图片"""
    return ImageOps.exif_transpose(image)

def add_watermark(image, text):
    """
    在图片上添加水印（完全采用您的原始逻辑，仅字体大小比例调整为 0.06）
    """
    # 将图片转正
    image = orientate(image)
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # 根据照片的宽高比例动态调整字体大小（调大至 0.06，可自行修改）
    if width > height:  # 横屏照片
        font_size = int(0.03 * width)
    else:  # 竖屏照片
        font_size = int(0.03 * height)

    # 加载字体（如果失败则使用默认字体）
    try:
        font = ImageFont.truetype(FONT_PATH, size=font_size)
        logger.info(f"使用指定字体，字号 {font_size}")
    except Exception as e:
        logger.error(f"指定字体加载失败: {FONT_PATH}，将使用默认字体。错误: {e}")
        font = ImageFont.load_default()

    fillcolor = '#F3AF16'  # 金黄色

    # 获取文本的边界框坐标
    text_bbox = draw.textbbox((0, 0), text, font=font)

    # 计算靠底部和靠边的像素值
    margin_bottom = int(0.05 * height)
    margin_right = int(0.05 * width)

    # 确定文本的位置（右下角）
    d_width = width - text_bbox[2] - margin_right
    d_height = height - text_bbox[3] - margin_bottom

    # 绘制文本
    draw.text((d_width, d_height), text, font=font, fill=fillcolor)

    return image

def get_new_filename(original_name):
    """生成新文件名：在原文件名前加 'watermark_' 并保持 .jpg 扩展名"""
    base = os.path.splitext(original_name)[0]
    return f"watermark_{base}.jpg"


def is_supported_image(filename):
    return filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))


def resolve_timestamp(image, input_path):
    dt = get_exif_datetime(image)
    if dt is None:
        dt = get_file_modify_time(input_path)
        logger.info(f"使用文件修改时间: {dt}")
    else:
        logger.info(f"使用 EXIF 拍摄时间: {dt}")
    return dt


def process_single_photo(file, temp_dir):
    if not is_supported_image(file.filename):
        logger.warning(f"跳过非图片文件: {file.filename}")
        return None

    input_path = os.path.join(temp_dir, file.filename)
    file.save(input_path)

    try:
        img = Image.open(input_path)
    except Exception as e:
        logger.error(f"无法打开图片 {file.filename}: {e}")
        return None

    dt = resolve_timestamp(img, input_path)
    text = dt.strftime('%Y-%m-%d %H:%M')
    img_with_watermark = add_watermark(img, text)

    new_filename = get_new_filename(file.filename)
    output_path = os.path.join(temp_dir, new_filename)
    img_with_watermark.save(output_path, 'JPEG', quality=95)
    return output_path


def package_outputs(output_files, upload_folder):
    zip_path = os.path.join(upload_folder, f'timestamped_photos_{os.urandom(4).hex()}.zip')
    with zipfile.ZipFile(zip_path, 'w') as z:
        for output_file in output_files:
            z.write(output_file, arcname=os.path.basename(output_file))
    return zip_path

def process(request, upload_folder):
    logger.info("开始处理照片添加时间戳请求")

    files = request.files.getlist('photos')
    if not files or files[0].filename == '':
        return error("请至少上传一个图片文件", 400)

    temp_dir = os.path.join(upload_folder, 'photo_ts_' + os.urandom(4).hex())
    os.makedirs(temp_dir, exist_ok=True)

    output_files = []

    try:
        for file in files:
            output_path = process_single_photo(file, temp_dir)
            if output_path:
                output_files.append(output_path)

        if not output_files:
            return error("没有成功处理的图片", 400)

        # 单文件直接返回
        if len(output_files) == 1:
            file_to_send = output_files[0]
            download_name = os.path.basename(file_to_send)
            # 响应发送完后清理整个临时目录（包含输入+输出）
            return file_response(
                file_to_send,
                download_name=download_name,
                cleanup_dirs=[temp_dir],
            )

        zip_path = package_outputs(output_files, upload_folder)
        return file_response(
            zip_path,
            download_name='timestamped_photos.zip',
            cleanup_paths=[zip_path],
            cleanup_dirs=[temp_dir],
        )

    except Exception as e:
        logger.exception("处理过程中发生异常")
        # 异常时清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        return error(f"处理失败: {str(e)}", 500)
    finally:
        # 确保在返回响应后，临时目录中的文件有机会被清理
        # 下载响应的清理由 file_response(call_on_close) 负责
        pass