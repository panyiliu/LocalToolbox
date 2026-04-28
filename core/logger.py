import os
import logging
from config import LOG_PATH

def get_logger(name='toolbox'):
    """获取日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 确保日志目录存在
    log_dir = os.path.dirname(LOG_PATH)
    os.makedirs(log_dir, exist_ok=True)

    # 文件handler
    file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 控制台handler（开发时方便）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger