# Apple Music macOS Bridge

Auto-bootstrap wrapper for `epheterson/mcp-applemusic` on macOS clients.

What it does:

- Clones `https://github.com/epheterson/mcp-applemusic.git` on first run.
- Pulls latest changes on each client startup discovery phase.
- Creates venv and runs `pip install -e .` automatically.
- Re-exports discovered tools with `apple_music_` prefix.

## Tools

All upstream `mcp-applemusic` tools are proxied with an `apple_music_` prefix (e.g., `apple_music_playlist`, `apple_music_search`). The exact tool list depends on the installed version of `mcp-applemusic`.

## Config

```toml
[apple_music_macos]
enabled = true
install_dir = "~/.xiaozhi/applemusic-mcp"
update_on_startup = true
```

## Dependencies

- `git`, `python3`, `pip`
- External repo: `https://github.com/epheterson/mcp-applemusic.git`

## Usage Notes

- macOS only (`platform.system() == "darwin"`).
- `repo_url`, `branch`, and tool prefix are hardcoded in the component.
- Auto-updates on each startup discovery phase when `update_on_startup = true`.

Platforms: MacOs
