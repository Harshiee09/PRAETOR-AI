"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { askQuestion, getHealth } from "@/lib/api/client";
import { ApiClientError, errorMessage } from "@/lib/api/errors";
import type { AskResponse, HealthResponse } from "@/lib/api/types";

export type ResearchEntry = {
  id: string;
  question: string;
  answer: AskResponse;
  sampleData: boolean;
};
type Failure = { message: string; requestId: string };
type ResearchContextValue = {
  entries: ResearchEntry[];
  current: ResearchEntry | undefined;
  pending: boolean;
  startedAt: number | null;
  error: Failure | null;
  health: HealthResponse["status"] | "checking";
  healthRequestId: string;
  documentHealth: "ok" | "limited" | "offline" | "checking";
  operationBusy: boolean;
  beginOperation: () => AbortController | null;
  endOperation: (controller: AbortController) => void;
  sampleData: boolean;
  draft: string;
  setDraft: (value: string) => void;
  submit: (question: string) => Promise<void>;
  clear: () => void;
  newResearch: () => void;
  select: (id: string) => void;
  refreshHealth: () => void;
};
const ResearchContext = createContext<ResearchContextValue | null>(null);

export function ResearchProvider({ children }: { children: ReactNode }) {
  const [entries, setEntries] = useState<ResearchEntry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [error, setError] = useState<Failure | null>(null);
  const [health, setHealth] =
    useState<ResearchContextValue["health"]>("checking");
  const [healthRequestId, setHealthRequestId] = useState("");
  const [documentHealth, setDocumentHealth] = useState<ResearchContextValue["documentHealth"]>("checking");
  const [externalBusy, setExternalBusy] = useState(false);
  const externalOperation = useRef<AbortController | null>(null);
  const [sampleData, setSampleData] = useState(false);
  const request = useRef<AbortController | null>(null);
  const healthRequest = useRef<AbortController | null>(null);

  const refreshHealth = useCallback(async () => {
    healthRequest.current?.abort();
    const controller = new AbortController();
    healthRequest.current = controller;
    try {
      const result = await getHealth({ signal: controller.signal });
      if (controller.signal.aborted) return;
      setHealth(result.status);
      setDocumentHealth(result.checks.documents === "ok" ? "ok" : "limited");
      setSampleData(result.sampleData);
      setHealthRequestId(result.requestId);
    } catch (failure) {
      if (controller.signal.aborted) return;
      setHealth("down");
      setDocumentHealth("offline");
      setSampleData(false);
      setHealthRequestId(
        failure instanceof ApiClientError ? failure.requestId : "unavailable",
      );
    }
  }, []);

  useEffect(() => {
    void refreshHealth();
    const interval = setInterval(() => void refreshHealth(), 60_000);
    return () => {
      clearInterval(interval);
      healthRequest.current?.abort();
      request.current?.abort();
      externalOperation.current?.abort();
    };
  }, [refreshHealth]);

  async function submit(question: string) {
    const trimmed = question.trim();
    if (
      request.current || externalOperation.current ||
      health === "down" ||
      health === "checking" ||
      !trimmed ||
      Array.from(trimmed).length > 2000
    )
      return;
    const controller = new AbortController();
    request.current = controller;
    setPending(true);
    setStartedAt(Date.now());
    setError(null);
    setSelectedId(null);
    try {
      const result = await askQuestion(trimmed, { signal: controller.signal });
      if (controller.signal.aborted) return;
      const entry = {
        id: crypto.randomUUID(),
        question: trimmed,
        answer: result,
        sampleData: result.sampleData,
      };
      setEntries((previous) => [...previous, entry]);
      setSelectedId(entry.id);
      setDraft("");
    } catch (failure) {
      if (controller.signal.aborted) return;
      setError({
        message: errorMessage(failure),
        requestId:
          failure instanceof ApiClientError ? failure.requestId : "unavailable",
      });
    } finally {
      if (request.current === controller) {
        request.current = null;
        setPending(false);
        setStartedAt(null);
      }
    }
  }

  function clear() {
    request.current?.abort();
    request.current = null;
    setEntries([]);
    setSelectedId(null);
    setDraft("");
    setError(null);
    setPending(false);
    setStartedAt(null);
  }
  function newResearch() {
    if (!pending) {
      setSelectedId(null);
      setError(null);
      setDraft("");
    }
  }
  const beginOperation = useCallback(() => {
    if (request.current || externalOperation.current) return null;
    const controller = new AbortController();
    externalOperation.current = controller;
    setExternalBusy(true);
    return controller;
  }, []);
  const endOperation = useCallback((controller: AbortController) => {
    if (externalOperation.current === controller) {
      externalOperation.current = null;
      setExternalBusy(false);
    }
  }, []);
  function select(id: string) {
    if (!pending) {
      setSelectedId(id);
      setError(null);
    }
  }
  return (
    <ResearchContext.Provider
      value={{
        entries,
        current: entries.find((entry) => entry.id === selectedId),
        pending,
        startedAt,
        error,
        health,
        healthRequestId,
        documentHealth,
        operationBusy: pending || externalBusy,
        beginOperation,
        endOperation,
        sampleData,
        draft,
        setDraft,
        submit,
        clear,
        newResearch,
        select,
        refreshHealth,
      }}
    >
      {children}
    </ResearchContext.Provider>
  );
}

export function useResearch() {
  const context = useContext(ResearchContext);
  if (!context) throw new Error("ResearchProvider is required");
  return context;
}
