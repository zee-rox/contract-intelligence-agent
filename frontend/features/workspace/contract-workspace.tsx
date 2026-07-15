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
