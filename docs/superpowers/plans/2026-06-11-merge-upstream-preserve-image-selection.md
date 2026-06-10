# Merge Upstream Preserve Image Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `https://github.com/basketikun/chatgpt2api` 的上游更新吸收到当前分支，同时保留本地分支特有的选图功能，完成后移除 `openspec/`。

**Architecture:** 以当前工作区为准保护未提交的选图相关改动，先新增上游 remote 并 fetch，再用提交图和文件级 diff 判断上游更新范围。合并时优先接受上游通用能力变更，保留本地 `image-selection`、图片元数据和前端选图页面/状态管理相关实现，并通过后端单测和前端构建验证。

**Tech Stack:** Python/FastAPI 后端、pytest/unittest 测试、Next.js/TypeScript 前端、Git remote/merge。

---

### Task 1: 建立合并上下文

**Files:**
- Read: `openspec/specs/image-selection-workflow/spec.md`
- Read: `openspec/specs/backend-session-management/spec.md`
- Read: `services/image_selection_queue_service.py`
- Read: `web/src/app/image-select/page.tsx`
- Read: `web/src/store/image-selection-sessions.ts`

- [ ] **Step 1: 检查工作区和远端**

Run: `git status --short --branch`
Expected: 显示当前分支和未提交文件，用来避免覆盖用户已有改动。

Run: `git remote -v`
Expected: 确认是否已有 `basketikun` 上游 remote。

- [ ] **Step 2: 梳理选图功能边界**

Run: `rg -n "image-selection|选图|ImageSelection|selection" services web/src test openspec`
Expected: 找到后端队列服务、会话 API、前端选图页、测试和 openspec 说明。

### Task 2: 获取上游并分析差异

**Files:**
- Modify: `.git/config` through `git remote add upstream https://github.com/basketikun/chatgpt2api.git`

- [ ] **Step 1: 添加上游 remote**

Run: `git remote add upstream https://github.com/basketikun/chatgpt2api.git`
Expected: 如果 remote 不存在则成功；如果已经存在则跳过或更新 URL。

- [ ] **Step 2: 拉取上游**

Run: `git fetch upstream`
Expected: 获取 `upstream/main`。

- [ ] **Step 3: 比较提交和文件**

Run: `git log --oneline --left-right --cherry-pick main...upstream/main`
Expected: 列出本地和上游各自独有提交。

Run: `git diff --name-status main...upstream/main`
Expected: 明确哪些文件需要吸收上游更新。

### Task 3: 合并上游并保留选图

**Files:**
- Modify: 由 `git merge upstream/main` 冲突结果决定
- Preserve: `services/image_selection_queue_service.py`
- Preserve: `api/sessions.py`
- Preserve: `services/session_service.py`
- Preserve: `web/src/app/image-select/page.tsx`
- Preserve: `web/src/store/image-selection-sessions.ts`
- Preserve: `test/test_image_selection_queue_service.py`
- Preserve: `web/test/image-selection-sessions.test.ts`

- [ ] **Step 1: 执行合并**

Run: `git merge upstream/main`
Expected: 自动合并或进入冲突状态。

- [ ] **Step 2: 解决冲突**

Use: 对通用 README、模型、配置、依赖、API 兼容层吸收上游；对选图会话、候选队列、保留/丢弃、图片管理筛选、图片元数据持久化保留本地实现。

- [ ] **Step 3: 检查选图入口仍存在**

Run: `rg -n "image-select|选图|image selection|ImageSelection" web/src services api test`
Expected: 选图页面、服务、测试仍存在。

### Task 4: 移除 OpenSpec 并验证

**Files:**
- Delete: `openspec/`
- Modify: `.opencode/commands/opsx-propose.md` only if it references removed OpenSpec workflow and no longer applies

- [ ] **Step 1: 移除 OpenSpec 文件夹**

Run: `Remove-Item -Recurse -Force openspec`
Expected: `openspec/` 不再存在。

- [ ] **Step 2: 运行后端测试**

Run: `.venv\Scripts\python.exe -m pytest test/test_config.py test/test_image_metadata_service.py test/test_image_selection_queue_service.py`
Expected: PASS。

- [ ] **Step 3: 运行前端验证**

Run: `npm run build` from `web/`
Expected: Next.js build succeeds。

- [ ] **Step 4: 最终审计**

Run: `git status --short`
Expected: 只有预期合并、选图保留、openspec 删除和计划文档变更。

Run: `rg -n "image-select|选图|image selection|ImageSelection" web/src services api test`
Expected: 仍能证明选图功能入口和实现存在。
