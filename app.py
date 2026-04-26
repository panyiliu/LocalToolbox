import os
from flask import Flask, render_template, request
import config
from core.logger import get_logger
from core.response import error
from core.tool_registry import TOOLS, get_tool, get_tool_module

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logger = get_logger('app')

@app.context_processor
def inject_build_info():
    return {
        "app_version": os.environ.get("APP_VERSION", "dev"),
        "app_build_time": os.environ.get("APP_BUILD_TIME", ""),
    }

@app.route('/')
def index():
    return render_template('index.html', tools=TOOLS)

@app.route('/tool/<tool_id>')
def tool_page(tool_id):
    tool = get_tool(tool_id)
    if not tool:
        return error('工具不存在', 404)
    return render_template(tool['template'], tool=tool)

@app.route('/api/<tool_id>', methods=['POST'])
def run_tool(tool_id):
    logger.info(f'收到API请求: /api/{tool_id}')
    module = get_tool_module(tool_id)
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