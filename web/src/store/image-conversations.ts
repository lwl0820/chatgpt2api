"use client";

import {
  deleteBackendSession,
  fetchBackendSessions,
  saveBackendSession,
  type BackendSessionKind,
  type ImageModel,
} from "@/lib/api";

export type ImageConversationMode = "generate" | "edit";

export type StoredReferenceImage = {
  name: string;
  type: string;
  dataUrl: string;
};

export type StoredImage = {
  id: string;
  taskId?: string;
  status?: "loading" | "success" | "error";
  taskStatus?: "queued" | "running";
  progress?: string;
  b64_json?: string;
  url?: string;
  revised_prompt?: string;
  error?: string;
  startTime?: number;
  elapsedSecs?: number;
  elapsedUpdatedAt?: number;
  durationMs?: number;
};

export type ImageTurnStatus = "queued" | "generating" | "success" | "error";

export type ImageTurn = {
  id: string;
  prompt: string;
  model: ImageModel;
  mode: ImageConversationMode;
  referenceImages: StoredReferenceImage[];
  count: number;
  size: string;
  ratio: string;
  tier: string;
  quality: string;
  images: StoredImage[];
  createdAt: string;
  status: ImageTurnStatus;
  error?: string;
  promptDeleted?: boolean;
  resultsDeleted?: boolean;
};

export type ImageConversation = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  turns: ImageTurn[];
};

export type ImageConversationStats = {
  queued: number;
  running: number;
};

const IMAGE_CONVERSATION_KIND: BackendSessionKind = "image-conversation";

function normalizeStoredImage(image: StoredImage): StoredImage {
  const normalized = {
    ...image,
    taskId: typeof image.taskId === "string" && image.taskId ? image.taskId : undefined,
    taskStatus: image.taskStatus === "queued" || image.taskStatus === "running" ? image.taskStatus : undefined,
    url: typeof image.url === "string" && image.url ? image.url : undefined,
    revised_prompt: typeof image.revised_prompt === "string" ? image.revised_prompt : undefined,
    startTime: typeof image.startTime === "number" ? image.startTime : undefined,
    elapsedSecs: typeof image.elapsedSecs === "number" ? image.elapsedSecs : undefined,
    elapsedUpdatedAt: typeof image.elapsedUpdatedAt === "number" ? image.elapsedUpdatedAt : undefined,
    durationMs: typeof image.durationMs === "number" ? image.durationMs : undefined,
  };
  if (image.status === "loading" || image.status === "error" || image.status === "success") {
    return normalized;
  }
  return {
    ...normalized,
    status: image.b64_json || image.url ? "success" : "loading",
  };
}

function normalizeReferenceImage(image: StoredReferenceImage): StoredReferenceImage {
  return {
    name: image.name || "reference.png",
    type: image.type || "image/png",
    dataUrl: image.dataUrl,
  };
}

function dataUrlMimeType(dataUrl: string) {
  const match = dataUrl.match(/^data:(.*?);base64,/);
  return match?.[1] || "image/png";
}

function getLegacyReferenceImages(source: Record<string, unknown>): StoredReferenceImage[] {
  if (Array.isArray(source.referenceImages)) {
    return source.referenceImages
      .filter((image): image is StoredReferenceImage => {
        if (!image || typeof image !== "object") {
          return false;
        }
        const candidate = image as StoredReferenceImage;
        return typeof candidate.dataUrl === "string" && candidate.dataUrl.length > 0;
      })
      .map(normalizeReferenceImage);
  }

  if (source.sourceImage && typeof source.sourceImage === "object") {
    const image = source.sourceImage as { dataUrl?: unknown; fileName?: unknown };
    if (typeof image.dataUrl === "string" && image.dataUrl) {
      return [
        {
          name: typeof image.fileName === "string" && image.fileName ? image.fileName : "reference.png",
          type: dataUrlMimeType(image.dataUrl),
          dataUrl: image.dataUrl,
        },
      ];
    }
  }

  return [];
}

function normalizeTurn(turn: ImageTurn & Record<string, unknown>): ImageTurn {
  const normalizedImages = Array.isArray(turn.images) ? turn.images.map(normalizeStoredImage) : [];
  const derivedStatus: ImageTurnStatus =
    normalizedImages.some((image) => image.status === "loading")
      ? "generating"
      : normalizedImages.some((image) => image.status === "error")
        ? "error"
        : "success";

  return {
    id: String(turn.id || `${Date.now()}`),
    prompt: String(turn.prompt || ""),
    model: (turn.model as ImageModel) || "gpt-image-2",
    mode: turn.mode === "edit" ? "edit" : "generate",
    referenceImages: getLegacyReferenceImages(turn),
    count: Math.max(1, Number(turn.count || normalizedImages.length || 1)),
    size: typeof turn.size === "string" ? turn.size : "",
    ratio: typeof turn.ratio === "string" && turn.ratio ? turn.ratio : "1:1",
    tier: typeof turn.tier === "string" && turn.tier ? turn.tier : "1k",
    quality: typeof turn.quality === "string" && turn.quality ? turn.quality : "auto",
    images: normalizedImages,
    createdAt: String(turn.createdAt || new Date().toISOString()),
    status:
      turn.status === "queued" ||
      turn.status === "generating" ||
      turn.status === "success" ||
      turn.status === "error"
        ? turn.status
        : derivedStatus,
    error: typeof turn.error === "string" ? turn.error : undefined,
    promptDeleted: turn.promptDeleted === true,
    resultsDeleted: turn.resultsDeleted === true,
  };
}

function normalizeConversation(conversation: ImageConversation & Record<string, unknown>): ImageConversation {
  const turns = Array.isArray(conversation.turns)
    ? conversation.turns.map((turn) => normalizeTurn(turn as ImageTurn & Record<string, unknown>))
    : [
        normalizeTurn({
          id: String(conversation.id || `${Date.now()}`),
          prompt: String(conversation.prompt || ""),
          model: (conversation.model as ImageModel) || "gpt-image-2",
          mode: conversation.mode === "edit" ? "edit" : "generate",
          referenceImages: getLegacyReferenceImages(conversation),
          count: Number(conversation.count || 1),
          size: typeof conversation.size === "string" ? conversation.size : "",
          ratio: typeof conversation.ratio === "string" && conversation.ratio ? conversation.ratio : "1:1",
          tier: typeof conversation.tier === "string" && conversation.tier ? conversation.tier : "1k",
          quality: typeof conversation.quality === "string" && conversation.quality ? conversation.quality : "auto",
          images: Array.isArray(conversation.images) ? (conversation.images as StoredImage[]) : [],
          createdAt: String(conversation.createdAt || new Date().toISOString()),
          status:
            conversation.status === "generating" || conversation.status === "success" || conversation.status === "error"
              ? conversation.status
              : "success",
          error: typeof conversation.error === "string" ? conversation.error : undefined,
        }),
      ];
  const lastTurn = turns.length > 0 ? turns[turns.length - 1] : null;

  return {
    id: String(conversation.id || `${Date.now()}`),
    title: String(conversation.title || ""),
    createdAt: String(conversation.createdAt || lastTurn?.createdAt || new Date().toISOString()),
    updatedAt: String(conversation.updatedAt || lastTurn?.createdAt || new Date().toISOString()),
    turns,
  };
}

function sortImageConversations(conversations: ImageConversation[]): ImageConversation[] {
  return [...conversations].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export async function listImageConversations(): Promise<ImageConversation[]> {
  const data = await fetchBackendSessions<ImageConversation & Record<string, unknown>>(IMAGE_CONVERSATION_KIND);
  return sortImageConversations(data.items.map(normalizeConversation));
}

export async function saveImageConversations(conversations: ImageConversation[]): Promise<void> {
  await Promise.all(
    conversations.map((conversation) => saveBackendSession(IMAGE_CONVERSATION_KIND, normalizeConversation(conversation))),
  );
}

export async function saveImageConversation(conversation: ImageConversation): Promise<void> {
  await saveBackendSession(IMAGE_CONVERSATION_KIND, normalizeConversation(conversation));
}

export async function renameImageConversation(id: string, title: string): Promise<void> {
  const data = await fetchBackendSessions<ImageConversation & Record<string, unknown>>(IMAGE_CONVERSATION_KIND);
  const target = data.items.map(normalizeConversation).find((item) => item.id === id);
  if (!target) return;
  await saveBackendSession(IMAGE_CONVERSATION_KIND, { ...target, title, updatedAt: new Date().toISOString() });
}

export async function deleteImageConversation(id: string): Promise<void> {
  await deleteBackendSession(IMAGE_CONVERSATION_KIND, id);
}

export async function clearImageConversations(): Promise<void> {
  const data = await fetchBackendSessions<ImageConversation & Record<string, unknown>>(IMAGE_CONVERSATION_KIND);
  await Promise.all(
    data.items
      .map((item) => String(item.id || ""))
      .filter(Boolean)
      .map((id) => deleteBackendSession(IMAGE_CONVERSATION_KIND, id)),
  );
}

export function getImageConversationStats(conversation: ImageConversation | null): ImageConversationStats {
  if (!conversation) {
    return { queued: 0, running: 0 };
  }

  return conversation.turns.reduce(
    (acc, turn) => {
      if (turn.resultsDeleted) {
        return acc;
      }
      if (turn.status === "queued") {
        acc.queued += 1;
      } else if (turn.status === "generating") {
        acc.running += 1;
      }
      return acc;
    },
    { queued: 0, running: 0 },
  );
}
