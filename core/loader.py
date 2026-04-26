import importlib
import traceback
from core.logger import get_logger
from core.tool_registry import get_tool

logger = get_logger('loader')

def load_tool(tool_id):
    """兼容函数：仅允许加载注册表中存在的工具模块"""
    if not get_tool(tool_id):
        logger.error(f'工具未注册: {tool_id}')
        return None
    try:
        module = importlib.import_module(f'tools.{tool_id}')
        logger.info(f'成功加载工具: {tool_id}')
        return module
    except ModuleNotFoundError:
        logger.error(f'工具模块不存在: {tool_id}')
        return None
    except Exception as e:
        logger.error(f'加载工具 {tool_id} 时出错: {traceback.format_exc()}')
        return None