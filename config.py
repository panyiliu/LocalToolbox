import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 上传文件夹
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
# 日志文件
LOG_PATH = os.path.join(BASE_DIR, 'logs/app.log')
# 调试模式（Docker / 生产建议设置环境变量 FLASK_DEBUG=false）
DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes')
# 服务监听地址和端口
HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
PORT = int(os.environ.get('FLASK_PORT', '5000'))