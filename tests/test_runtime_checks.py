from core.runtime_checks import check_debug_mode_warning, check_python_version


def test_python_version_check_passes_current_runtime():
    result = check_python_version(3, 10)
    assert result.ok is True
    assert result.level == "block"


def test_debug_mode_warning_reports_warn_when_enabled():
    result = check_debug_mode_warning(True)
    assert result.ok is False
    assert result.level == "warn"
    assert "FLASK_DEBUG=true" in result.message
