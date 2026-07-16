"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { fetchClauseAnalysis, questionStreamUrl, uploadDocument } from "@/lib/api";
import type {
  Citation,
  ClauseAnalysisResult,
  DocumentIngestionResponse,
  QAResponse,
  RiskAssessment
} from "@/types/api";
import {
  AnalysisPane,
  DocumentViewer,
  MobileTabs,
  TopBar,
  type ChatThreadMessage,
  type ComparisonSummary,
  type UploadState,
  type WorkspaceTab
} from "./workspace-components";

export function ContractWorkspace() {
  const [state, setState] = useState<UploadState>("idle");
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("document");
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [ingestion, setIngestion] = useState<DocumentIngestionResponse | null>(null);
  const [analysis, setAnalysis] = useState<ClauseAnalysisResult | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatThreadMessage[]>([]);
  const [lastQuestion, setLastQuestion] = useState("");
  const [comparison, setComparison] = useState<ComparisonSummary | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [activePage, setActivePage] = useState(1);
  const [pageCount, setPageCount] = useState(1);
  const docxRefs = useRef<Record<string, HTMLElement | null>>({});
  const uploadSequence = useRef(0);

  const activeRiskByClause = useMemo(() => {
    const map = new Map<string, RiskAssessment>();
    for (const risk of analysis?.risks ?? []) {
      map.set(risk.clause_id, risk);
    }
    return map;
  }, [analysis]);

  useEffect(() => {
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [fileUrl]);

  useEffect(() => {
    if (!activeCitation || activeCitation.source_locator.source_type !== "docx") {
      return;
    }
    docxRefs.current[`p-${activeCitation.source_locator.paragraph_start}`]?.scrollIntoView?.({
      block: "center",
      behavior: "smooth"
    });
  }, [activeCitation]);

  async function handleUpload(selectedFile: File) {
    const sequence = ++uploadSequence.current;
    setFile(selectedFile);
    setFileUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return URL.createObjectURL(selectedFile);
    });
    setState("uploading");
    setActiveTab("document");
    setError(null);
    setMessages([]);
    setLastQuestion("");
    setComparison(null);
    setAnalysis(null);
    setIngestion(null);
    setActiveCitation(null);
    setActivePage(1);
    setPageCount(1);

    try {
      const uploaded = await uploadDocument(selectedFile);
      if (sequence !== uploadSequence.current) return;
      setIngestion(uploaded);
      setState("analyzing");
      const result = await fetchClauseAnalysis(uploaded.document.document_id);
      if (sequence !== uploadSequence.current) return;
      setAnalysis(result);
      setState("ready");
      setActiveTab("analysis");
    } catch (uploadError) {
      setState("error");
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed");
    }
  }

  function handleCitation(citation: Citation) {
    setActiveCitation(citation);
    if (citation.source_locator.source_type === "pdf") {
      setActivePage(citation.source_locator.page_number);
    }
    setActiveTab("document");
  }

  async function handleCompare(selectedFile: File) {
    try {
      const uploaded = await uploadDocument(selectedFile);
      const compared = await fetchClauseAnalysis(uploaded.document.document_id);
      const diff = compareClauses(analysis?.clauses ?? [], compared.clauses);
      setComparison({ filename: selectedFile.name, ...diff });
    } catch {
      setComparison({ filename: selectedFile.name, added: 0, removed: 0, changed: 0, error: "Comparison failed" });
    }
  }

  function submitQuestion(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startQuestion(question.trim());
  }

  function startQuestion(trimmed: string) {
    if (!ingestion || !trimmed || streaming || state !== "ready") {
      return;
    }

    setLastQuestion(trimmed);
    const userMessage: ChatThreadMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: trimmed,
      citations: []
    };
    const assistantId = crypto.randomUUID();
    setMessages((current) => [
      ...current,
      userMessage,
      { id: assistantId, role: "assistant", text: "", citations: [], streaming: true }
    ]);
    setQuestion("");
    setStreaming(true);

    const source = new EventSource(questionStreamUrl(ingestion.document.document_id, trimmed));
    source.addEventListener("answer_delta", (message) => {
      const payload = JSON.parse(message.data) as { text: string };
      setMessages((current) =>
        current.map((item) => (item.id === assistantId ? { ...item, text: item.text + payload.text } : item))
      );
    });
    source.addEventListener("citation", (message) => {
      const citation = JSON.parse(message.data) as Citation;
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantId ? { ...item, citations: dedupeCitations([...item.citations, citation]) } : item
        )
      );
    });
    source.addEventListener("refusal", (message) => {
      const payload = JSON.parse(message.data) as { answer: string; reason: string };
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantId
            ? { ...item, text: payload.answer, refused: true, refusalReason: payload.reason, citations: [] }
            : item
        )
      );
    });
    source.addEventListener("final", (message) => {
      const payload = JSON.parse(message.data) as QAResponse;
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantId
            ? {
                ...item,
                text: payload.answer,
                citations: payload.citations,
                refused: payload.refused,
                refusalReason: payload.refusal_reason ?? undefined,
                streaming: false
              }
            : item
        )
      );
      setStreaming(false);
      source.close();
    });
    source.addEventListener("error", () => {
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantId
            ? {
                ...item,
                text: "The answer stream was interrupted.",
                refused: true,
                refusalReason: "stream_interrupted",
                streaming: false
              }
            : item
        )
      );
      setStreaming(false);
      source.close();
    });
  }

  const documentLabel = ingestion?.document.original_filename ?? file?.name ?? "Contract Intelligence";
  const fileMeta = ingestion
    ? `${formatBytes(ingestion.document.file_size_bytes)}  •  uploaded just now`
    : file
      ? file.name
      : null;

  return (
    <main className="cia-shell">
      <TopBar
        title={documentLabel}
        meta={fileMeta}
        status={state}
        page={activePage}
        pageCount={pageCount}
        hasDocument={Boolean(file)}
        onUpload={handleUpload}
        onCompare={handleCompare}
      />
      <MobileTabs activeTab={activeTab} onChange={setActiveTab} />
      <div className="cia-workspace">
        <section className={activeTab === "document" ? "cia-pane cia-pane-visible" : "cia-pane"} aria-label="Document workspace">
          <DocumentViewer
            key={`${fileUrl ?? "empty"}-${state}`}
            state={state}
            error={error}
            file={file}
            fileUrl={fileUrl}
            chunks={ingestion?.chunks ?? []}
            activeCitation={activeCitation}
            activePage={activePage}
            pageCount={pageCount}
            docxRefs={docxRefs}
            onUpload={handleUpload}
            onPageChange={setActivePage}
            onPageCountChange={setPageCount}
          />
        </section>
        <aside className={activeTab === "analysis" ? "cia-pane cia-pane-visible" : "cia-pane"} aria-label="Analysis workspace">
          <AnalysisPane
            state={state}
            error={error}
            warnings={ingestion?.warnings ?? []}
            analysis={analysis}
            activeRiskByClause={activeRiskByClause}
            activeCitationId={activeCitation?.citation_id ?? null}
            comparison={comparison}
            messages={messages}
            question={question}
            streaming={streaming}
            onQuestionChange={setQuestion}
            onQuestionSubmit={submitQuestion}
            onRetry={() => startQuestion(lastQuestion)}
            onCitation={handleCitation}
          />
        </aside>
      </div>
    </main>
  );
}

function compareClauses(
  current: ClauseAnalysisResult["clauses"],
  incoming: ClauseAnalysisResult["clauses"]
) {
  const matchedCurrent = new Set<number>();
  let changed = 0;

  incoming.forEach((candidate, incomingIndex) => {
    const matchIndex = findClauseMatch(candidate, current, matchedCurrent, incomingIndex);
    if (matchIndex === null) {
      return;
    }
    matchedCurrent.add(matchIndex);
    if (normalizeClauseText(current[matchIndex].clause_text) !== normalizeClauseText(candidate.clause_text)) {
      changed += 1;
    }
  });

  return {
    added: incoming.length - matchedCurrent.size,
    removed: current.length - matchedCurrent.size,
    changed
  };
}

function findClauseMatch(
  candidate: ClauseAnalysisResult["clauses"][number],
  current: ClauseAnalysisResult["clauses"],
  used: Set<number>,
  incomingIndex: number
): number | null {
  const exactHeading = current.findIndex((item, index) =>
    !used.has(index) &&
    item.clause_type === candidate.clause_type &&
    normalizeClauseText(item.clause_heading ?? "") === normalizeClauseText(candidate.clause_heading ?? "")
  );
  if (exactHeading >= 0) {
    return exactHeading;
  }

  const candidateTokens = clauseTokens(candidate.clause_text);
  let best: { index: number; score: number; distance: number } | null = null;
  for (const [index, item] of current.entries()) {
    if (used.has(index)) {
      continue;
    }
    if (item.clause_type !== candidate.clause_type) {
      continue;
    }
    const score = jaccard(candidateTokens, clauseTokens(item.clause_text));
    const distance = Math.abs(index - incomingIndex);
    if (score >= 0.35 && (!best || score > best.score || (score === best.score && distance < best.distance))) {
      best = { index, score, distance };
    }
  }
  return best?.index ?? null;
}

function normalizeClauseText(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function clauseTokens(value: string) {
  return new Set(normalizeClauseText(value).split(" ").filter((token) => token.length > 2));
}

function jaccard(left: Set<string>, right: Set<string>) {
  const intersection = [...left].filter((token) => right.has(token)).length;
  const union = new Set([...left, ...right]).size;
  return union ? intersection / union : 0;
}

function dedupeCitations(citations: Citation[]) {
  const seen = new Set<string>();
  return citations.filter((citation) => {
    if (seen.has(citation.citation_id)) {
      return false;
    }
    seen.add(citation.citation_id);
    return true;
  });
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
