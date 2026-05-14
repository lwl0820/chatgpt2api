## 1. OpenSpec 文档

- [x] 1.1 将 proposal、design、spec 和 tasks 内容改为中文表述。
- [x] 1.2 将规格和设计从 `createdAt` 排序调整为 `updatedAt` 排序，并明确 `updatedAt` 只由创建和配置编辑更新。

## 2. 会话排序与时间语义

- [x] 2.1 更新 `web/src/store/image-selection-sessions.ts`，让 `sortImageSelectionSessions()` 只按 `updatedAt` 倒序排序，不做额外兜底。
- [x] 2.2 更新选图页的会话持久化和实时更新逻辑，继续复用共享排序函数。
- [x] 2.3 移除生图任务、候选图决策、撤销、暂停和继续等非配置操作对会话 `updatedAt` 的写入。
- [x] 2.4 保留新建会话和配置编辑保存时对 `updatedAt` 的写入。

## 3. 验证

- [x] 3.1 静态检查选图页和图片管理页都通过共享列表排序获得更新时间倒序结果。
- [x] 3.2 运行 OpenSpec 校验并修复问题。
- [x] 3.3 运行 Web 前端构建或等价 TypeScript 校验并修复回归。
