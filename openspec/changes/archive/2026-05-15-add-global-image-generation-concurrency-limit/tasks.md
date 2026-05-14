## 1. Backend Configuration

- [x] 1.1 Add `image_global_concurrency` to `ConfigStore` with default `3`, minimum `1`, and inclusion in `config.get()`.
- [x] 1.2 Normalize `image_global_concurrency` in `ConfigStore.update()` so invalid, zero, negative, or missing values cannot be persisted as active runtime values.
- [x] 1.3 Add config tests covering default value, valid update, and invalid value normalization.

## 2. Image Task Scheduling

- [x] 2.1 Refactor `ImageTaskService` submission so new tasks are persisted as `queued` and scheduled through a service-owned global scheduler.
- [x] 2.2 Track queued task execution payloads in memory and start only the oldest queued tasks while running count is below `config.image_global_concurrency`.
- [x] 2.3 Update task completion paths to release a global running slot and schedule the next queued task after success or error.
- [x] 2.4 Preserve duplicate `client_task_id`, task polling, task cleanup, logging, and startup recovery behavior.
- [x] 2.5 Add image task service tests proving queued visibility at the limit, next-task start after slot release, shared limit across generation/edit modes, and unchanged duplicate submission behavior.

## 3. Settings UI

- [x] 3.1 Extend `SettingsConfig` and settings store normalization/save logic with `image_global_concurrency`.
- [x] 3.2 Add a settings store setter for the new field with the same input flow as existing numeric image settings.
- [x] 3.3 Add the “全局生图并发数” input to `ConfigCard` near the existing image concurrency settings with explanatory help text.

## 4. Verification

- [x] 4.1 Run backend tests covering config and image task scheduling.
- [x] 4.2 Run frontend lint/type checks or the repository's available frontend verification command.
- [x] 4.3 Run `openspec status --change add-global-image-generation-concurrency-limit` and confirm the change is apply-ready.
