# clipboard 组件

`clipboard` 是 Windows 剪贴板组件，提供读取和写入剪贴板文本的 MCP 工具，并支持写入 CF_HTML 格式的富文本内容。它适合让助手把整理后的文本、代码片段、表格或带格式的 HTML 内容复制到用户当前 Windows 桌面环境。

## 基本信息

| 项 | 内容 |
| --- | --- |
| 组件目录 | `clipboard/` |
| 入口文件 | `clipboard/component.py` |
| 组件类 | `ClipboardComponent` |
| 工具前缀 | `clipboard_` |
| 支持平台 | Windows |
| 外部依赖 | `pywin32` |
| 配置 | 无必填配置 |

## 安装依赖

```bash
pip install pywin32
```

该组件直接调用 Windows 剪贴板 API。非 Windows 环境或缺少 `pywin32` 时，工具调用会失败并返回错误信息。

## 配置

组件无需额外配置，启用后即可使用：

```toml
[clipboard]
enabled = true
```

## 工具

### `clipboard_set`

写入 Windows 剪贴板。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `content` | string | 是 | 写入剪贴板的纯文本内容 |
| `content_html` | string | 否 | 可选 HTML 片段，用于写入 CF_HTML 富文本 |

基础示例：

```json
{
  "content": "复制到剪贴板的文本"
}
```

富文本示例：

```json
{
  "content": "会议结论：同意上线",
  "content_html": "<p><b>会议结论</b>：<span style=\"color:green\">同意上线</span></p>"
}
```

成功返回：

```json
{
  "success": true,
  "length": 9,
  "has_html": false
}
```

### `clipboard_get`

读取当前 Windows 剪贴板文本。

参数：无。

示例调用：

```json
{}
```

成功返回：

```json
{
  "success": true,
  "content": "当前剪贴板内容",
  "length": 8
}
```

## CF_HTML 支持

当传入 `content_html` 时，组件会构造 Windows 标准 CF_HTML payload：

```text
Version:0.9
StartHTML:0000000105
EndHTML:0000000190
StartFragment:0000000137
EndFragment:0000000158
<html><body><!--StartFragment-->...<!--EndFragment--></body></html>
```

实现函数 `build_cf_html_payload(fragment_html)` 会自动计算 `StartHTML`、`EndHTML`、`StartFragment` 和 `EndFragment` 字节偏移。调用者只需要传入 HTML 片段，不需要手动添加 CF_HTML 头。

## 使用场景

| 场景 | 推荐调用 |
| --- | --- |
| 复制普通文本 | 只传 `content` |
| 复制 Markdown 渲染后的 HTML | 同时传 `content` 和 `content_html` |
| 读取用户刚复制的内容 | 调用 `clipboard_get` |
| 给 Word、Outlook、飞书等富文本编辑器粘贴格式 | 传入简洁 HTML 片段 |

## 实现要点

- `set_windows_clipboard_text()` 使用 `CF_UNICODETEXT` 写入纯文本。
- 当 `content_html` 非空时，注册 `HTML Format` 剪贴板格式并写入 CF_HTML 字节。
- `get_windows_clipboard_text()` 优先读取 `CF_UNICODETEXT`，其次读取 `CF_TEXT` 并按 UTF-8 容错解码。
- 每次读写都会在 `finally` 中关闭剪贴板句柄，避免占用系统资源。

## 错误处理

典型错误包括：

| 错误 | 原因 | 处理建议 |
| --- | --- | --- |
| `No module named win32clipboard` | 未安装 `pywin32` | 执行 `pip install pywin32` |
| `OpenClipboard` 失败 | 其他程序短暂占用剪贴板 | 稍后重试 |
| 富文本粘贴无格式 | 目标程序不支持 CF_HTML 或 HTML 片段过于复杂 | 简化 HTML，保留纯文本兜底 |

## 安全注意

- 剪贴板是用户级全局资源，写入会覆盖用户现有剪贴板内容。
- 不建议把密码、Token 或私钥写入剪贴板。
- 读取剪贴板可能包含敏感信息，调用方应避免把结果写入日志。
