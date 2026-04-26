# Runtime Stability Regression Report

## Scope
- Runtime preflight checks (local and container startup path)
- `html2image` Playwright runtime guard and normalized error message
- Environment contract alignment (README + Docker/Compose startup path)
- Unified npm commands (`preflight`, `dev`, `repair:playwright`, `test`)
- RuntimeBootstrap module API (`core/runtime_bootstrap.py`)
- Tool dispatch single path (registry-only dispatch in `app.py`)
- Html2Image engine boundary module (`core/html2image_engine.py`)

## Automated verification
- Python contract tests: `15 passed`
  - Run command: `npm run test:py`
- JavaScript client tests: `3 passed`
  - Run command: `npm run test:js`
- Local preflight:
  - Before repair: failed on `playwright_chromium` block item as expected
  - After `npm run repair:playwright`: passed (with debug warning only)

## Environment checks and outcomes
- `python_version`: pass
- `python_dependencies`: pass
- `upload_folder_writable`: pass
- `log_folder_writable`: pass
- `playwright_chromium`: pass after repair command
- `port_available`: pass
- `debug_mode`: warn when `FLASK_DEBUG=true` (non-blocking by design)

## New contract coverage
- `tests/test_runtime_bootstrap.py`: validates structured bootstrap report and check graph behavior.
- `tests/test_tool_registry_contract.py`: validates registry completeness and lookup integrity.
- `tests/test_html2image_runtime_guard.py`: validates normalized failure mapping for renderer dependency errors.

## Docker path verification
- `docker compose up --build -d` attempted and failed on host side:
  - Docker Desktop engine pipe unavailable (`//./pipe/dockerDesktopLinuxEngine`)
  - This is an environment availability blocker, not project code failure.

## Residual risk
- Docker runtime path must be re-verified on a host with active Docker engine.
- Browser-level visual regression is still manual.
