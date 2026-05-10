# local_schedule 组件

`local_schedule` 是跨平台本地日程组件，使用 SQLite 保存事件，支持时间段事件、截止日期事件、状态管理和空闲时间查询。它适合在不依赖云端日历服务的情况下，为 XiaozhiMCP 提供轻量级本地计划管理能力。

## 基本信息

| 项 | 内容 |
| --- | --- |
| 组件目录 | `local_schedule/` |
| 入口文件 | `local_schedule/component.py` |
| 数据层 | `LocalScheduleStore` |
| 组件类 | `LocalScheduleComponent` |
| 工具前缀 | `schedule_` |
| 支持平台 | Windows / Linux / MacOs |
| 外部依赖 | 无，使用 Python 标准库 `sqlite3` |
| 默认数据库 | `~/.xiaozhi_mcp/local_schedule/local_schedule.sqlite3` |

## 配置

默认无需配置，数据会保存到用户主目录：

```toml
[local_schedule]
enabled = true
```

自定义数据库位置：

```toml
[local_schedule]
db_path = "D:/data/xiaozhi/local_schedule.sqlite3"
```

macOS 或 Linux 示例：

```toml
[local_schedule]
db_path = "~/.xiaozhi_mcp/local_schedule/local_schedule.sqlite3"
```

## 数据模型

SQLite 表名为 `schedules`，主要字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 自增主键 |
| `title` | text | 事件标题，必填 |
| `description` | text | 事件说明 |
| `schedule_type` | text | `range` 或 `deadline` |
| `status` | text | `未开始`、`进行中`、`已完成` |
| `start_ts` / `end_ts` | integer | 用于范围查询的时间戳 |
| `start_time` / `end_time` | text | ISO 8601 时间字符串 |
| `due_ts` / `due_time` | integer/text | 截止日期事件的到期时间 |
| `created_at` | text | 创建时间 |

组件启动时会自动创建表和索引，并通过 `_ensure_columns()` 为旧表补齐 `schedule_type`、`status`、`due_ts`、`due_time` 等字段。

## 时间格式

所有时间参数使用 ISO 8601 字符串：

```text
2026-05-10T09:00:00
2026-05-10T09:00:00+08:00
2026-05-10T01:00:00Z
```

带时区的输入会转换为 UTC 后移除时区信息保存。例如 `2026-05-10T09:00:00+08:00` 会保存为 `2026-05-10T01:00:00`。

## 工具

### `schedule_list_events`

列出事件，可选按时间范围过滤。过滤逻辑是“事件与查询范围有重叠”：`event.end_ts > start_time` 且 `event.start_ts < end_time`。

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `start_time` | string | `""` | 可选查询开始时间 |
| `end_time` | string | `""` | 可选查询结束时间 |

示例：

```json
{
  "start_time": "2026-05-10T09:00:00",
  "end_time": "2026-05-10T18:00:00"
}
```

### `schedule_add_event`

新增事件。支持两种类型：

| 类型 | 必填时间字段 | 说明 |
| --- | --- | --- |
| `range` | `start_time`、`end_time` | 有开始和结束时间的日程 |
| `deadline` | `due_time` | 截止日期事件，内部也会把 `start_time` 和 `end_time` 设置为 `due_time` |

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `title` | string | 必填 | 事件标题 |
| `schedule_type` | string | `range` | `range` 或 `deadline` |
| `start_time` | string | `""` | 范围事件开始时间 |
| `end_time` | string | `""` | 范围事件结束时间 |
| `due_time` | string | `""` | 截止日期事件到期时间 |
| `status` | string | `未开始` | `未开始`、`进行中`、`已完成` |
| `description` | string | `""` | 事件说明 |

范围事件示例：

```json
{
  "title": "需求评审",
  "schedule_type": "range",
  "start_time": "2026-05-10T09:00:00",
  "end_time": "2026-05-10T10:00:00",
  "status": "未开始",
  "description": "评审组件仓库 Wiki 文档"
}
```

截止日期示例：

```json
{
  "title": "提交发布说明",
  "schedule_type": "deadline",
  "due_time": "2026-05-10T18:00:00",
  "status": "进行中"
}
```

### `schedule_update_event`

更新事件标题、类型和时间字段。未传字段会沿用原值。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `event_id` | integer | 是 | 事件 ID |
| `title` | string | 否 | 新标题 |
| `schedule_type` | string | 否 | `range` 或 `deadline` |
| `start_time` | string | 否 | 新开始时间 |
| `end_time` | string | 否 | 新结束时间 |
| `due_time` | string | 否 | 新截止时间 |

示例：

```json
{
  "event_id": 3,
  "title": "需求评审（延期）",
  "start_time": "2026-05-10T10:00:00",
  "end_time": "2026-05-10T11:00:00"
}
```

### `schedule_update_status`

更新事件状态。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `event_id` | integer | 是 | 事件 ID |
| `status` | string | 是 | `未开始`、`进行中`、`已完成` |

示例：

```json
{
  "event_id": 3,
  "status": "已完成"
}
```

### `schedule_delete_event`

按 ID 删除事件。

示例：

```json
{
  "event_id": 3
}
```

### `schedule_find_free_slots`

查找指定范围内的空闲时间段。组件只把 `range` 类型事件视为忙碌时间，`deadline` 类型不会占用时间段。

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `range_start` | string | 必填 | 查询范围开始时间 |
| `range_end` | string | 必填 | 查询范围结束时间 |
| `min_minutes` | integer | `30` | 最小空闲分钟数 |

示例：

```json
{
  "range_start": "2026-05-10T09:00:00",
  "range_end": "2026-05-10T18:00:00",
  "min_minutes": 45
}
```

返回示例：

```json
{
  "success": true,
  "count": 2,
  "free_slots": [
    {
      "start_time": "2026-05-10T10:00:00",
      "end_time": "2026-05-10T11:30:00",
      "minutes": 90
    }
  ]
}
```

## 校验规则

- `title` 不能为空。
- `schedule_type` 只能是 `range` 或 `deadline`。
- `status` 只能是 `未开始`、`进行中`、`已完成`。
- `range` 事件要求 `end_time` 晚于 `start_time`。
- `deadline` 事件要求 `due_time` 可解析为有效时间。
- `schedule_find_free_slots` 要求 `range_end` 晚于 `range_start`。

## 测试覆盖

仓库已有 `tests/test_local_schedule.py`，覆盖：

- 带时区时间标准化。
- 截止日期事件使用 `due_time` 作为范围字段。
- 状态更新和非法状态校验。
- 时间范围重叠查询。

运行：

```bash
pytest tests/test_local_schedule.py
```
