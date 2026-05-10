# XiaozhiMCP Components

Pluggable MCP components for the XiaozhiMCP platform. Components extend the server or client with additional MCP tools — each component lives in its own directory and is auto-discovered by the runtime.

## Component vs. Core System Feature

A feature should be a **Component** when it meets one or more of these criteria:

| Criteria | Example |
|---|---|
| Wraps an external API or third-party MCP server | `exa` (Exa AI search API), `apple_music_macos` (mcp-applemusic bridge) |
| Requires platform-specific OS interaction | `clipboard` (Windows clipboard), `windows_manager` (Win32 window APIs) |
| Is an optional domain feature with independent persistence | `local_schedule` (SQLite-backed schedule) |
| Has its own external dependencies not needed by core | `exa` needs `requests`, `clipboard` needs `pywin32` |

A feature should be a **Core System Feature** (built into the main `xiaozhiMCP` server) when:

| Criteria | Example |
|---|---|
| It is a thin facade over a core module already in the main repo | `logmcp_get_errors` (45-line wrapper over `ErrorStore`) |
| It provides infrastructure every deployment needs | Catalog management, cluster communication, error logging |
| It has no external dependencies beyond what core already uses | SQLite-based error store is already in `error_store.py` |

## Component Structure

```
my_component/
  __init__.py       # Empty file (enables package imports)
  component.py      # Entry point (see interface below)
  README.md         # Component documentation
```

### `component.py` Entry Point

The runtime discovers your component through one of three conventions (checked in order):

1. **Factory function**: `build_component(config: dict, full_config: dict) -> object`
2. **Named class**: `class Component: ...`
3. **Any class with `register`**: Any class in the module that has a `register` method

The component instance receives two config dicts:
- `config`: Component-specific config section (keyed by component name in `config.toml`)
- `full_config`: The entire config dict

### Required Interface

Every component must implement these methods:

```python
def register(self, mcp) -> None:
    """Register tools with the FastMCP server using @mcp.tool() decorator."""

def export_tools(self) -> list[dict]:
    """Return tool definitions for remote cluster registration.
    Each tool dict: {"name": "...", "description": "...", "input_schema": {...}}"""
```

### Optional Interface

```python
def supports_role(self, role: str) -> bool:
    """Return False to exclude this component from a role ("server" or "client").
    If omitted, component is used in all roles."""

def invoke_tool(self, tool_name: str, arguments: dict) -> dict:
    """Synchronous tool invocation (used in client role)."""

async def ainvoke_tool(self, tool_name: str, arguments: dict) -> dict:
    """Async tool invocation (preferred for client role)."""

def set_remote_invoker(self, fn) -> None:
    """Accept a remote tool invoker function from the cluster server.
    Called by the server when cluster is enabled."""
```

### Tool Definition Format

```python
{
    "name": "my_component_do_something",
    "description": "Human-readable description of what the tool does.",
    "input_schema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            "param2": {"type": "integer", "default": 10}
        },
        "required": ["param1"]
    }
}
```

Tool names must be globally unique across the server and all connected clients. Use a consistent prefix (e.g., `my_component_`).

### `index.json` Registry

Each component must have an entry in `index.json`:

```json
{
    "name": "my_component",
    "description": "Short one-line description.",
    "version": "0.1.0",
    "path": "my_component",
    "entry": "component.py",
    "readme": "README.md",
    "platforms": ["Windows", "Linux", "MacOs"]
}
```

Fields:
- `name`: Must match the directory name. Only `[a-zA-Z0-9_-]` allowed.
- `description`: One-line summary shown in catalog listings.
- `version`: Semantic version string.
- `path`: Directory path relative to repo root.
- `entry`: Entry point filename (default: `component.py`).
- `readme`: README filename (default: `README.md`).
- `platforms`: Array of supported platforms.

### `README.md` Convention

Every component README must follow this structure:

```markdown
# Component Name

Brief description of what the component does and when to use it.

## Tools

- `tool_name(param: type) -> result` — What the tool does.

## Config

```toml
[component_name]
key = "value"
```

## Dependencies

- List any external Python packages
- List any system requirements (e.g., `pywin32` on Windows)

## Usage Notes

Any important notes about behavior, limitations, or setup.

Platforms: Windows|Linux|MacOs
```

**Critical**: The LAST line of the README must follow this format:
```
Platforms: <Platform1>|<Platform2>|...
```
Valid platform tokens: `Windows`, `Linux`, `MacOs` (pipe-separated, no extra spaces). This line is parsed by the catalog system to determine platform compatibility and must match the component's `index.json` `platforms` field.

## Config Convention

Each component reads its config from a TOML section named after the component:

```toml
# config.toml
[my_component]
enabled = true
api_key = "your_key_here"
```

The component receives this section as the `config` dict and the full config as `full_config`.

## Creating a New Component

1. Create a directory under this repo: `my_component/`
2. Add `__init__.py` (empty) and `component.py` (entry point)
3. Implement the required interface: `register(mcp)` and `export_tools()`
4. Write a `README.md` following the convention above
5. Add an entry to `index.json`
6. Test by installing via `catalog_install_component_to_server("my_component")`

## Current Components

| Component | Platforms | Type | Description |
|---|---|---|---|
| `apple_music_macos` | MacOs | MCP Bridge | Auto-bootstrap wrapper for mcp-applemusic |
| `clipboard` | Windows | System MCP | Read/write Windows clipboard with HTML support |
| `exa` | Windows, Linux, MacOs | API MCP | Exa AI web search integration |
| `local_schedule` | Windows, Linux, MacOs | Data MCP | SQLite-backed schedule/calendar manager |
| `windows_manager` | Windows | System MCP | Windows window/application management |
