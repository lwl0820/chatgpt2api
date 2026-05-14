## Context

选图会话当前把提示词存放在 session 级别，后台队列服务在补齐候选图时读取 `session.prompt` 并提交图片生成任务。候选图记录只保存任务 ID、状态、图片 URL/相对路径、`revised_prompt` 等生成结果信息，没有保存提交任务时使用的原始提示词。

下载候选图时，前端会调用共享图片下载函数并传入 `selectedSession.prompt`。当“下载图片时追加提示词”设置开启时，这个提示词会被写入下载文件尾部。因此，如果用户在旧候选图生成后编辑并保存了会话提示词，下载旧候选图会携带新的会话提示词，而不是旧候选图实际生成时使用的提示词。

图片管理器的提示词反查也有同类问题：它从选图 session 读取 session 级 prompt 并映射到所有候选图路径，无法区分同一 session 内不同时间生成的候选图使用了不同提示词。

## Goals / Non-Goals

**Goals:**

- 让每个新提交的选图候选图记录提交生成任务时使用的提示词。
- 选图下载当前候选图时，追加候选图生成提示词，而不是无条件追加会话当前提示词。
- 图片管理器从选图 session 反查提示词时优先使用候选图级提示词。
- 对历史候选图保持兼容：候选图缺少生成提示词时，继续回退到 session prompt，避免历史下载完全丢失提示词。
- 保持现有候选图状态、撤销历史、下载文件名和原始图片存储文件不变。

**Non-Goals:**

- 不迁移或重写历史选图 session 数据。
- 不尝试从图片内容、任务服务或 `revised_prompt` 反推历史候选图的真实原始提示词。
- 不改变全局“下载图片时追加提示词”设置、尾部载荷格式或图片会话结果下载行为。
- 不改变用户编辑会话提示词后仅影响后续候选图的产品语义。

## Decisions

- 在候选图记录上新增可选的生成提示词字段，例如 `prompt`。后台队列服务创建 loading candidate 时，将当前 `session.prompt` 清理后写入该字段，并用同一个值提交生成任务。备选方案是只在任务完成后从任务数据回填提示词，但任务数据未必持久包含原始 prompt，且 loading 阶段已经能准确知道提交值。
- 候选图状态同步时保留候选图生成提示词。`_task_to_candidate` 在把 loading candidate 转为 ready/error/loading 时继续展开原 candidate 字段，避免结果更新丢失 `prompt`。备选方案是在 ready 阶段重新从 session 读取提示词，但这会重新引入“生成后编辑 session prompt 导致旧图提示词漂移”的问题。
- 前端下载当前候选图时使用 `currentCandidate.prompt || selectedSession.prompt`。这让新数据按候选图生成提示词工作，同时让历史候选图继续沿用原来的 session 级回退行为。备选方案是历史候选图缺失字段时不追加提示词，但这会让历史数据在设置开启时从“可关联提示词”退化为“无提示词”。
- 图片管理器提示词映射优先使用候选图级 `prompt`，缺失时回退到 session prompt。这样同一选图 session 内跨提示词生成的图片能得到更准确的下载载荷，同时保持历史数据兼容。备选方案是完全改用 candidate prompt，不回退 session prompt，但会降低旧数据可用性。
- `revised_prompt` 不作为默认下载提示词来源。它是模型返回的修订提示词，可能与用户提交的原始提示词不同；本变更目标是追溯图片生成请求的输入提示词，而不是模型修订结果。后续如果需要同时保存 revised prompt，可以另立变更定义载荷格式。

## Risks / Trade-offs

- 历史候选图仍可能使用 session 当前提示词作为回退，无法恢复真正生成时提示词 -> 不迁移历史数据，并通过新字段保证变更后的候选图准确。
- 同一 candidate 同时存在 `prompt` 与 `revised_prompt` 可能造成语义混淆 -> 类型和代码命名应明确 `prompt` 表示提交生成任务时的用户提示词，`revised_prompt` 表示模型返回的修订提示词。
- 如果用户在候选图 loading 后立刻编辑 session prompt，loading candidate 必须仍保留旧 prompt -> 在创建 loading candidate 的同一逻辑中冻结 prompt，并避免后续同步从 session 覆盖。
- 图片管理器反查路径可能被多个记录匹配，后写入的映射会覆盖先写入的映射 -> 保持现有覆盖语义，仅改进选图 session 内的提示词来源；更复杂的冲突处理不在本变更范围内。

## Migration Plan

无需数据迁移。发布后，新提交的候选图会携带生成提示词；历史候选图缺失该字段时继续回退到 session prompt。回滚时，前端和图片管理器可继续忽略候选图级提示词字段，已保存字段作为额外数据留在 session 中不影响旧逻辑。

## Open Questions

- 候选图字段名是否使用通用 `prompt`，还是更明确的 `generation_prompt`/`sourcePrompt`；实现时应优先保持前后端命名一致并避免与 `revised_prompt` 混淆。
