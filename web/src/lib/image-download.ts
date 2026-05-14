import { fetchImageDownloadSettings } from "@/lib/api";

export const IMAGE_PROMPT_PAYLOAD_PREFIX = "\n\n-- chatgpt2api prompt --\n";
export const IMAGE_PROMPT_PAYLOAD_SUFFIX = "\n-- end chatgpt2api prompt --\n";

type DownloadImageSource = Blob | string;

let appendPromptSettingCache: boolean | null = null;

export function appendPromptPayloadToBlob(blob: Blob, prompt: string, enabled: boolean) {
  const normalizedPrompt = String(prompt || "").trim();
  if (!enabled || !normalizedPrompt) {
    return blob;
  }
  return new Blob([blob, IMAGE_PROMPT_PAYLOAD_PREFIX, normalizedPrompt, IMAGE_PROMPT_PAYLOAD_SUFFIX], { type: blob.type });
}

export async function getImageDownloadAppendPromptEnabled() {
  if (appendPromptSettingCache !== null) {
    return appendPromptSettingCache;
  }
  try {
    const data = await fetchImageDownloadSettings();
    appendPromptSettingCache = Boolean(data.image_download_append_prompt);
  } catch {
    appendPromptSettingCache = false;
  }
  return appendPromptSettingCache;
}

export function resetImageDownloadAppendPromptCache() {
  appendPromptSettingCache = null;
}

export function getExtensionFromMime(type: string) {
  if (type.includes("jpeg") || type.includes("jpg")) return "jpg";
  if (type.includes("webp")) return "webp";
  if (type.includes("gif")) return "gif";
  return "png";
}

function blobFromDataUrl(dataUrl: string) {
  const [header, payload = ""] = dataUrl.split(",", 2);
  const mime = header.match(/^data:([^;]+)/)?.[1] || "image/png";
  const binary = atob(payload);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type: mime });
}

async function blobFromSource(source: DownloadImageSource) {
  if (source instanceof Blob) {
    return source;
  }
  if (source.startsWith("data:")) {
    return blobFromDataUrl(source);
  }
  const response = await fetch(source);
  if (!response.ok) {
    throw new Error("download failed");
  }
  return response.blob();
}

function triggerBlobDownload(blob: Blob, fileName: string) {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.rel = "noopener";
  anchor.href = objectUrl;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
}

export async function downloadImageWithPrompt(
  source: DownloadImageSource,
  fileName: string,
  options: { prompt?: string; inferExtension?: boolean } = {},
) {
  const appendPrompt = await getImageDownloadAppendPromptEnabled();
  const blob = await blobFromSource(source);
  const downloadBlob = appendPromptPayloadToBlob(blob, options.prompt || "", appendPrompt);
  const downloadName = options.inferExtension && blob.type
    ? fileName.replace(/\.[a-z0-9]+$/i, `.${getExtensionFromMime(blob.type)}`)
    : fileName;
  triggerBlobDownload(downloadBlob, downloadName);
}
