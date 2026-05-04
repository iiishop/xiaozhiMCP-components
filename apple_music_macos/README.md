# Apple Music macOS Bridge

Auto-bootstrap wrapper for `epheterson/mcp-applemusic` on macOS clients.

What it does:

- Clones `https://github.com/epheterson/mcp-applemusic.git` on first run.
- Pulls latest changes on each client startup discovery phase.
- Creates `venv` and runs `pip install -e .` automatically.
- Re-exports discovered tools with `apple_music_` prefix.

Required config in Xiaozhi node `config.toml`:

```toml
[components]
folder = "components"

[apple_music]
enabled = true
repo_url = "https://github.com/epheterson/mcp-applemusic.git"
branch = "main"
install_dir = "~/.xiaozhi/applemusic-mcp"
update_on_startup = true
tool_prefix = "apple_music_"
```

Platforms: MacOs
