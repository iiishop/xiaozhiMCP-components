# exa

Exa AI web search MCP component. Provides neural web search via the Exa API with configurable search types, content modes, and domain filtering.

## Tools

- `exa_web_search(keywords, num_results, search_type, content_mode, max_characters, max_age_hours, include_domains_csv, exclude_domains_csv, category, summary_query, output_schema_json, system_prompt)` — Search the web using Exa's neural search engine.
  - `search_type`: `auto`, `fast`, `instant`, `deep-lite`, `deep`, `deep-reasoning`
  - `content_mode`: `highlights`, `text`, `summary`

## Config

```toml
[exa]
api_key = "your_exa_api_key"
base_url = "https://api.exa.ai"
```

Alternatively, set the `EXA_API_KEY` environment variable.

## Dependencies

- `requests` (HTTP client)

## Usage Notes

- Response size is auto-trimmed to stay under ~1KB for LLM context efficiency.
- Cross-platform: works on Windows, Linux, and macOS.

Platforms: Windows|Linux|MacOs
