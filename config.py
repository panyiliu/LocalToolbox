import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 上传文件夹
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
# 日志文件
LOG_PATH = os.path.join(BASE_DIR, 'logs/app.log')
# 调试模式
DEBUG = True
# 服务监听地址和端口
HOST = '0.0.0.0'
PORT = 5000