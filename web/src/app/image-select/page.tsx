"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp, Check, ImageIcon, LoaderCircle, Maximize2, Pause, Play, Settings2, Sparkles, Trash2, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createImageGenerationTask,
  fetchImageTasks,
  type ImageTask,
} from "@/lib/api";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { cn } from "@/lib/utils";
import {
  buildImageSelectionTitle,
  deleteImageSelectionSession,
  extractManagedImageRel,
  getImageSelectionSessionStats,
  listImageSelectionSessions,
  saveImageSelectionSession,
  type ImageSelectionCandidate,
  type ImageSelectionSession,
} from "@/store/image-selection-sessions";

const DEFAULT_QUEUE_LIMIT = 6;
const DEFAULT_FAILURE_LIMIT = 5;
const imageSizeOptions = [
  { value: "", label: "未指定" },
  { value: "1:1", label: "1:1" },
  { value: "16:9", label: "16:9" },
  { value: "4:3", label: "4:3" },
  { value: "3:4", label: "3:4" },
  { value: "9:16", label: "9:16" },
];

function createId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function taskToCandidate(candidate: ImageSelectionCandidate, task: ImageTask): ImageSelectionCandidate {
  if (task.status === "success") {
    const first = task.data?.[0];
    if (!first?.url && !first?.b64_json) {
      return { ...candidate, status: "error", error: "未返回图片数据" };
    }
    const url = first.url || (first.b64_json ? `data:image/png;base64,${first.b64_json}` : "");
    return {
      ...candidate,
      taskId: task.id,
      status: "ready",
      url,
      rel: extractManagedImageRel(url),
      revised_prompt: first.revised_prompt,
      error: undefined,
    };
  }
  if (task.status === "error") {
    return { ...candidate, taskId: task.id, status: "error", error: task.error || "生成失败" };
  }
  return { ...candidate, taskId: task.id, status: "loading", error: undefined };
}

function isTextInputTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  const tagName = target.tagName.toLowerCase();
  return tagName === "input" || tagName === "textarea" || target.isContentEditable;
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(date);
}

function aspectClass(size: string) {
  if (size === "16:9") return "aspect-video";
  if (size === "9:16") return "aspect-[9/16]";
  if (size === "4:3") return "aspect-[4/3]";
  if (size === "3:4") return "aspect-[3/4]";
  return "aspect-square";
}

function thumbWidthClass(size: string) {
  if (size === "16:9") return "w-36";
  if (size === "9:16") return "w-12";
  if (size === "4:3") return "w-28";
  if (size === "3:4") return "w-16";
  return "w-20";
}

type CandidateStripProps = {
  candidates: ImageSelectionCandidate[];
  currentCandidateId?: string;
  size: string;
  onSelectCandidate: (candidateId: string) => void;
  dark?: boolean;
};

function CandidateStrip({ candidates, currentCandidateId, size, onSelectCandidate, dark = false }: CandidateStripProps) {
  return (
    <div className="hide-scrollbar flex w-full min-w-0 gap-2 overflow-x-auto overscroll-x-contain pb-1">
      {candidates.map((candidate) => (
        <div
          key={candidate.id}
          className={cn(
            "relative h-20 shrink-0 overflow-hidden rounded-xl border bg-stone-100",
            thumbWidthClass(size),
            candidate.id === currentCandidateId
              ? dark ? "border-white ring-2 ring-white/30" : "border-stone-950 ring-2 ring-stone-950/10"
              : dark ? "border-white/20" : "border-stone-200",
          )}
        >
          <button
            type="button"
            className="block h-full w-full"
            onClick={() => {
              if (candidate.status === "ready") {
                onSelectCandidate(candidate.id);
              }
            }}
          >
            {candidate.url ? (
              <img src={candidate.url} alt="候选缩略图" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full w-full items-center justify-center">
                <LoaderCircle className="size-4 animate-spin text-stone-400" />
              </div>
            )}
          </button>
        </div>
      ))}
    </div>
  );
}

type ReviewStageProps = {
  session: ImageSelectionSession;
  stats: ReturnType<typeof getImageSelectionSessionStats> | null;
  currentCandidate: ImageSelectionCandidate | null;
  reviewCandidates: ImageSelectionCandidate[];
  hasLoading: boolean;
  isSubmitting: boolean;
  immersive?: boolean;
  onKeep: () => void;
  onDiscard: () => void;
  onSelectCandidate: (candidateId: string) => void;
  immersiveActions?: ReactNode;
};

function ReviewStage({
  session,
  stats,
  currentCandidate,
  reviewCandidates,
  hasLoading,
  isSubmitting,
  immersive = false,
  onKeep,
  onDiscard,
  onSelectCandidate,
  immersiveActions,
}: ReviewStageProps) {
  if (immersive) {
    return (
      <div className="flex h-full min-h-0 flex-col bg-stone-950 text-white">
        <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2 text-xs text-stone-300">
              <span>队列 {stats?.active ?? 0} / {session.queueLimit}</span>
              <span>保留 {stats?.kept ?? 0}</span>
              <span>丢弃 {stats?.discarded ?? 0}</span>
              <span>跳过 {stats?.error ?? 0}</span>
            </div>
            <div className="mt-1 max-w-[70vw] truncate text-sm font-medium">{session.prompt}</div>
          </div>
          <div className="flex flex-wrap justify-end gap-2">
            <Button className="rounded-xl bg-emerald-600 text-white hover:bg-emerald-700" disabled={!currentCandidate} onClick={onKeep}>
              <ArrowUp className="size-4" />
              保留
            </Button>
            <Button variant="outline" className="rounded-xl border-white/20 bg-white/10 text-white hover:bg-white/20" disabled={!currentCandidate} onClick={onDiscard}>
              <ArrowDown className="size-4" />
              丢弃
            </Button>
            {immersiveActions}
          </div>
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center p-3">
          <div className="flex h-full w-full items-center justify-center overflow-hidden">
            {currentCandidate?.url ? (
              <img src={currentCandidate.url} alt="当前候选图" className="max-h-full max-w-full object-contain" />
            ) : (
              <div className="flex flex-col items-center gap-3 text-stone-300">
                {hasLoading || isSubmitting ? <LoaderCircle className="size-8 animate-spin" /> : <ImageIcon className="size-8" />}
                <div>{hasLoading || isSubmitting ? "正在等待候选图" : "暂无可选择候选"}</div>
              </div>
            )}
          </div>
        </div>
        <div className="shrink-0 border-t border-white/10 px-4 py-3">
          <CandidateStrip candidates={reviewCandidates} currentCandidateId={currentCandidate?.id} size={session.size} onSelectCandidate={onSelectCandidate} dark />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 pt-4">
      <div className="flex flex-1 flex-col items-center justify-center gap-4">
        <div className={cn("flex max-h-[64dvh] w-full max-w-[min(100%,920px)] items-center justify-center overflow-hidden rounded-[28px] bg-stone-950 text-white", aspectClass(session.size))}>
          {currentCandidate?.url ? (
            <img src={currentCandidate.url} alt="当前候选图" className="h-full w-full object-contain" />
          ) : (
            <div className="flex flex-col items-center gap-3 text-stone-300">
              {hasLoading || isSubmitting ? <LoaderCircle className="size-8 animate-spin" /> : <ImageIcon className="size-8" />}
              <div>{hasLoading || isSubmitting ? "正在等待候选图" : "暂无可选择候选"}</div>
            </div>
          )}
        </div>

        <div className="flex w-full max-w-[720px] flex-col gap-2 sm:flex-row">
          <Button className="h-13 flex-1 rounded-2xl bg-emerald-600 text-white hover:bg-emerald-700" disabled={!currentCandidate} onClick={onKeep}>
            <ArrowUp className="size-5" />
            保留（↑）
          </Button>
          <Button variant="outline" className="h-13 flex-1 rounded-2xl border-rose-200 bg-white text-rose-600 hover:bg-rose-50" disabled={!currentCandidate} onClick={onDiscard}>
            <ArrowDown className="size-5" />
            丢弃（↓）
          </Button>
        </div>
      </div>

      <div className="min-w-0 rounded-2xl border border-stone-100 bg-white p-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <div className="text-xs font-medium text-stone-500">候选队列</div>
          <div className="flex flex-wrap gap-3 text-xs text-stone-500">
            <div className="flex items-center gap-1"><Check className="size-3 text-emerald-600" /> 保留进入当前选图会话归档</div>
            <div className="flex items-center gap-1"><X className="size-3 text-rose-500" /> 丢弃不删除图片文件</div>
          </div>
        </div>
        <CandidateStrip candidates={reviewCandidates} currentCandidateId={currentCandidate?.id} size={session.size} onSelectCandidate={onSelectCandidate} />
      </div>
    </div>
  );
}

function ImageSelectContent() {
  const sessionsRef = useRef<ImageSelectionSession[]>([]);
  const fillingRef = useRef(false);
  const promptRef = useRef<HTMLTextAreaElement>(null);
  const [sessions, setSessions] = useState<ImageSelectionSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [currentCandidateId, setCurrentCandidateId] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [imageSize, setImageSize] = useState("");
  const [queueLimit, setQueueLimit] = useState(DEFAULT_QUEUE_LIMIT);
  const [failureLimit, setFailureLimit] = useState(DEFAULT_FAILURE_LIMIT);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [isImmersive, setIsImmersive] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [configQueueLimit, setConfigQueueLimit] = useState(DEFAULT_QUEUE_LIMIT);
  const [configFailureLimit, setConfigFailureLimit] = useState(DEFAULT_FAILURE_LIMIT);

  const selectedSession = useMemo(
    () => sessions.find((session) => session.id === selectedSessionId) ?? null,
    [selectedSessionId, sessions],
  );
  const stats = selectedSession ? getImageSelectionSessionStats(selectedSession) : null;
  const readyCandidates = useMemo(
    () => selectedSession?.candidates.filter((candidate) => candidate.status === "ready" && candidate.url) ?? [],
    [selectedSession],
  );
  const currentCandidate =
    readyCandidates.find((candidate) => candidate.id === currentCandidateId) ?? readyCandidates[0] ?? null;
  const hasLoading = Boolean(selectedSession?.candidates.some((candidate) => candidate.status === "loading"));
  const reviewCandidates = selectedSession?.candidates.filter((candidate) => candidate.status === "ready" || candidate.status === "loading") ?? [];

  useEffect(() => {
    if (!selectedSession) {
      setCurrentCandidateId(null);
      return;
    }
    if (readyCandidates.some((candidate) => candidate.id === currentCandidateId)) {
      return;
    }
    setCurrentCandidateId(readyCandidates[0]?.id ?? null);
  }, [currentCandidateId, readyCandidates, selectedSession]);

  const persistSession = useCallback(async (session: ImageSelectionSession) => {
    const nextSessions = [session, ...sessionsRef.current.filter((item) => item.id !== session.id)]
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
    sessionsRef.current = nextSessions;
    setSessions(nextSessions);
    await saveImageSelectionSession(session);
  }, []);

  const handleDeleteSession = useCallback(async (id: string) => {
    const nextSessions = sessionsRef.current.filter((session) => session.id !== id);
    sessionsRef.current = nextSessions;
    setSessions(nextSessions);
    if (selectedSessionId === id) {
      setSelectedSessionId(nextSessions[0]?.id ?? null);
      setCurrentCandidateId(null);
      setIsImmersive(false);
    }
    setDeleteTargetId(null);
    await deleteImageSelectionSession(id);
    toast.success("选图会话已删除，图片文件已保留");
  }, [selectedSessionId]);

  const updateSession = useCallback(async (sessionId: string, updater: (session: ImageSelectionSession) => ImageSelectionSession) => {
    const current = sessionsRef.current.find((session) => session.id === sessionId);
    if (!current) {
      return null;
    }
    const nextSession = updater(current);
    await persistSession(nextSession);
    return nextSession;
  }, [persistSession]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const storedSessions = await listImageSelectionSessions();
        if (cancelled) {
          return;
        }
        const restored = storedSessions.map((session) =>
          session.status === "running"
            ? { ...session, status: "paused" as const, updatedAt: new Date().toISOString() }
            : session,
        );
        sessionsRef.current = restored;
        setSessions(restored);
        setSelectedSessionId(restored[0]?.id ?? null);
        for (const session of restored) {
          if (session.status === "paused" && session.candidates.some((candidate) => candidate.status === "loading")) {
            void saveImageSelectionSession(session);
          }
        }
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "加载选图会话失败");
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleStart = useCallback(async () => {
    const text = prompt.trim();
    if (!text) {
      toast.error("请输入提示词");
      return;
    }
    const now = new Date().toISOString();
    const session: ImageSelectionSession = {
      id: createId(),
      title: buildImageSelectionTitle(text),
      prompt: text,
      size: imageSize,
      queueLimit,
      failureLimit,
      status: "running",
      candidates: [],
      createdAt: now,
      updatedAt: now,
      consecutiveFailures: 0,
    };
    setSelectedSessionId(session.id);
    setCurrentCandidateId(null);
    setPrompt("");
    await persistSession(session);
    toast.success("选图已开始");
  }, [failureLimit, imageSize, persistSession, prompt, queueLimit]);

  const handlePause = useCallback(async () => {
    if (!selectedSession) {
      return;
    }
    await updateSession(selectedSession.id, (session) => ({ ...session, status: "paused", updatedAt: new Date().toISOString() }));
  }, [selectedSession, updateSession]);

  const handleContinue = useCallback(async () => {
    if (!selectedSession) {
      return;
    }
    await updateSession(selectedSession.id, (session) => ({
      ...session,
      status: "running",
      consecutiveFailures: 0,
      lastError: undefined,
      updatedAt: new Date().toISOString(),
    }));
  }, [selectedSession, updateSession]);

  const openSessionConfig = useCallback(() => {
    if (!selectedSession) {
      return;
    }
    setConfigQueueLimit(selectedSession.queueLimit);
    setConfigFailureLimit(selectedSession.failureLimit);
    setConfigOpen(true);
  }, [selectedSession]);

  const handleSaveSessionConfig = useCallback(async () => {
    if (!selectedSession) {
      return;
    }
    const nextQueueLimit = Math.max(1, Math.min(100, Number(configQueueLimit) || DEFAULT_QUEUE_LIMIT));
    const nextFailureLimit = Math.max(1, Math.min(100, Number(configFailureLimit) || DEFAULT_FAILURE_LIMIT));
    await updateSession(selectedSession.id, (session) => ({
      ...session,
      queueLimit: nextQueueLimit,
      failureLimit: nextFailureLimit,
      consecutiveFailures: Math.min(session.consecutiveFailures, nextFailureLimit),
      updatedAt: new Date().toISOString(),
    }));
    setConfigOpen(false);
    toast.success("会话配置已更新");
  }, [configFailureLimit, configQueueLimit, selectedSession, updateSession]);

  const selectSession = useCallback((id: string) => {
    setSelectedSessionId(id);
    setCurrentCandidateId(null);
    setIsImmersive(false);
  }, []);

  const decideCurrent = useCallback(async (status: "kept" | "discarded") => {
    if (!selectedSession || !currentCandidate) {
      return;
    }
    const now = new Date().toISOString();
    await updateSession(selectedSession.id, (session) => ({
      ...session,
      updatedAt: now,
      candidates: session.candidates.map((candidate) =>
        candidate.id === currentCandidate.id ? { ...candidate, status, decidedAt: now } : candidate,
      ),
    }));
    setCurrentCandidateId(null);
  }, [currentCandidate, selectedSession, updateSession]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (isTextInputTarget(event.target) || !currentCandidate) {
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        void decideCurrent("kept");
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        void decideCurrent("discarded");
      }
      if (event.key === "Escape" && isImmersive) {
        event.preventDefault();
        setIsImmersive(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentCandidate, decideCurrent, isImmersive]);

  useEffect(() => {
    if (!selectedSession) {
      setIsImmersive(false);
    }
  }, [selectedSession]);

  useEffect(() => {
    if (!selectedSession?.candidates.some((candidate) => candidate.status === "loading")) {
      return;
    }
    const poll = async () => {
      const snapshot = sessionsRef.current.find((session) => session.id === selectedSession.id);
      const loadingIds = snapshot?.candidates.flatMap((candidate) =>
        candidate.status === "loading" && candidate.taskId ? [candidate.taskId] : [],
      ) || [];
      if (loadingIds.length === 0) {
        return;
      }
      try {
        const taskList = await fetchImageTasks(loadingIds);
        if (taskList.items.length === 0 && taskList.missing_ids.length === 0) {
          return;
        }
        const taskMap = new Map(taskList.items.map((task) => [task.id, task]));
        await updateSession(selectedSession.id, (session) => {
          let failures = session.consecutiveFailures;
          const candidates = session.candidates.map((candidate) => {
            if (candidate.status !== "loading" || !candidate.taskId) {
              return candidate;
            }
            if (taskList.missing_ids.includes(candidate.taskId)) {
              failures += 1;
              return { ...candidate, status: "error" as const, error: "任务已丢失" };
            }
            const task = taskMap.get(candidate.taskId);
            if (!task) {
              return candidate;
            }
            const nextCandidate = taskToCandidate(candidate, task);
            if (nextCandidate.status === "error") {
              failures += 1;
            } else if (nextCandidate.status === "ready") {
              failures = 0;
            }
            return nextCandidate;
          });
          const shouldPause = failures >= session.failureLimit;
          return {
            ...session,
            candidates,
            consecutiveFailures: failures,
            status: shouldPause ? "paused" : session.status,
            lastError: shouldPause ? "连续生成失败，已暂停选图" : session.lastError,
            updatedAt: new Date().toISOString(),
          };
        });
      } catch {
        // transient polling errors should not stop existing submitted tasks
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 2000);
    return () => window.clearInterval(timer);
  }, [selectedSession?.id, selectedSession?.candidates, updateSession]);

  useEffect(() => {
    const fillQueue = async () => {
      const snapshot = sessionsRef.current.find((session) => session.id === selectedSessionId);
      if (!snapshot || snapshot.status !== "running" || fillingRef.current) {
        return;
      }
      const currentStats = getImageSelectionSessionStats(snapshot);
      const slots = Math.max(0, snapshot.queueLimit - currentStats.active);
      if (slots === 0) {
        return;
      }
      fillingRef.current = true;
      setIsSubmitting(true);
      try {
        for (let index = 0; index < slots; index += 1) {
          const now = new Date().toISOString();
          const candidateId = createId();
          const candidate: ImageSelectionCandidate = {
            id: candidateId,
            taskId: candidateId,
            status: "loading",
            createdAt: now,
          };
          await updateSession(snapshot.id, (session) => ({
            ...session,
            candidates: [...session.candidates, candidate],
            updatedAt: now,
          }));
          try {
            const task = await createImageGenerationTask(candidateId, snapshot.prompt, "gpt-image-2", snapshot.size);
            await updateSession(snapshot.id, (session) => ({
              ...session,
              candidates: session.candidates.map((item) =>
                item.id === candidateId ? taskToCandidate({ ...item, taskId: candidateId }, task) : item,
              ),
              updatedAt: new Date().toISOString(),
            }));
          } catch (error) {
            const message = error instanceof Error ? error.message : "提交生成任务失败";
            await updateSession(snapshot.id, (session) => {
              const failures = session.consecutiveFailures + 1;
              return {
                ...session,
                candidates: session.candidates.map((item) =>
                  item.id === candidateId ? { ...item, status: "error", error: message } : item,
                ),
                consecutiveFailures: failures,
                status: failures >= session.failureLimit ? "paused" : session.status,
                lastError: failures >= session.failureLimit ? "连续生成失败，已暂停选图" : message,
                updatedAt: new Date().toISOString(),
              };
            });
          }
        }
      } finally {
        fillingRef.current = false;
        setIsSubmitting(false);
      }
    };
    void fillQueue();
  }, [selectedSessionId, selectedSession?.status, selectedSession?.candidates, updateSession]);

  if (isLoading) {
    return <div className="flex min-h-[40vh] items-center justify-center"><LoaderCircle className="size-5 animate-spin text-stone-400" /></div>;
  }

  return (
    <section className="mx-auto grid min-h-[calc(100dvh-6.5rem)] w-full max-w-[1380px] gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="rounded-[28px] border border-white/80 bg-white/80 p-4 shadow-sm">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="text-xs font-semibold tracking-[0.18em] text-stone-500 uppercase">Selection</div>
            <h1 className="text-xl font-semibold tracking-tight">选图</h1>
          </div>
          <Sparkles className="size-5 text-stone-400" />
        </div>
        <div className="mt-5 space-y-3">
          <Textarea
            ref={promptRef}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="输入提示词，开始持续生成候选图"
            className="min-h-28 rounded-2xl border-stone-200 bg-white shadow-none"
          />
          <div className="grid grid-cols-2 gap-2">
            {imageSizeOptions.map((option) => (
              <button
                key={option.label}
                type="button"
                onClick={() => setImageSize(option.value)}
                className={cn(
                  "rounded-xl border px-3 py-2 text-sm transition",
                  imageSize === option.value ? "border-stone-950 bg-stone-950 text-white" : "border-stone-200 bg-white text-stone-600 hover:bg-stone-50",
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-stone-500">本次队列长度</label>
            <Input
              type="number"
              min="1"
              max="100"
              value={queueLimit}
              onChange={(event) => setQueueLimit(Math.max(1, Math.min(100, Number(event.target.value) || DEFAULT_QUEUE_LIMIT)))}
              className="h-10 rounded-xl border-stone-200 bg-white"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-stone-500">连续错误暂停</label>
            <Input
              type="number"
              min="1"
              max="100"
              value={failureLimit}
              onChange={(event) => setFailureLimit(Math.max(1, Math.min(100, Number(event.target.value) || DEFAULT_FAILURE_LIMIT)))}
              className="h-10 rounded-xl border-stone-200 bg-white"
            />
            <p className="text-xs text-stone-500">连续失败达到该数量后暂停本次选图。</p>
          </div>
          <Button className="h-11 w-full rounded-2xl bg-stone-950 text-white" onClick={() => void handleStart()}>
            <Play className="size-4" />
            开始选图
          </Button>
        </div>
        <div className="mt-6 space-y-2">
          <div className="text-xs font-medium text-stone-500">选图会话</div>
          {sessions.length === 0 ? <div className="rounded-2xl bg-stone-50 p-4 text-sm text-stone-500">暂无选图会话</div> : null}
          {sessions.map((session) => {
            const sessionStats = getImageSelectionSessionStats(session);
            const active = session.id === selectedSessionId;
            return (
              <div
                key={session.id}
                role="button"
                tabIndex={0}
                className={cn(
                  "w-full rounded-2xl border p-3 text-left transition",
                  active ? "border-stone-950 bg-stone-950 text-white" : "border-stone-200 bg-white text-stone-700 hover:bg-stone-50",
                )}
                onClick={() => selectSession(session.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    selectSession(session.id);
                  }
                }}
              >
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold">{session.title || "未命名选图"}</div>
                    <div className={cn("mt-1 text-xs", active ? "text-stone-300" : "text-stone-400")}>{formatTime(session.updatedAt)}</div>
                    <div className={cn("mt-2 text-xs", active ? "text-stone-200" : "text-stone-500")}>保留 {sessionStats.kept} · 丢弃 {sessionStats.discarded}</div>
                  </div>
                  <span
                    role="button"
                    tabIndex={0}
                    className={cn(
                      "inline-flex size-7 shrink-0 items-center justify-center rounded-full transition",
                      active ? "text-stone-300 hover:bg-white/10 hover:text-white" : "text-stone-300 hover:bg-rose-50 hover:text-rose-500",
                    )}
                    onClick={(event) => {
                      event.stopPropagation();
                      setDeleteTargetId(session.id);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        event.stopPropagation();
                        setDeleteTargetId(session.id);
                      }
                    }}
                    aria-label="删除选图会话"
                  >
                    <Trash2 className="size-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </aside>

      <main className="flex min-h-0 min-w-0 flex-col rounded-[32px] border border-white/80 bg-white/70 p-4 shadow-sm sm:p-6">
        {!selectedSession ? (
          <div className="flex min-h-[520px] flex-1 items-center justify-center text-center text-stone-500">
            <div>
              <ImageIcon className="mx-auto mb-4 size-10 text-stone-300" />
              <div className="text-lg font-semibold text-stone-800">输入提示词开始选图</div>
              <p className="mt-2 text-sm">系统会自动补齐候选队列，你可以快速保留或丢弃大图候选。</p>
            </div>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-start justify-between gap-3 border-b border-stone-100 pb-4">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 text-xs text-stone-500">
                  <span className="rounded-full bg-stone-100 px-2.5 py-1">{selectedSession.status === "running" ? "运行中" : "已暂停"}</span>
                  <span>队列 {stats?.active ?? 0} / {selectedSession.queueLimit}</span>
                  <span>连续错误暂停 {selectedSession.failureLimit}</span>
                  <span>保留 {stats?.kept ?? 0}</span>
                  <span>丢弃 {stats?.discarded ?? 0}</span>
                  <span>跳过 {stats?.error ?? 0}</span>
                </div>
                <h2 className="mt-2 line-clamp-2 text-lg font-semibold text-stone-950">{selectedSession.prompt}</h2>
                {selectedSession.lastError ? <p className="mt-1 text-sm text-amber-700">{selectedSession.lastError}</p> : null}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="rounded-xl border-stone-200 bg-white" disabled={!selectedSession} onClick={openSessionConfig}>
                  <Settings2 className="size-4" />
                  配置会话
                </Button>
                <Button variant="outline" className="rounded-xl border-stone-200 bg-white" disabled={!selectedSession} onClick={() => setIsImmersive(true)}>
                  <Maximize2 className="size-4" />
                  沉浸选图
                </Button>
                {selectedSession.status === "running" ? (
                  <Button variant="outline" className="rounded-xl border-stone-200 bg-white" onClick={() => void handlePause()}>
                    <Pause className="size-4" />
                    暂停
                  </Button>
                ) : (
                  <Button className="rounded-xl bg-stone-950 text-white" onClick={() => void handleContinue()}>
                    <Play className="size-4" />
                    继续选图
                  </Button>
                )}
              </div>
            </div>

            <ReviewStage
              session={selectedSession}
              stats={stats}
              currentCandidate={currentCandidate}
              reviewCandidates={reviewCandidates}
              hasLoading={hasLoading}
              isSubmitting={isSubmitting}
              onKeep={() => void decideCurrent("kept")}
              onDiscard={() => void decideCurrent("discarded")}
              onSelectCandidate={setCurrentCandidateId}
            />
          </>
        )}
      </main>
      {selectedSession && isImmersive ? (
        <div className="fixed inset-0 z-[120] bg-stone-950">
          <ReviewStage
            session={selectedSession}
            stats={stats}
            currentCandidate={currentCandidate}
            reviewCandidates={reviewCandidates}
            hasLoading={hasLoading}
            isSubmitting={isSubmitting}
            immersive
            onKeep={() => void decideCurrent("kept")}
            onDiscard={() => void decideCurrent("discarded")}
            onSelectCandidate={setCurrentCandidateId}
            immersiveActions={(
              <>
                {selectedSession.status === "running" ? (
                  <Button
                    variant="outline"
                    className="rounded-xl border-white/20 bg-white/10 text-white hover:bg-white/20"
                    onClick={() => void handlePause()}
                  >
                    <Pause className="size-4" />
                    暂停
                  </Button>
                ) : (
                  <Button
                    className="rounded-xl bg-white text-stone-950 hover:bg-stone-100"
                    onClick={() => void handleContinue()}
                  >
                    <Play className="size-4" />
                    继续
                  </Button>
                )}
                <Button
                  variant="outline"
                  className="rounded-xl border-white/20 bg-white/10 text-white hover:bg-white/20"
                  onClick={() => setIsImmersive(false)}
                >
                  <X className="size-4" />
                  退出
                </Button>
              </>
            )}
          />
        </div>
      ) : null}
      <Dialog open={Boolean(deleteTargetId)} onOpenChange={(open) => (!open ? setDeleteTargetId(null) : null)}>
        <DialogContent showCloseButton={false} className="rounded-2xl p-6">
          <DialogHeader className="gap-2">
            <DialogTitle>删除选图会话</DialogTitle>
            <DialogDescription className="text-sm leading-6">
              只会删除这个选图会话记录和归档关系，不会删除已经生成的图片文件。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" className="rounded-xl" onClick={() => setDeleteTargetId(null)}>
              取消
            </Button>
            <Button className="rounded-xl bg-rose-600 text-white hover:bg-rose-700" onClick={() => deleteTargetId ? void handleDeleteSession(deleteTargetId) : undefined}>
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={configOpen} onOpenChange={setConfigOpen}>
        <DialogContent className="rounded-2xl p-6">
          <DialogHeader className="gap-2">
            <DialogTitle>配置选图会话</DialogTitle>
            <DialogDescription className="text-sm leading-6">
              只影响当前会话。队列长度变大后会继续补齐；变小后不会取消已提交任务，但不会再超过新上限继续补位。
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-stone-700">队列长度</label>
              <Input
                type="number"
                min="1"
                max="100"
                value={configQueueLimit}
                onChange={(event) => setConfigQueueLimit(Math.max(1, Math.min(100, Number(event.target.value) || DEFAULT_QUEUE_LIMIT)))}
                className="h-10 rounded-xl border-stone-200 bg-white"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-stone-700">连续错误暂停</label>
              <Input
                type="number"
                min="1"
                max="100"
                value={configFailureLimit}
                onChange={(event) => setConfigFailureLimit(Math.max(1, Math.min(100, Number(event.target.value) || DEFAULT_FAILURE_LIMIT)))}
                className="h-10 rounded-xl border-stone-200 bg-white"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" className="rounded-xl" onClick={() => setConfigOpen(false)}>
              取消
            </Button>
            <Button className="rounded-xl bg-stone-950 text-white" onClick={() => void handleSaveSessionConfig()}>
              保存配置
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}

export default function ImageSelectPage() {
  const { isCheckingAuth, session } = useAuthGuard();

  if (isCheckingAuth || !session) {
    return <div className="flex min-h-[40vh] items-center justify-center"><LoaderCircle className="size-5 animate-spin text-stone-400" /></div>;
  }

  return <ImageSelectContent />;
}
