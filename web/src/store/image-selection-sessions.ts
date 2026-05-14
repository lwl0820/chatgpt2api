"use client";

import {
  deleteBackendSession,
  fetchBackendSession,
  fetchBackendSessions,
  saveBackendSession,
  streamBackendSession,
  type BackendSessionKind,
} from "@/lib/api";

export type ImageSelectionCandidateStatus = "loading" | "ready" | "kept" | "discarded" | "error";
export type ImageSelectionSessionStatus = "running" | "paused" | "idle";

export type ImageSelectionCandidate = {
  id: string;
  taskId?: string;
  status: ImageSelectionCandidateStatus;
  prompt?: string;
  url?: string;
  rel?: string;
  revised_prompt?: string;
  error?: string;
  createdAt: string;
  decidedAt?: string;
};

export type ImageSelectionDecisionHistoryItem = {
  candidateId: string;
  previousStatus: "ready";
  nextStatus: "kept" | "discarded";
  decidedAt: string;
};

export type ImageSelectionSession = {
  id: string;
  title: string;
  prompt: string;
  size: string;
  queueLimit: number;
  failureLimit: number;
  status: ImageSelectionSessionStatus;
  candidates: ImageSelectionCandidate[];
  decisionHistory: ImageSelectionDecisionHistoryItem[];
  createdAt: string;
  updatedAt: string;
  consecutiveFailures: number;
  lastError?: string;
};

export type ImageSelectionSessionDelta = {
  id: string;
  updatedAt?: string;
  fields?: Partial<Omit<ImageSelectionSession, "id" | "candidates">> & { candidates?: ImageSelectionCandidate[] };
  candidates?: {
    upsert?: ImageSelectionCandidate[];
    remove?: string[];
  };
};

const MAX_DECISION_HISTORY = 10;

export type ImageSelectionSessionStats = {
  loading: number;
  ready: number;
  kept: number;
  discarded: number;
  error: number;
  active: number;
};

const IMAGE_SELECTION_SESSION_KIND: BackendSessionKind = "image-selection-session";

function normalizeCandidate(candidate: ImageSelectionCandidate & Record<string, unknown>): ImageSelectionCandidate {
  const status = ["loading", "ready", "kept", "discarded", "error"].includes(String(candidate.status))
    ? candidate.status as ImageSelectionCandidateStatus
    : candidate.url
      ? "ready"
      : "loading";
  return {
    id: String(candidate.id || `${Date.now()}`),
    taskId: typeof candidate.taskId === "string" && candidate.taskId ? candidate.taskId : undefined,
    status,
    prompt: typeof candidate.prompt === "string" && candidate.prompt.trim() ? candidate.prompt : undefined,
    url: typeof candidate.url === "string" && candidate.url ? candidate.url : undefined,
    rel: typeof candidate.rel === "string" && candidate.rel ? candidate.rel : undefined,
    revised_prompt: typeof candidate.revised_prompt === "string" ? candidate.revised_prompt : undefined,
    error: typeof candidate.error === "string" ? candidate.error : undefined,
    createdAt: String(candidate.createdAt || new Date().toISOString()),
    decidedAt: typeof candidate.decidedAt === "string" && candidate.decidedAt ? candidate.decidedAt : undefined,
  };
}

function normalizeDecisionHistoryItem(
  item: ImageSelectionDecisionHistoryItem & Record<string, unknown>,
): ImageSelectionDecisionHistoryItem | null {
  const nextStatus = item.nextStatus === "kept" || item.nextStatus === "discarded" ? item.nextStatus : null;
  if (!item.candidateId || !nextStatus) {
    return null;
  }
  return {
    candidateId: String(item.candidateId),
    previousStatus: "ready",
    nextStatus,
    decidedAt: String(item.decidedAt || new Date().toISOString()),
  };
}

export function normalizeImageSelectionSession(session: ImageSelectionSession & Record<string, unknown>): ImageSelectionSession {
  const candidates = Array.isArray(session.candidates)
    ? session.candidates.map((candidate) => normalizeCandidate(candidate as ImageSelectionCandidate & Record<string, unknown>))
    : [];
  const status = session.status === "running" || session.status === "paused" || session.status === "idle"
    ? session.status
    : "paused";
  const decisionHistory = Array.isArray(session.decisionHistory)
    ? session.decisionHistory
      .map((item) => normalizeDecisionHistoryItem(item as ImageSelectionDecisionHistoryItem & Record<string, unknown>))
      .filter((item): item is ImageSelectionDecisionHistoryItem => Boolean(item))
      .slice(-MAX_DECISION_HISTORY)
    : [];
  const prompt = String(session.prompt || "");
  return {
    id: String(session.id || `${Date.now()}`),
    title: String(session.title || buildImageSelectionTitle(prompt)),
    prompt,
    size: typeof session.size === "string" ? session.size : "",
    queueLimit: Math.max(1, Math.min(100, Number(session.queueLimit || 6))),
    failureLimit: Math.max(1, Math.min(100, Number(session.failureLimit || 5))),
    status,
    candidates,
    decisionHistory,
    createdAt: typeof session.createdAt === "string" ? session.createdAt : "",
    updatedAt: typeof session.updatedAt === "string" ? session.updatedAt : "",
    consecutiveFailures: Math.max(0, Number(session.consecutiveFailures || 0)),
    lastError: typeof session.lastError === "string" ? session.lastError : undefined,
  };
}

export function buildImageSelectionTitle(prompt: string) {
  const trimmed = prompt.trim();
  return trimmed.length <= 12 ? trimmed : `${trimmed.slice(0, 12)}...`;
}

export function getImageSelectionSessionStats(session: ImageSelectionSession): ImageSelectionSessionStats {
  const stats = session.candidates.reduce(
    (acc, candidate) => {
      acc[candidate.status] += 1;
      return acc;
    },
    { loading: 0, ready: 0, kept: 0, discarded: 0, error: 0 },
  );
  return { ...stats, active: stats.loading + stats.ready };
}

export function getKeptImageSelectionPaths(session: ImageSelectionSession | null): string[] {
  if (!session) {
    return [];
  }
  return session.candidates.flatMap((candidate) =>
    candidate.status === "kept" && candidate.rel ? [candidate.rel] : [],
  );
}

export function extractManagedImageRel(url: string): string {
  const value = String(url || "").trim();
  if (!value) {
    return "";
  }
  const marker = "/images/";
  try {
    const parsed = new URL(value, typeof window !== "undefined" ? window.location.origin : "http://localhost");
    const index = parsed.pathname.indexOf(marker);
    if (index >= 0) {
      return decodeURIComponent(parsed.pathname.slice(index + marker.length));
    }
  } catch {
    const index = value.indexOf(marker);
    if (index >= 0) {
      return decodeURIComponent(value.slice(index + marker.length).split(/[?#]/, 1)[0] || "");
    }
  }
  return "";
}

export function sortImageSelectionSessions(sessions: ImageSelectionSession[]) {
  return [...sessions].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function normalizeImageSelectionSessionDelta(delta: ImageSelectionSessionDelta & Record<string, unknown>): ImageSelectionSessionDelta {
  const fields = typeof delta.fields === "object" && delta.fields && !Array.isArray(delta.fields)
    ? delta.fields as ImageSelectionSessionDelta["fields"]
    : undefined;
  const candidates = typeof delta.candidates === "object" && delta.candidates && !Array.isArray(delta.candidates)
    ? delta.candidates as ImageSelectionSessionDelta["candidates"]
    : undefined;
  return {
    id: String(delta.id || ""),
    updatedAt: typeof delta.updatedAt === "string" ? delta.updatedAt : undefined,
    fields,
    candidates: candidates ? {
      upsert: Array.isArray(candidates.upsert)
        ? candidates.upsert.map((candidate) => normalizeCandidate(candidate as ImageSelectionCandidate & Record<string, unknown>))
        : undefined,
      remove: Array.isArray(candidates.remove) ? candidates.remove.map((id) => String(id)) : undefined,
    } : undefined,
  };
}

export function applyImageSelectionSessionDelta(session: ImageSelectionSession, delta: ImageSelectionSessionDelta): ImageSelectionSession {
  if (!delta.id || delta.id !== session.id) {
    return session;
  }
  let next: ImageSelectionSession = { ...session, ...(delta.fields || {}) };
  if (delta.updatedAt) {
    next.updatedAt = delta.updatedAt;
  }
  if (Array.isArray(delta.fields?.candidates)) {
    next.candidates = delta.fields.candidates.map((candidate) => normalizeCandidate(candidate as ImageSelectionCandidate & Record<string, unknown>));
  } else if (delta.candidates) {
    const remove = new Set(delta.candidates.remove || []);
    const upsert = new Map((delta.candidates.upsert || []).map((candidate) => [candidate.id, candidate]));
    const candidates = next.candidates
      .filter((candidate) => !remove.has(candidate.id))
      .map((candidate) => upsert.get(candidate.id) || candidate);
    const existingIds = new Set(candidates.map((candidate) => candidate.id));
    for (const candidate of delta.candidates.upsert || []) {
      if (!existingIds.has(candidate.id)) {
        candidates.push(candidate);
      }
    }
    next.candidates = candidates;
  }
  return normalizeImageSelectionSession(next as ImageSelectionSession & Record<string, unknown>);
}

export async function listImageSelectionSessions(): Promise<ImageSelectionSession[]> {
  const data = await fetchBackendSessions<ImageSelectionSession & Record<string, unknown>>(IMAGE_SELECTION_SESSION_KIND);
  return sortImageSelectionSessions(data.items.map(normalizeImageSelectionSession));
}

export async function getImageSelectionSession(id: string): Promise<ImageSelectionSession | null> {
  try {
    const data = await fetchBackendSession<ImageSelectionSession & Record<string, unknown>>(IMAGE_SELECTION_SESSION_KIND, id);
    return normalizeImageSelectionSession(data.item);
  } catch {
    return null;
  }
}

export async function streamImageSelectionSession(
  id: string,
  options: {
    signal: AbortSignal;
    onSession: (session: ImageSelectionSession) => void;
    onDelta?: (delta: ImageSelectionSessionDelta) => void;
    onDeleted?: (id: string) => void;
  },
): Promise<void> {
  await streamBackendSession<ImageSelectionSession & Record<string, unknown>>(IMAGE_SELECTION_SESSION_KIND, id, {
    signal: options.signal,
    onSession: (session) => options.onSession(normalizeImageSelectionSession(session)),
    onDelta: (delta) => options.onDelta?.(normalizeImageSelectionSessionDelta(delta as ImageSelectionSessionDelta & Record<string, unknown>)),
    onDeleted: options.onDeleted,
  });
}

export async function saveImageSelectionSession(session: ImageSelectionSession): Promise<void> {
  await saveBackendSession(IMAGE_SELECTION_SESSION_KIND, normalizeImageSelectionSession(session));
}

export async function saveImageSelectionSessions(sessions: ImageSelectionSession[]): Promise<void> {
  await Promise.all(
    sessions.map((session) => saveBackendSession(IMAGE_SELECTION_SESSION_KIND, normalizeImageSelectionSession(session))),
  );
}

export async function deleteImageSelectionSession(id: string): Promise<void> {
  await deleteBackendSession(IMAGE_SELECTION_SESSION_KIND, id);
}
