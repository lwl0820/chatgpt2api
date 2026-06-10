# 上游合并记录

本次合并将 `upstream/main` 的更新并入本地 `main`，同时保留本地已有的选图功能和图片下载追加提示词等行为。

## 保留的本地能力

- 前端导航继续保留 `/image-select` 入口，显示为“选图”。
- 选图相关后端队列、会话类型和前端会话存储继续保留。
- 图片下载 ZIP 和单图下载在启用 `image_download_append_prompt` 时继续追加对应提示词。
- 图片元数据写入仍会在保存图片时记录相对路径对应的时间信息。
- 本地图片相关配置继续保留：`image_global_concurrency`、`image_download_append_prompt`、`image_thumbnail_generation`、`image_cleanup_skip_kept`。

## 接入的上游能力

- 保留上游新增的图片存储、图片稳定等待、超时续轮询和错误关闭逻辑。
- 保留上游新增的 Debug 页面、版本发布弹窗、主题切换和相关 UI 组件。
- 保留上游配置项：`image_settle_enabled`、`image_timeout_retry_secs`、`image_settle_secs`、`auto_relogin_after_refresh`、`image_storage`。

## 验证记录

- 后端语法检查已通过：
  `.venv\Scripts\python.exe -m py_compile api\app.py services\config.py services\image_service.py services\image_task_service.py services\protocol\conversation.py`
- 关键后端单测已通过：
  `.venv\Scripts\python.exe -m unittest test.test_image_metadata_service test.test_config test.test_image_selection_queue_service test.test_frontend_backend_sessions test.test_image_download_prompt`
- 冲突文件和主要目录未发现 Git 冲突标记。
- `git diff --cached --check` 已通过。

## 已知验证缺口

前端 `npm run build` 尚未完成。失败原因是本地 `node_modules` 缺少上游已在 `web/package.json` 声明的依赖：`radix-ui`、`react-markdown`、`remark-gfm`。

已尝试 `npm install`，但联网审批通道返回 `503 Service Unavailable`，无法获得执行授权；已尝试 `npm install --offline`，但本机 npm 缓存不完整，返回 `ENOTCACHED`。后续在允许联网安装依赖后，应先在 `web/` 目录运行 `npm install`，再重新运行 `npm run build`。

## 其他说明

- `openspec/` 已移除。
- `web/pnpm-lock.yaml` 是未跟踪文件，未纳入本次合并提交。
