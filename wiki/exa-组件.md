# exa 组件

`exa` 是跨平台 Web 搜索组件，封装 Exa Search API，为 XiaozhiMCP 提供实时网页搜索、内容摘要和结果压缩能力。它适合需要最新网络信息、限定搜索域名、控制搜索深度或让模型获取简短网页证据的场景。

## 基本信息

| 项 | 内容 |
| --- | --- |
| 组件目录 | `exa/` |
| 入口文件 | `exa/component.py` |
| 组件类 | `ExaSearchComponent` |
| 工厂函数 | `build_component(config)` |
| 工具前缀 | `exa_` |
| 支持平台 | Windows / Linux / MacOs |
| 外部依赖 | `requests` |
| 外部服务 | Exa API |

## 配置

推荐在配置文件中设置 API Key：

```toml
[exa]
api_key = "your_exa_api_key"
base_url = "https://api.exa.ai"
```

也可以使用环境变量：

```bash
export EXA_API_KEY="your_exa_api_key"
export EXA_BASE_URL="https://api.exa.ai"
```

Windows PowerShell：

```powershell
$env:EXA_API_KEY = "your_exa_api_key"
$env:EXA_BASE_URL = "https://api.exa.ai"
```

`base_url` 默认值是 `https://api.exa.ai`，通常不需要修改。

## 工具

### `exa_web_search`

调用 Exa `/search` 接口并返回压缩后的结果。

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `keywords` | string | 必填 | 搜索关键词，建议简短明确 |
| `num_results` | integer | `5` | 期望结果数，组件会限制在 1 到 100 |
| `search_type` | string | `auto` | 搜索策略，可选 `auto`、`fast`、`instant`、`deep-lite`、`deep`、`deep-reasoning` |
| `content_mode` | string | `highlights` | 内容模式，可选 `highlights`、`text`、`summary` |
| `max_characters` | integer | `1400` | 每条内容字符预算，组件限制在 300 到 12000 |
| `max_age_hours` | integer/null | `null` | 可选时效过滤，单位小时 |
| `include_domains_csv` | string | `""` | 逗号分隔的域名白名单 |
| `exclude_domains_csv` | string | `""` | 逗号分隔的域名黑名单 |
| `category` | string | `""` | 可选 Exa category 字段 |
| `summary_query` | string | `""` | 用于 highlights 或 summary 生成的附加 query |
| `output_schema_json` | string | `""` | 可选 JSON schema 字符串，用于结构化输出 |
| `system_prompt` | string | `""` | 可选 Exa system prompt |

## 搜索类型选择

| `search_type` | 建议场景 |
| --- | --- |
| `auto` | 默认选择，由 Exa 决定策略 |
| `fast` | 希望更快返回，接受结果深度较低 |
| `instant` | 需要即时搜索体验 |
| `deep-lite` | 需要比 fast 更深入但控制成本 |
| `deep` | 需要更全面搜索 |
| `deep-reasoning` | 需要复杂问题推理型搜索 |

如果传入未知值，组件会自动回退到 `auto`。

## 内容模式选择

| `content_mode` | 返回内容 | 建议场景 |
| --- | --- | --- |
| `highlights` | 重点片段 | 默认模式，适合大多数问答和引用 |
| `text` | 网页正文文本 | 需要读取原文内容时使用 |
| `summary` | 摘要 | 希望获得更概括的网页信息时使用 |

如果传入未知值，组件会自动回退到 `highlights`。

## 调用示例

基础搜索：

```json
{
  "keywords": "MCP protocol tool registration",
  "num_results": 5,
  "search_type": "auto",
  "content_mode": "highlights"
}
```

限定域名搜索：

```json
{
  "keywords": "FastMCP tool decorator",
  "include_domains_csv": "gofastmcp.com,github.com",
  "exclude_domains_csv": "medium.com",
  "num_results": 3,
  "content_mode": "summary"
}
```

近期内容搜索：

```json
{
  "keywords": "Exa API search recent changes",
  "max_age_hours": 168,
  "search_type": "fast",
  "content_mode": "highlights"
}
```

结构化输出：

```json
{
  "keywords": "latest MCP servers for desktop automation",
  "content_mode": "summary",
  "output_schema_json": "{\"type\":\"object\",\"properties\":{\"projects\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}}}",
  "system_prompt": "Extract project names only."
}
```

## 返回结构

成功时返回：

```json
{
  "success": true,
  "query": "MCP protocol tool registration",
  "searchType": "auto",
  "count": 3,
  "results": [
    {
      "title": "Example Title",
      "url": "https://example.com/article",
      "publishedDate": "2026-05-10",
      "snippet": "Short highlighted content..."
    }
  ]
}
```

如果 Exa 返回结构化 `output` 字段，组件也会把它透传到结果中。

失败时返回：

```json
{
  "success": false,
  "error": "EXA_API_KEY is missing. Set env var EXA_API_KEY first."
}
```

## 实现要点

- `_normalize_search_type()` 校验搜索类型，非法值回退到 `auto`。
- `_normalize_content_mode()` 校验内容模式，非法值回退到 `highlights`。
- `_split_csv()` 把逗号分隔的域名字符串转换为数组。
- `build_search_payload()` 负责构造 Exa 请求体，并限制结果数和字符数。
- `_extract_snippet()` 根据内容模式从 `highlights`、`summary` 或 `text` 中提取片段。
- 返回结果会进行长度控制，超过约 1KB 时缩减到前三条并进一步截断片段。

## 使用注意

- `keywords` 不应传入长段落，建议传搜索词或一句明确问题。
- `output_schema_json` 必须是合法 JSON 字符串，否则会返回 `Invalid search parameters`。
- API Key 不应提交到仓库，生产环境优先使用 `EXA_API_KEY` 环境变量。
- 网络请求超时时间为 20 秒，调用端应准备处理失败返回。
