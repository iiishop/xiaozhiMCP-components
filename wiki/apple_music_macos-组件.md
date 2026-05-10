# apple_music_macos 组件

`apple_music_macos` 是 macOS 专用的 Apple Music MCP 桥接组件。它不会直接实现 Apple Music 操作，而是在 macOS client 侧自动准备 `epheterson/mcp-applemusic`，通过 stdio MCP 协议发现上游工具，并把工具名称统一加上 `apple_music_` 前缀后暴露给 XiaozhiMCP。

## 基本信息

| 项 | 内容 |
| --- | --- |
| 组件目录 | `apple_music_macos/` |
| 入口文件 | `apple_music_macos/component.py` |
| 组件类 | `Component` |
| 工具前缀 | `apple_music_` |
| 支持平台 | MacOs |
| 支持角色 | `client` |
| 外部依赖 | `git`、`python3`、`pip` |
| 外部仓库 | `https://github.com/epheterson/mcp-applemusic.git` |

## 适用场景

- 用户在 macOS 上使用 Apple Music。
- 需要通过 XiaozhiMCP 调用第三方 Apple Music MCP 工具。
- 希望组件自动处理克隆、更新、虚拟环境和安装流程。

不适合的场景：

- Windows 或 Linux 环境。
- server 角色直接运行 Apple Music 工具。
- 无法访问 GitHub 或无法创建 Python 虚拟环境的受限环境。

## 配置

```toml
[apple_music_macos]
enabled = true
install_dir = "~/.xiaozhi/applemusic-mcp"
update_on_startup = true
```

字段说明：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `enabled` | bool/string | `true` | 是否启用组件，支持 `1`、`true`、`yes`、`on` |
| `install_dir` | string | `~/.xiaozhi/applemusic-mcp` | 上游仓库克隆和虚拟环境目录 |
| `update_on_startup` | bool/string | `true` | 启动发现阶段是否 fetch/pull 上游仓库 |

`repo_url`、`branch` 和工具前缀目前在代码中固定：

```python
repo_url = "https://github.com/epheterson/mcp-applemusic.git"
branch = "main"
tool_prefix = "apple_music_"
```

## 启动流程

组件在 `_prepare_apple_music(full_config)` 中执行准备工作：

1. 检查平台：只有 `platform.system().lower() == "darwin"` 才继续。
2. 读取 `[apple_music_macos]` 配置。
3. 如果 `enabled` 为 false，返回不可用。
4. 若 `install_dir` 中没有 `.git`，执行 `git clone --branch main`。
5. 如果仓库已存在且 `update_on_startup = true`，执行 `git fetch` 和 `git pull --ff-only`。
6. 如果虚拟环境不存在，执行 `python3 -m venv <install_dir>/venv`。
7. 执行 `<venv>/bin/python -m pip install -e <install_dir>`。
8. 返回 stdio MCP 启动配置：命令、参数、工具前缀和环境变量。

## 工具发现

`Component.export_tools()` 会启动或复用 `_StdioMCPClient`，向上游 MCP 服务发送 `tools/list` 请求。上游返回的每个工具会被转换为：

```python
{
    "name": f"apple_music_{raw_name}",
    "description": raw_description,
    "input_schema": raw_input_schema,
    "_raw_name": raw_name,
}
```

因此实际工具列表取决于安装时的 `mcp-applemusic` 版本。例如上游工具名如果是 `search`，在 XiaozhiMCP 中会暴露为 `apple_music_search`。

## 工具调用

调用 `apple_music_` 前缀工具时，`invoke_tool()` 会：

1. 确保桥接进程已启动。
2. 在 `export_tools()` 结果中找到匹配工具。
3. 去掉组件侧前缀，使用 `_raw_name` 调用上游 MCP 工具。
4. 返回上游 `tools/call` 结果。

调用示例：

```json
{
  "tool": "apple_music_search",
  "arguments": {
    "query": "Daft Punk",
    "type": "artist"
  }
}
```

具体参数以当前上游 `mcp-applemusic` 暴露的 schema 为准。

## stdio MCP 通信

组件内置 `_StdioMCPClient`，使用 MCP stdio 协议的 `Content-Length` framing：

```text
Content-Length: 123

{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

启动后先发送 `initialize`，再发送 `notifications/initialized`，随后可执行 `tools/list` 和 `tools/call`。

## 角色与平台限制

```python
def supports_role(self, role: str) -> bool:
    return role == "client" and platform.system().lower() == "darwin"
```

这表示组件只应在 macOS client 侧启用。非 macOS 或非 client 角色下，组件不应参与工具注册。

## 常见问题

| 问题 | 原因 | 处理建议 |
| --- | --- | --- |
| 工具列表为空 | 非 macOS、组件禁用或准备流程失败 | 检查系统平台、`enabled` 配置和错误日志 |
| `clone applemusic repo failed` | 无法访问 GitHub 或 git 不可用 | 安装 git，检查网络和代理 |
| `create applemusic venv failed` | `python3` 不可用或目录无权限 | 安装 Python 3，检查 `install_dir` 权限 |
| `install applemusic package failed` | pip 安装失败 | 手动进入 `install_dir` 查看上游依赖错误 |
| 调用未知工具 | 工具名不存在或上游版本变化 | 先重新获取 `export_tools()` 工具清单 |

## 使用注意

- 首次运行会克隆和安装上游仓库，耗时取决于网络和 pip 速度。
- `update_on_startup = true` 会在每次启动发现阶段拉取最新代码，稳定部署可考虑设为 `false`。
- 上游工具 schema 和行为由 `mcp-applemusic` 决定，本组件只做自动准备和代理。
- `_raw_name` 是内部字段，用于把前缀工具映射回上游原始工具名，调用方不需要传入。
