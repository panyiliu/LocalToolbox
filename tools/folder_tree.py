from core.response import error

def process(request, upload_folder):
    return error('文件夹树查看器是纯前端工具，无需调用后端API', 400)