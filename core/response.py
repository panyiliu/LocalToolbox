from flask import jsonify, send_file
import os
import mimetypes
import shutil
import time

def success(data=None, message='OK'):
    return jsonify({'success': True, 'data': data, 'message': message})

def error(message='Error', code=400):
    return jsonify({'success': False, 'data': None, 'message': message}), code

def _safe_delete_file(path, retries=5, delay_s=0.15):
    for i in range(retries):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except PermissionError:
            if i < retries - 1:
                time.sleep(delay_s)
            else:
                return
        except Exception:
            return

def _safe_delete_dir(path, retries=5, delay_s=0.15):
    for i in range(retries):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=False)
            elif os.path.exists(path):
                _safe_delete_file(path, retries=retries, delay_s=delay_s)
            return
        except PermissionError:
            if i < retries - 1:
                time.sleep(delay_s)
            else:
                return
        except Exception:
            return

def file_response(file_path, download_name=None, cleanup_paths=None, cleanup_dirs=None):
    if download_name is None:
        download_name = os.path.basename(file_path)
    # 确保 mimetype 正确
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        # 根据扩展名手动设置
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.mp3':
            mime_type = 'audio/mpeg'
        elif ext == '.ogg':
            mime_type = 'audio/ogg'
        elif ext == '.flac':
            mime_type = 'audio/flac'
        elif ext == '.zip':
            mime_type = 'application/zip'
        else:
            mime_type = 'application/octet-stream'
    resp = send_file(file_path, as_attachment=True, download_name=download_name, mimetype=mime_type)

    cleanup_paths = cleanup_paths or []
    cleanup_dirs = cleanup_dirs or []

    def _cleanup():
        for p in cleanup_paths:
            if p:
                _safe_delete_file(p)
        for d in cleanup_dirs:
            if d:
                _safe_delete_dir(d)

    # 关键：等响应完全发送完再清理（避免 Windows 上文件占用导致下载失败）
    resp.call_on_close(_cleanup)
    return resp