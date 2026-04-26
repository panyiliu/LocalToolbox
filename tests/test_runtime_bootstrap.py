from core.runtime_bootstrap import BootstrapReport, RuntimeBootstrap
from core.runtime_checks import CheckResult


def test_bootstrap_report_properties():
    report = BootstrapReport(
        results=[
            CheckResult(name="a", level="block", ok=True, message="ok"),
            CheckResult(name="b", level="block", ok=False, message="fail"),
            CheckResult(name="c", level="warn", ok=False, message="warn"),
        ]
    )
    assert report.ok is False
    assert len(report.failed_blocks) == 1
    assert len(report.warnings) == 1


def test_runtime_bootstrap_build_checks_respects_skip_port():
    checks_with_port = RuntimeBootstrap(skip_port_check=False).build_checks()
    checks_without_port = RuntimeBootstrap(skip_port_check=True).build_checks()
    assert len(checks_with_port) == len(checks_without_port) + 1
