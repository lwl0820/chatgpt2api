## Why

当前图片任务提交后会立即启动后台线程，已有的“单账号图片并发”只能限制每个账号同时使用次数，不能限制整个系统同时运行的生图任务总量。选图队列、普通文生图和图生图并行触发时，可能同时占用过多上游请求、线程和账号槽位，增加失败率和部署资源压力。

## What Changes

- 在系统设置中新增“全局生图并发数”，用于限制所有图片生成任务同时运行的总数。
- 后端持久化并暴露该设置，缺失或无效时使用安全默认值。
- 图片任务调度在启动上游文生图或图生图调用前遵守全局并发限制，超出限制的任务保持排队，直到运行槽位释放。
- 保留现有单账号图片并发限制；全局限制控制系统总并发，单账号限制继续控制每个账号的并发使用。
- 不改变任务提交、轮询、成功、失败、日志和图片保存的外部 API 语义。

## Capabilities

### New Capabilities
- `global-image-generation-concurrency`: Covers configuring, persisting, displaying, and enforcing a system-wide concurrent image generation task limit.

### Modified Capabilities
- None.

## Impact

- Backend config store and settings API payloads need a new positive integer field, likely `image_global_concurrency`.
- Image task service needs queue-aware execution so submitted tasks can remain queued until a global slot is available.
- Settings UI and client settings store need to load, edit, validate, and save the new field alongside existing image settings.
- Tests should cover default config behavior, settings updates, queueing/enforcement in image task execution, and UI/API type normalization where applicable.
