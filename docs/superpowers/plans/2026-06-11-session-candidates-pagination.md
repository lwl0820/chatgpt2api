# Session Candidates Pagination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split image-selection session metadata loading from candidate image loading.

**Architecture:** Keep persisted session payloads unchanged. Return lightweight metadata for image-selection session lists and expose candidates as a paginated sub-resource under the existing session route namespace.

**Tech Stack:** FastAPI, Python unittest, Next.js TypeScript, Node test runner.

---

### Task 1: Backend Tests

**Files:**
- Modify: `test/test_session_service.py`
- Modify: `test/test_sessions_api.py`

- [ ] Add tests proving image-selection session lists omit `candidates` and include `candidateCount`.
- [ ] Add tests proving `GET /api/sessions/{kind}/{id}/candidates` returns paginated candidates.
- [ ] Run `uv run python -m unittest test.test_session_service test.test_sessions_api` and confirm the new tests fail before implementation.

### Task 2: Backend Implementation

**Files:**
- Modify: `services/session_service.py`
- Modify: `api/sessions.py`

- [ ] Add service helpers for lightweight public sessions and candidate pagination.
- [ ] Add FastAPI route for candidate pagination with `offset` and `limit` query validation.
- [ ] Run the backend tests and confirm they pass.

### Task 3: Frontend API and Store

**Files:**
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/store/image-selection-sessions.ts`
- Modify: `web/test/image-selection-sessions.test.ts`

- [ ] Add typed paginated candidate response API.
- [ ] Add store helper for loading candidates and merging them into sessions.
- [ ] Add tests for candidate page normalization/merge behavior.

### Task 4: Frontend Consumers

**Files:**
- Modify: `web/src/app/image-select/page.tsx`
- Modify: `web/src/app/image-manager/page.tsx`

- [ ] Load selected image-selection candidates on demand in the selection UI.
- [ ] Load kept paths only when a selection-session filter is active in image manager.
- [ ] Run frontend tests and build.

