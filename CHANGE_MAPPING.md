# Behavior Mapping (Old -> New)

## Runtime bootstrap
- Old: startup directly executes `python app.py` without environment checks.
- New: `scripts/preflight.py` delegates to `core/runtime_bootstrap.py` and runs block/warn checks before startup.
- Compatibility: direct `python app.py` remains available as fallback.

## Tool dispatch
- Old: `app.py` used `TOOLS` + dynamic `render_template(f"{tool_id}.html")` + `load_tool(tool_id)`.
- New: `core/tool_registry.py` centralizes tool metadata and module mapping.
- Compatibility: `app.py` still calls legacy `load_tool(tool_id)` when registry import fails.

## `photo_timestamp`
- Old: monolithic `process()` handled validation, timestamp resolve, watermark, and packaging inline.
- New: split into `is_supported_image`, `resolve_timestamp`, `process_single_photo`, `package_outputs`.
- Compatibility: request field (`photos`), response content, and error messages are unchanged.

## `html2image`
- Old: `process()` directly parsed options and invoked Playwright sequence inline.
- New: split into request parsing in `tools/html2image.py`, renderer/service boundary in `core/html2image_engine.py`, and normalized dependency error mapping.
- Compatibility: request fields (`html_file`, `format`, `quality`) and download behavior unchanged.

## Frontend script layering
- Old: major page logic embedded in templates.
- New: logic moved into `static/js/*-page.js` and shared `static/js/world-time-utils.js`.
- Compatibility: templates preserve element IDs, button labels, and API endpoints.

## API client layer
- Old: `common.js` only exported globals.
- New: adds `ToolboxApiClient` stable object while preserving global `apiRequest`/`downloadBlob`.

## Unified dev commands
- Old: npm only wrapped tests.
- New: `preflight`, `dev`, `repair:playwright`, and `dev:skip-noncritical` added.
- Compatibility: existing `test:py`/`test:js` behavior preserved.

## Tool dispatch
- Old: registry path + loader fallback dual-track dispatch.
- New: runtime dispatch uses registry single path only.
- Compatibility: tool IDs and API endpoint contracts remain unchanged.
