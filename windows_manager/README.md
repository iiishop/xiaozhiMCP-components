# windows_manager

Windows desktop window/application management MCP component. Enumerate, find, focus, and close windows, plus retrieve process performance stats.

## Tools

- `windows_list_open_apps()` — List all visible top-level windows.
- `windows_find_apps(keyword)` — Find open windows by title keyword.
- `windows_focus_app(keyword, match_index)` — Focus a window by keyword, with multi-strategy activation (direct foreground, topmost toggle, alt-key simulation).
- `windows_close_app(keyword, match_index)` — Close a window via `WM_CLOSE` message.
- `windows_list_app_performance(keyword)` — List windows with CPU seconds and working set (MB), optionally filtered by keyword.

## Config

This component has no required or optional configuration. It works out of the box when enabled.

## Dependencies

- `pywin32` (Win32 GUI and process APIs)
- PowerShell (for process performance stats via `Get-Process`)

## Usage Notes

- Windows only. Requires `pywin32` installed (`pip install pywin32`).
- Window focusing uses a three-strategy fallback to maximize success rate.
- Duplicate windows (same title + PID) are deduplicated.

Platforms: Windows
