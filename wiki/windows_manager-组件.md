# windows_manager 组件

`windows_manager` 是 Windows 桌面窗口管理组件，提供窗口枚举、关键词查找、聚焦、关闭和进程性能读取能力。它适合让 XiaozhiMCP 在 Windows 客户端上辅助用户切换应用、定位窗口或观察桌面应用资源占用。

## 基本信息

| 项 | 内容 |
| --- | --- |
| 组件目录 | `windows_manager/` |
| 入口文件 | `windows_manager/component.py` |
| 组件类 | `WindowsManagerComponent` |
| 工具前缀 | `windows_` |
| 支持平台 | Windows |
| 外部依赖 | `pywin32`、PowerShell |
| 配置 | 无必填配置 |

## 安装依赖

```bash
pip install pywin32
```

`windows_list_app_performance` 会调用 PowerShell `Get-Process` 获取 CPU 秒数和工作集内存，因此系统需要可用的 PowerShell。

## 配置

组件无需额外配置：

```toml
[windows_manager]
enabled = true
```

## 工具

### `windows_list_open_apps`

列出当前所有可见顶层窗口。组件会过滤无标题窗口和 owner window，并按 `title + pid` 去重。

参数：无。

返回示例：

```json
{
  "success": true,
  "count": 2,
  "apps": [
    {"title": "Google Chrome", "pid": 12040},
    {"title": "Visual Studio Code", "pid": 8840}
  ]
}
```

### `windows_find_apps`

按窗口标题关键词查找窗口，大小写不敏感。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 是 | 标题关键词 |

示例：

```json
{
  "keyword": "Chrome"
}
```

### `windows_focus_app`

按关键词聚焦窗口。当多个窗口匹配时，使用 `match_index` 选择第几个匹配项，索引从 1 开始。

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 必填 | 标题关键词 |
| `match_index` | integer | `1` | 匹配序号 |

示例：

```json
{
  "keyword": "Code",
  "match_index": 1
}
```

返回示例：

```json
{
  "success": true,
  "keyword": "Code",
  "match_index": 1,
  "window": {"title": "Visual Studio Code", "pid": 8840},
  "activated": true,
  "strategy": "direct"
}
```

聚焦策略按顺序尝试：

1. `direct`：`ShowWindow`、`BringWindowToTop`、`SetForegroundWindow`。
2. `topmost_toggle`：临时置顶再取消置顶后设置前台窗口。
3. `alt_key`：模拟 Alt 键后再次设置前台窗口。

### `windows_close_app`

按关键词和匹配序号关闭窗口。实现上发送 `WM_CLOSE` 消息，是否真正退出由目标应用决定。

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 必填 | 标题关键词 |
| `match_index` | integer | `1` | 匹配序号 |

示例：

```json
{
  "keyword": "Notepad",
  "match_index": 1
}
```

### `windows_list_app_performance`

列出窗口并合并进程性能数据，可选按标题关键词过滤。

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | `""` | 可选标题关键词 |

返回示例：

```json
{
  "success": true,
  "keyword": "Chrome",
  "count": 1,
  "apps": [
    {
      "title": "Google Chrome",
      "pid": 12040,
      "cpu_seconds": 32.172,
      "working_set_mb": 418.512
    }
  ]
}
```

## 实现要点

- `_load_win32_modules()` 延迟导入 `win32con`、`win32gui`、`win32process`，避免非 Windows 或缺依赖环境在扫描组件时崩溃。
- `list_open_windows()` 使用 `EnumWindows` 枚举窗口，只保留可见、无 owner、标题非空的顶层窗口。
- `normalize_windows()` 按 `title + pid` 去重，并按标题排序。
- `filter_windows_by_keyword()` 进行大小写不敏感标题过滤。
- `select_window_match()` 使用从 1 开始的 `match_index`，更符合用户口语习惯。
- `_fetch_process_stats()` 调用 PowerShell `Get-Process -Id ... | ConvertTo-Json`，再合并 CPU 和内存数据。

## 使用注意

- 该组件只适用于 Windows 桌面会话，不能用于无 GUI 的服务环境。
- Windows 前台窗口限制可能导致聚焦失败，组件已内置多策略兜底，但不能保证 100% 成功。
- `windows_close_app` 发送的是关闭请求，不会强制杀进程。
- 标题关键词可能匹配多个窗口，执行聚焦或关闭前建议先调用 `windows_find_apps` 查看结果。
- 非 Windows 或未安装 `pywin32` 时，工具会返回 `windows_manager is only available on Windows with pywin32 installed (pip install pywin32).`

## 推荐调用流程

查找并聚焦应用：

```json
{
  "tool": "windows_find_apps",
  "arguments": {"keyword": "Chrome"}
}
```

确认目标后：

```json
{
  "tool": "windows_focus_app",
  "arguments": {"keyword": "Chrome", "match_index": 1}
}
```

查看资源占用：

```json
{
  "tool": "windows_list_app_performance",
  "arguments": {"keyword": ""}
}
```
