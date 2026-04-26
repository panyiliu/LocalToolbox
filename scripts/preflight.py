import argparse
import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.runtime_bootstrap import BootstrapReport, RuntimeBootstrap


def format_result(result) -> str:
    status = "PASS" if result.ok else "FAIL"
    line = f"[{status}] ({result.level}) {result.name}: {result.message}"
    if not result.ok and result.fix:
        line += f" | 修复: {result.fix}"
    return line


def print_report(report: BootstrapReport):
    for result in report.results:
        print(format_result(result))


def run_preflight(skip_noncritical: bool = False, skip_port_check: bool = False) -> int:
    report = RuntimeBootstrap(skip_port_check=skip_port_check).run()
    print_report(report)

    if report.failed_blocks and not skip_noncritical:
        print(f"Preflight failed: {len(report.failed_blocks)} 个阻断项")
        return 1
    if report.warnings:
        print(f"Preflight passed with warnings: {len(report.warnings)}")
    else:
        print("Preflight passed")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Runtime preflight checks")
    parser.add_argument("--skip-noncritical", action="store_true", help="保留与预留参数，当前仅阻断级检查会失败")
    parser.add_argument("--skip-port-check", action="store_true", help="跳过端口占用检查")
    args = parser.parse_args()
    exit_code = run_preflight(skip_noncritical=args.skip_noncritical, skip_port_check=args.skip_port_check)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
