import os
from flask import Flask, render_template, request
import config
from core.loader import load_tool
from core.logger import get_logger
from core.response import error

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logger = get_logger('app')

# 工具列表（手动维护，清晰直观）
TOOLS = [
    {'id': 'html2image',    'name': 'HTML转图片',      'description': '将HTML文件转换为JPEG或PNG图片', 'icon': 'bi-filetype-html'},
    {'id': 'folder_tree',   'name': '文件夹树查看器',  'description': '显示文件夹结构树并支持复制', 'icon': 'bi-folder'},
    {'id': 'photo_timestamp', 'name': '照片添加拍摄时间戳', 'description': '为照片添加拍摄日期水印', 'icon': 'bi-camera'},
    {'id': 'world_clock',   'name': '世界时钟',        'description': '查看全球主要时区的当前时间', 'icon': 'bi-globe2'},
    {'id': 'world_map_clock', 'name': '世界地图时钟',  'description': '在世界地图上查看主要城市的当地时间', 'icon': 'bi-map'},
]

@app.route('/')
def index():
    return render_template('index.html', tools=TOOLS)

@app.route('/tool/<tool_id>')
def tool_page(tool_id):
    tool = next((t for t in TOOLS if t['id'] == tool_id), None)
    if not tool:
        return error('工具不存在', 404)
    return render_template(f'{tool_id}.html', tool=tool)

@app.route('/api/<tool_id>', methods=['POST'])
def run_tool(tool_id):
    logger.info(f'收到API请求: /api/{tool_id}')
    module = load_tool(tool_id)
    if not module:
        return error('工具不存在或加载失败', 404)

    # 调用工具的process函数
    try:
        # 注意：process应返回Flask响应对象（可以是json或file）
        return module.process(request, app.config['UPLOAD_FOLDER'])
    except Exception as e:
        logger.exception(f'工具 {tool_id} 处理出错')
        return error(f'服务器内部错误: {str(e)}', 500)

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)