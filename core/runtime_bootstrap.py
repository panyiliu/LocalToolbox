import os
from dataclasses import dataclass
from typing import Callable

import config
from core.runtime_checks import (
    CheckResult,
    check_debug_mode_warning,
    check_directory_writable,
    check_playwright_chromium,
    check_port_available,
    check_python_dependencies,
    check_python_version,
)


CheckFactory = Callable[[], CheckResult]


@dataclass
class BootstrapReport:
    results: list[CheckResult]

    @property
    def failed_blocks(self) -> list[CheckResult]:
        return [result for result in self.results if not result.ok and result.level == "block"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [result for result in self.results if not result.ok and result.level == "warn"]

    @property
    def ok(self) -> bool:
        return not self.failed_blocks


class RuntimeBootstrap:
    def __init__(self, skip_port_check: bool = False):
        self.skip_port_check = skip_port_check

    def build_checks(self) -> list[CheckFactory]:
        checks: list[CheckFactory] = [
            lambda: check_python_version(),
            lambda: check_python_dependencies(),
            lambda: check_directory_writable(config.UPLOAD_FOLDER, "upload_folder_writable"),
            lambda: check_directory_writable(os.path.dirname(config.LOG_PATH), "log_folder_writable"),
            lambda: check_playwright_chromium(),
            lambda: check_debug_mode_warning(config.DEBUG),
        ]
        if not self.skip_port_check:
            checks.append(lambda: check_port_available(config.HOST, config.PORT))
        return checks

    def run(self) -> BootstrapReport:
        results = [check_factory() for check_factory in self.build_checks()]
        return BootstrapReport(results=results)
