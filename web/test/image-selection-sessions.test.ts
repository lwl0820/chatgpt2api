import assert from "node:assert/strict";
import test from "node:test";

import {
  getImageSelectionCandidateThumbnailUrl,
  getImageSelectionSessionStats,
  normalizeImageSelectionSession,
  setImageSelectionCandidateThumbnailStatus,
  type ImageSelectionSession,
} from "../src/store/image-selection-sessions.ts";

function buildSession(overrides: Partial<ImageSelectionSession> = {}): ImageSelectionSession {
  return {
    id: "session-1",
    title: "Session",
    prompt: "cat",
    size: "1:1",
    queueLimit: 6,
    failureLimit: 5,
    status: "paused",
    candidates: [],
    decisionHistory: [],
    createdAt: "2026-01-01T00:00:00.000Z",
    updatedAt: "2026-01-01T00:00:00.000Z",
    consecutiveFailures: 0,
    ...overrides,
  };
}

test("keeps stats reset metadata when normalizing sessions", () => {
  const session = normalizeImageSelectionSession(buildSession({ statsResetAt: "2026-01-01T00:10:00.000Z" }));

  assert.equal(session.statsResetAt, "2026-01-01T00:10:00.000Z");
});

test("resets kept discarded and skipped stats without changing active queue stats", () => {
  const session = buildSession({
    statsResetAt: "2026-01-01T00:10:00.000Z",
    candidates: [
      { id: "kept-before", status: "kept", createdAt: "2026-01-01T00:00:00.000Z", decidedAt: "2026-01-01T00:05:00.000Z" },
      { id: "discarded-before", status: "discarded", createdAt: "2026-01-01T00:00:00.000Z", decidedAt: "2026-01-01T00:06:00.000Z" },
      { id: "error-before", status: "error", createdAt: "2026-01-01T00:00:00.000Z", errorAt: "2026-01-01T00:07:00.000Z" },
      { id: "loading", status: "loading", createdAt: "2026-01-01T00:11:00.000Z" },
      { id: "ready", status: "ready", createdAt: "2026-01-01T00:12:00.000Z" },
    ],
  });

  assert.deepEqual(getImageSelectionSessionStats(session), {
    loading: 1,
    ready: 1,
    kept: 0,
    discarded: 0,
    error: 0,
    active: 2,
  });
});

test("counts new kept discarded and skipped activity after reset", () => {
  const session = buildSession({
    statsResetAt: "2026-01-01T00:10:00.000Z",
    candidates: [
      { id: "kept-before", status: "kept", createdAt: "2026-01-01T00:00:00.000Z", decidedAt: "2026-01-01T00:05:00.000Z" },
      { id: "kept-after", status: "kept", createdAt: "2026-01-01T00:11:00.000Z", decidedAt: "2026-01-01T00:12:00.000Z" },
      { id: "discarded-after", status: "discarded", createdAt: "2026-01-01T00:11:00.000Z", decidedAt: "2026-01-01T00:13:00.000Z" },
      { id: "error-after", status: "error", createdAt: "2026-01-01T00:09:00.000Z", errorAt: "2026-01-01T00:14:00.000Z" },
    ],
  });

  const stats = getImageSelectionSessionStats(session);

  assert.equal(stats.kept, 1);
  assert.equal(stats.discarded, 1);
  assert.equal(stats.error, 1);
});

test("stats reset metadata does not mutate session state used for ordering or selection", () => {
  const before = buildSession({
    statsResetAt: "2026-01-01T00:10:00.000Z",
    candidates: [
      { id: "kept-before", status: "kept", rel: "a.png", createdAt: "2026-01-01T00:00:00.000Z", decidedAt: "2026-01-01T00:05:00.000Z" },
      { id: "ready", status: "ready", url: "/images/b.png", createdAt: "2026-01-01T00:11:00.000Z" },
    ],
  });
  const after = normalizeImageSelectionSession(before);

  assert.equal(after.updatedAt, before.updatedAt);
  assert.equal(after.prompt, before.prompt);
  assert.equal(after.title, before.title);
  assert.equal(after.queueLimit, before.queueLimit);
  assert.equal(after.failureLimit, before.failureLimit);
  assert.equal(after.status, before.status);
  assert.deepEqual(after.candidates.map((candidate) => candidate.status), ["kept", "ready"]);
});

test("candidate thumbnail fallback switches to original after missing is recorded", () => {
  const session = buildSession({
    candidates: [
      { id: "candidate-1", status: "ready", url: "/images/candidate-1.png", createdAt: "2026-01-01T00:00:00.000Z" },
    ],
  });

  const missingSession = setImageSelectionCandidateThumbnailStatus(session, "candidate-1", "missing");

  assert.equal(getImageSelectionCandidateThumbnailUrl(missingSession.candidates[0]), "/images/candidate-1.png");
});

test("normalization preserves missing thumbnail state and clears stale state when url changes", () => {
  const session = normalizeImageSelectionSession(buildSession({
    candidates: [
      { id: "candidate-1", status: "ready", url: "/images/candidate-1.png", thumbnailStatus: "missing", createdAt: "2026-01-01T00:00:00.000Z" },
    ],
  }));

  assert.equal(session.candidates[0].thumbnailStatus, "missing");

  const updated = normalizeImageSelectionSession({
    ...session,
    candidates: [
      { id: "candidate-1", status: "ready", url: "/images/candidate-1-updated.png", createdAt: "2026-01-01T00:00:00.000Z" },
    ],
  });

  assert.equal(updated.candidates[0].thumbnailStatus, "unknown");
});
