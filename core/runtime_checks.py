import importlib.util
import os
import socket
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    level: str
    ok: bool
    message: str
    fix: str = ""


def check_python_dependencies() -> CheckResult:
    required_modules = ["flask", "playwright", "PIL"]
    missing = [module for module in required_modules if importlib.util.find_spec(module) is None]
    if missing:
        return CheckResult(
            name="python_dependencies",
            level="block",
            ok=False,
            message=f"缺少 Python 依赖: {', '.join(missing)}",
            fix="python -m pip install -r requirements.txt",
        )
    return CheckResult(name="python_dependencies", level="block", ok=True, message="Python 依赖完整")


def check_python_version(min_major: int = 3, min_minor: int = 10) -> CheckResult:
    version_info = sys.version_info
    version_text = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    if (version_info.major, version_info.minor) < (min_major, min_minor):
        return CheckResult(
            name="python_version",
            level="block",
            ok=False,
            message=f"Python 版本过低: {version_text}",
            fix=f"请升级到 Python {min_major}.{min_minor}+",
        )
    return CheckResult(name="python_version", level="block", ok=True, message=f"Python 版本满足要求: {version_text}")


def check_directory_writable(path: str, name: str) -> CheckResult:
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, ".write_test")
        with open(test_file, "w", encoding="utf-8") as file_obj:
            file_obj.write("ok")
        os.remove(test_file)
        return CheckResult(name=name, level="block", ok=True, message=f"目录可写: {path}")
    except Exception as exc:
        return CheckResult(
            name=name,
            level="block",
            ok=False,
            message=f"目录不可写: {path} ({exc})",
            fix=f"检查目录权限并确保可写: {path}",
        )


def check_port_available(host: str, port: int) -> CheckResult:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return CheckResult(
                name="port_available",
                level="block",
                ok=False,
                message=f"端口被占用: {host}:{port}",
                fix=f"更换 FLASK_PORT 或停止占用端口 {port} 的进程",
            )
    return CheckResult(name="port_available", level="block", ok=True, message=f"端口可用: {host}:{port}")


def check_playwright_chromium() -> CheckResult:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
        return CheckResult(name="playwright_chromium", level="block", ok=True, message="Chromium 可用")
    except Exception as exc:
        return CheckResult(
            name="playwright_chromium",
            level="block",
            ok=False,
            message=f"Chromium 不可用: {exc}",
            fix="python -m playwright install chromium",
        )


def check_debug_mode_warning(debug_enabled: bool) -> CheckResult:
    if debug_enabled:
        return CheckResult(
            name="debug_mode",
            level="warn",
            ok=False,
            message="当前 FLASK_DEBUG=true，生产环境建议关闭",
            fix="设置环境变量 FLASK_DEBUG=false",
        )
    return CheckResult(name="debug_mode", level="warn", ok=True, message="Debug 模式配置正常")
