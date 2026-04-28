from importlib import import_module
from typing import Optional

from core.logger import get_logger

logger = get_logger("tool_registry")

ToolDescriptor = dict[str, str]

_TOOL_DESCRIPTORS: list[ToolDescriptor] = [
    {
        "id": "html2image",
        "name": "HTML转图片",
        "description": "将HTML文件转换为JPEG或PNG图片",
        "icon": "bi-filetype-html",
        "template": "html2image.html",
        "module": "tools.html2image",
    },
    {
        "id": "html2pdf",
        "name": "HTML转PDF",
        "description": "将HTML文件转换为单页或分页PDF",
        "icon": "bi-file-earmark-pdf",
        "template": "html2pdf.html",
        "module": "tools.html2pdf",
    },
    {
        "id": "folder_tree",
        "name": "文件夹树查看器",
        "description": "显示文件夹结构树并支持复制",
        "icon": "bi-folder",
        "template": "folder_tree.html",
        "module": "tools.folder_tree",
    },
    {
        "id": "photo_timestamp",
        "name": "照片添加拍摄时间戳",
        "description": "为照片添加拍摄日期水印",
        "icon": "bi-camera",
        "template": "photo_timestamp.html",
        "module": "tools.photo_timestamp",
    },
    {
        "id": "world_clock",
        "name": "世界时钟",
        "description": "查看全球主要时区的当前时间",
        "icon": "bi-globe2",
        "template": "world_clock.html",
        "module": "",
    },
    {
        "id": "world_map_clock",
        "name": "世界地图时钟",
        "description": "在世界地图上查看主要城市的当地时间",
        "icon": "bi-map",
        "template": "world_map_clock.html",
        "module": "",
    },
]

TOOLS: list[ToolDescriptor] = [
    {
        "id": item["id"],
        "name": item["name"],
        "description": item["description"],
        "icon": item["icon"],
        "template": item["template"],
    }
    for item in _TOOL_DESCRIPTORS
]

_TOOLS_BY_ID = {item["id"]: item for item in _TOOL_DESCRIPTORS}


def get_tool(tool_id: str) -> Optional[ToolDescriptor]:
    return _TOOLS_BY_ID.get(tool_id)


def get_tool_module(tool_id: str):
    descriptor = _TOOLS_BY_ID.get(tool_id)
    if not descriptor:
        return None
    module_path = descriptor.get("module", "")
    if not module_path:
        return None
    try:
        return import_module(module_path)
    except Exception:
        logger.exception("加载注册工具失败: %s", module_path)
        return None
