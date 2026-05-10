# clipboard

Windows clipboard read/write MCP component. Supports plain text and optional HTML rich-text payload (CF_HTML format) for preserving formatting when pasting.

## Tools

- `clipboard_set(content, content_html)` — Copy text to the Windows clipboard. Use `content_html` for rich-text formatting.
- `clipboard_get()` — Read current Windows clipboard text content.

## Dependencies

- `pywin32` (Windows clipboard API)

## Usage Notes

- Windows only. Requires `pywin32` installed (`pip install pywin32`).
- The HTML payload uses the CF_HTML clipboard format for rich-text support.

Platforms: Windows
