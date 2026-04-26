from core.tool_registry import TOOLS, get_tool


def test_tool_registry_entries_have_required_fields():
    required_fields = {"id", "name", "description", "icon", "template"}
    for tool in TOOLS:
        assert required_fields.issubset(set(tool.keys()))
        assert tool["id"]
        assert tool["template"].endswith(".html")


def test_get_tool_returns_registered_tool():
    for tool in TOOLS:
        looked_up = get_tool(tool["id"])
        assert looked_up is not None
        assert looked_up["template"] == tool["template"]
