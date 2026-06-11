# 图片选择会话候选图分页设计

## 背景

`GET /api/sessions?kind=image-selection-session` 之前会返回每个选图会话的完整 `candidates` 数组。选图会话累计图片较多时，列表页、图片管理页只需要会话元数据，却会被迫下载所有候选图数据，导致接口响应慢、前端初始化慢。

## 目标

- 会话列表接口只返回会话元数据，不返回 `candidates`。
- 候选图片通过独立接口按需分页加载。
- 保存、删除、SSE 更新仍沿用现有 session 存储模型，避免迁移历史数据。

## 接口设计

### 会话列表

`GET /api/sessions?kind=image-selection-session`

返回的每个会话不包含 `candidates` 字段，并额外提供：

- `candidateCount`：候选图总数。

其他会话类型保持现有行为。

### 候选图分页

`GET /api/sessions/{kind}/{session_id}/candidates?offset=0&limit=50`

返回：

```json
{
  "items": [],
  "total": 120,
  "offset": 0,
  "limit": 50,
  "has_more": true
}
```

约束：

- `offset >= 0`。
- `1 <= limit <= 200`。
- 越权或会话不存在返回 404。
- 目前只有包含 `candidates` 数组的会话会返回图片列表，主要服务 `image-selection-session`。

## 前端调整

- `listImageSelectionSessions()` 只拿轻量会话。
- 新增 `listImageSelectionSessionCandidates(id, options)` 分页加载候选图。
- 选图页在选中会话时分页加载候选图，滚动/需要更多时继续拉取。
- 图片管理页只在用户选择某个选图会话过滤时加载该会话的候选图，避免初始化全量拉取。

