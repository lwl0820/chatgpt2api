"use client";

import localforage from "localforage";

export type ImageSelectionCandidateStatus = "loading" | "ready" | "kept" | "discarded" | "error";
export type ImageSelectionSessionStatus = "running" | "paused" | "idle";

export type ImageSelectionCandidate = {
  id: string;
  taskId?: string;
  status: ImageSelectionCandidateStatus;
  url?: string;
  rel?: string;
  revised_prompt?: string;
  error?: string;
  createdAt: string;
  decidedAt?: string;
};

export type ImageSelectionSession = {
  id: string;
  title: string;
  prompt: string;
  size: string;
  queueLimit: number;
  status: ImageSelectionSessionStatus;
  candidates: ImageSelectionCandidate[];
  createdAt: string;
  updatedAt: string;
  consecutiveFailures: number;
  lastError?: string;
};

export type ImageSelectionSessionStats = {
  loading: number;
  ready: number;
  kept: number;
  discarded: number;
  error: number;
  active: number;
};

const imageSelectionStorage = localforage.createInstance({
  name: "chatgpt2api",
  storeName: "image_selection_sessions",
});

const IMAGE_SELECTION_SESSIONS_KEY = "items";
let imageSelectionWriteQueue: Promise<void> = Promise.resolve();

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
    url: typeof candidate.url === "string" && candidate.url ? candidate.url : undefined,
    rel: typeof candidate.rel === "string" && candidate.rel ? candidate.rel : undefined,
    revised_prompt: typeof candidate.revised_prompt === "string" ? candidate.revised_prompt : undefined,
    error: typeof candidate.error === "string" ? candidate.error : undefined,
    createdAt: String(candidate.createdAt || new Date().toISOString()),
    decidedAt: typeof candidate.decidedAt === "string" && candidate.decidedAt ? candidate.decidedAt : undefined,
  };
}

export function normalizeImageSelectionSession(session: ImageSelectionSession & Record<string, unknown>): ImageSelectionSession {
  const candidates = Array.isArray(session.candidates)
    ? session.candidates.map((candidate) => normalizeCandidate(candidate as ImageSelectionCandidate & Record<string, unknown>))
    : [];
  const status = session.status === "running" || session.status === "paused" || session.status === "idle"
    ? session.status
    : "paused";
  const prompt = String(session.prompt || "");
  return {
    id: String(session.id || `${Date.now()}`),
    title: String(session.title || buildImageSelectionTitle(prompt)),
    prompt,
    size: typeof session.size === "string" ? session.size : "",
    queueLimit: Math.max(1, Math.min(100, Number(session.queueLimit || 6))),
    status,
    candidates,
    createdAt: String(session.createdAt || new Date().toISOString()),
    updatedAt: String(session.updatedAt || new Date().toISOString()),
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

function sortSessions(sessions: ImageSelectionSession[]) {
  return [...sessions].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

function getTimestamp(value: string) {
  const time = new Date(value).getTime();
  return Number.isFinite(time) ? time : 0;
}

function pickLatestSession(current: ImageSelectionSession, next: ImageSelectionSession) {
  return getTimestamp(next.updatedAt) >= getTimestamp(current.updatedAt) ? next : current;
}

function queueImageSelectionWrite<T>(operation: () => Promise<T>): Promise<T> {
  const result = imageSelectionWriteQueue.then(operation);
  imageSelectionWriteQueue = result.then(
    () => undefined,
    () => undefined,
  );
  return result;
}

async function readStoredImageSelectionSessions(): Promise<ImageSelectionSession[]> {
  const items =
    (await imageSelectionStorage.getItem<Array<ImageSelectionSession & Record<string, unknown>>>(
      IMAGE_SELECTION_SESSIONS_KEY,
    )) || [];
  return items.map(normalizeImageSelectionSession);
}

export async function listImageSelectionSessions(): Promise<ImageSelectionSession[]> {
  return sortSessions(await readStoredImageSelectionSessions());
}

export async function saveImageSelectionSession(session: ImageSelectionSession): Promise<void> {
  await queueImageSelectionWrite(async () => {
    const items = await readStoredImageSelectionSessions();
    const nextSession = normalizeImageSelectionSession(session);
    const current = items.find((item) => item.id === nextSession.id);
    const persistedSession = current ? pickLatestSession(current, nextSession) : nextSession;
    await imageSelectionStorage.setItem(
      IMAGE_SELECTION_SESSIONS_KEY,
      sortSessions([persistedSession, ...items.filter((item) => item.id !== persistedSession.id)]),
    );
  });
}

export async function saveImageSelectionSessions(sessions: ImageSelectionSession[]): Promise<void> {
  await queueImageSelectionWrite(async () => {
    const items = await readStoredImageSelectionSessions();
    const sessionMap = new Map(items.map((item) => [item.id, item]));
    for (const session of sessions.map(normalizeImageSelectionSession)) {
      const current = sessionMap.get(session.id);
      sessionMap.set(session.id, current ? pickLatestSession(current, session) : session);
    }
    await imageSelectionStorage.setItem(IMAGE_SELECTION_SESSIONS_KEY, sortSessions([...sessionMap.values()]));
  });
}
