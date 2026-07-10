"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  FileText,
  Moon,
  PanelRightOpen,
  SearchCheck,
  Send,
  Sun,
  Upload,
  XCircle
} from "lucide-react";
import React from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { fetchClauseAnalysis, questionStreamUrl, uploadDocument } from "@/lib/api";
import { cx } from "@/lib/utils";
import type {
  CandidateChunk,
  Citation,
  ClauseAnalysisResult,
  DocumentIngestionResponse,
  QAResponse,
  RiskAssessment,
} from "@/types/api";

const PdfPreview = dynamic(() => import("./pdf-preview").then((module) => module.PdfPreview), {
  ssr: false,
  loading: () => (
    <Panel className="flex h-full items-center justify-center rounded-md p-6">
      <span className="text-sm">Loading PDF viewer...</span>
    </Panel>
  )
});

type UploadState = "idle" | "uploading" | "analyzing" | "ready" | "error";
type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations: Citation[];
  refused?: boolean;
  streaming?: boolean;
};

export function ContractWorkspace() {
  const [mode, setMode] = useState<"light" | "dark">("light");
  const [state, setState] = useState<UploadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [ingestion, setIngestion] = useState<DocumentIngestionResponse | null>(null);
  const [analysis, setAnalysis] = useState<ClauseAnalysisResult | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const docxRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const activeRiskByClause = useMemo(() => {
    const map = new Map<string, RiskAssessment>();
    for (const risk of analysis?.risks ?? []) {
      map.set(risk.clause_id, risk);
    }
    return map;
  }, [analysis]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", mode === "dark");
  }, [mode]);

  useEffect(() => {
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [fileUrl]);

  useEffect(() => {
    if (!activeCitation) {
      return;
    }
    const locator = activeCitation.source_locator;
    if (locator.source_type === "docx") {
      docxRefs.current[`p-${locator.paragraph_start}`]?.scrollIntoView?.({ block: "center", behavior: "smooth" });
    }
  }, [activeCitation]);

  async function handleUpload(selectedFile: File) {
    setFile(selectedFile);
    setFileUrl(URL.createObjectURL(selectedFile));
    setState("uploading");
    setError(null);
    setMessages([]);
    setAnalysis(null);
    setActiveCitation(null);
    try {
      const uploaded = await uploadDocument(selectedFile);
      setIngestion(uploaded);
      setState("analyzing");
      const result = await fetchClauseAnalysis(uploaded.document.document_id);
      setAnalysis(result);
      setState("ready");
    } catch (uploadError) {
      setState("error");
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed");
    }
  }

  function handleCitation(citation: Citation) {
    setActiveCitation(citation);
  }

  function submitQuestion(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!ingestion || !question.trim() || streaming) {
      return;
    }
    const trimmed = question.trim();
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", text: trimmed, citations: [] };
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
          item.id === assistantId ? { ...item, text: payload.answer, refused: true, citations: [] } : item
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
            ? { ...item, text: "The answer stream was interrupted.", refused: true, streaming: false }
            : item
        )
      );
      setStreaming(false);
      source.close();
    });
  }

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <header className="flex min-h-16 items-center justify-between border-b border-[var(--border)] bg-[var(--panel)] px-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[var(--accent)] text-white">
            <SearchCheck size={22} aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-base font-semibold">Contract Intelligence Agent</h1>
            <p className="text-xs text-[color-mix(in_srgb,var(--foreground),transparent_35%)]">
              Automated review for informational use only
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="secondary"
          aria-label={mode === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          onClick={() => setMode((current) => (current === "dark" ? "light" : "dark"))}
        >
          {mode === "dark" ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
        </Button>
      </header>

      <div className="grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[300px_minmax(0,1fr)_380px]">
        <aside className="border-b border-[var(--border)] bg-[var(--panel)] p-4 lg:border-b-0 lg:border-r">
          <UploadPanel state={state} file={file} error={error} onUpload={handleUpload} />
          <StatusPanel ingestion={ingestion} analysis={analysis} state={state} />
        </aside>

        <section className="min-h-[520px] bg-[var(--panel-muted)] p-3 md:p-4">
          <DocumentPreview
            file={file}
            fileUrl={fileUrl}
            chunks={ingestion?.chunks ?? []}
            activeCitation={activeCitation}
            docxRefs={docxRefs}
          />
        </section>

        <aside className="grid min-h-[640px] grid-rows-[minmax(0,1fr)_minmax(300px,44vh)] border-t border-[var(--border)] bg-[var(--panel)] lg:border-l lg:border-t-0">
          <ClausePanel analysis={analysis} activeRiskByClause={activeRiskByClause} onCitation={handleCitation} />
          <ChatPanel
            disabled={!ingestion || state !== "ready"}
            messages={messages}
            question={question}
            streaming={streaming}
            onQuestionChange={setQuestion}
            onSubmit={submitQuestion}
            onCitation={handleCitation}
          />
        </aside>
      </div>
    </main>
  );
}

function UploadPanel({
  state,
  file,
  error,
  onUpload
}: {
  state: UploadState;
  file: File | null;
  error: string | null;
  onUpload: (file: File) => void;
}) {
  return (
    <Panel className="rounded-md p-3">
      <label
        className="flex min-h-36 cursor-pointer flex-col items-center justify-center gap-3 rounded-md border border-dashed border-[var(--border)] bg-[var(--panel-muted)] p-4 text-center"
        htmlFor="contract-upload"
      >
        <Upload size={24} aria-hidden="true" />
        <span className="text-sm font-medium">{file ? file.name : "Upload PDF or DOCX"}</span>
        <span className="text-xs text-[color-mix(in_srgb,var(--foreground),transparent_40%)]">
          Source locations are preserved for citations.
        </span>
      </label>
      <input
        id="contract-upload"
        className="sr-only"
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={(event) => {
          const selectedFile = event.currentTarget.files?.[0];
          if (selectedFile) {
            onUpload(selectedFile);
          }
        }}
      />
      <div className="mt-3 flex items-center justify-between text-xs">
        <Badge tone={state === "error" ? "high" : state === "ready" ? "success" : "neutral"}>{state}</Badge>
        {state === "uploading" || state === "analyzing" ? <span aria-live="polite">Processing...</span> : null}
      </div>
      {error ? (
        <div className="mt-3 flex gap-2 rounded-md border border-[var(--danger)] p-2 text-sm text-[var(--danger)]" role="alert">
          <XCircle size={18} aria-hidden="true" />
          <span>{error}</span>
        </div>
      ) : null}
    </Panel>
  );
}

function StatusPanel({
  ingestion,
  analysis,
  state
}: {
  ingestion: DocumentIngestionResponse | null;
  analysis: ClauseAnalysisResult | null;
  state: UploadState;
}) {
  return (
    <div className="mt-4 space-y-3 text-sm">
      <div className="flex items-center gap-2">
        <PanelRightOpen size={18} aria-hidden="true" />
        <h2 className="font-semibold">Processing</h2>
      </div>
      <Step label="Upload" active={state !== "idle"} done={Boolean(ingestion)} />
      <Step label="Extract source text" active={state === "uploading"} done={Boolean(ingestion)} />
      <Step label="Analyze clauses" active={state === "analyzing"} done={Boolean(analysis)} />
      <Step label="Ready for questions" active={state === "ready"} done={state === "ready"} />
      {ingestion ? (
        <dl className="mt-4 grid grid-cols-2 gap-2 rounded-md border border-[var(--border)] p-3 text-xs">
          <dt className="text-[color-mix(in_srgb,var(--foreground),transparent_38%)]">Type</dt>
          <dd className="text-right uppercase">{ingestion.document.source_type}</dd>
          <dt className="text-[color-mix(in_srgb,var(--foreground),transparent_38%)]">Chunks</dt>
          <dd className="text-right">{ingestion.chunks.length}</dd>
          <dt className="text-[color-mix(in_srgb,var(--foreground),transparent_38%)]">Status</dt>
          <dd className="text-right">{ingestion.document.status}</dd>
        </dl>
      ) : null}
    </div>
  );
}

function Step({ label, active, done }: { label: string; active: boolean; done: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={cx(
          "h-2.5 w-2.5 rounded-full border border-[var(--border)]",
          done && "bg-[var(--accent)]",
          active && !done && "bg-[var(--warning)]"
        )}
      />
      <span className={done ? "font-medium" : undefined}>{label}</span>
    </div>
  );
}

function DocumentPreview({
  file,
  fileUrl,
  chunks,
  activeCitation,
  docxRefs
}: {
  file: File | null;
  fileUrl: string | null;
  chunks: CandidateChunk[];
  activeCitation: Citation | null;
  docxRefs: React.MutableRefObject<Record<string, HTMLDivElement | null>>;
}) {
  if (!file || !fileUrl) {
    return (
      <div className="flex h-full min-h-[520px] items-center justify-center rounded-md border border-dashed border-[var(--border)] bg-[var(--panel)] p-6 text-center">
        <div>
          <FileText className="mx-auto mb-3" size={32} aria-hidden="true" />
          <h2 className="font-semibold">Document viewer</h2>
          <p className="mt-1 max-w-sm text-sm text-[color-mix(in_srgb,var(--foreground),transparent_35%)]">
            Upload a contract to inspect extracted text, source locations, and citation highlights.
          </p>
        </div>
      </div>
    );
  }
  if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
    return <PdfPreview fileUrl={fileUrl} activeCitation={activeCitation} />;
  }
  return <DocxPreview chunks={chunks} activeCitation={activeCitation} docxRefs={docxRefs} />;
}

function DocxPreview({
  chunks,
  activeCitation,
  docxRefs
}: {
  chunks: CandidateChunk[];
  activeCitation: Citation | null;
  docxRefs: React.MutableRefObject<Record<string, HTMLDivElement | null>>;
}) {
  return (
    <Panel className="h-full overflow-auto rounded-md p-4" aria-label="DOCX document viewer">
      <div className="mx-auto max-w-3xl space-y-3">
        {chunks.map((chunk) => {
          const locator = chunk.source_locators[0];
          const paragraphNumber = locator?.source_type === "docx" ? locator.paragraph_start : chunk.chunk_index + 1;
          const active =
            activeCitation?.source_locator.source_type === "docx" &&
            activeCitation.source_locator.paragraph_start === paragraphNumber;
          return (
            <div
              key={chunk.chunk_id}
              ref={(node) => {
                docxRefs.current[`p-${paragraphNumber}`] = node;
              }}
              className={cx(
                "rounded-md border border-[var(--border)] bg-[var(--panel)] p-4 leading-7",
                active && "citation-highlight"
              )}
              tabIndex={0}
            >
              <div className="mb-2 text-xs text-[color-mix(in_srgb,var(--foreground),transparent_45%)]">
                Paragraph {paragraphNumber}
              </div>
              {chunk.normalized_text.split("\n").map((line) => (
                <p key={line} className={line === chunk.detected_heading ? "font-semibold" : undefined}>
                  {line}
                </p>
              ))}
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

function ClausePanel({
  analysis,
  activeRiskByClause,
  onCitation
}: {
  analysis: ClauseAnalysisResult | null;
  activeRiskByClause: Map<string, RiskAssessment>;
  onCitation: (citation: Citation) => void;
}) {
  return (
    <section className="min-h-0 overflow-auto border-b border-[var(--border)] p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold">Clauses and risk</h2>
        {analysis ? <Badge tone={analysis.manifest.status === "completed" ? "success" : "warning"}>{analysis.manifest.status}</Badge> : null}
      </div>
      {!analysis ? (
        <p className="text-sm text-[color-mix(in_srgb,var(--foreground),transparent_35%)]">Analysis appears after upload.</p>
      ) : (
        <div className="space-y-3">
          {analysis.clauses.map((clause) => {
            const risk = activeRiskByClause.get(clause.clause_id);
            return (
              <motion.article
                key={clause.clause_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-md border border-[var(--border)] p-3"
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge>{clause.clause_type.replaceAll("_", " ")}</Badge>
                  {risk ? <Badge tone={risk.risk_level}>{risk.risk_level} risk</Badge> : null}
                </div>
                <h3 className="text-sm font-semibold">{clause.clause_heading ?? "Clause"}</h3>
                <p className="mt-2 line-clamp-3 text-sm text-[color-mix(in_srgb,var(--foreground),transparent_24%)]">
                  {clause.clause_text}
                </p>
                {risk ? <p className="mt-2 text-xs text-[color-mix(in_srgb,var(--foreground),transparent_30%)]">{risk.risk_reason}</p> : null}
                {clause.source_locators[0] ? (
                  <Button
                    className="mt-3 h-8 text-xs"
                    variant="secondary"
                    type="button"
                    onClick={() =>
                      onCitation({
                        citation_id: clause.clause_id,
                        chunk_id: clause.source_chunk_ids[0],
                        source_locator: clause.source_locators[0],
                        quoted_snippet: clause.clause_heading ?? clause.clause_text.slice(0, 80)
                      })
                    }
                  >
                    <SearchCheck size={14} aria-hidden="true" />
                    Locate
                  </Button>
                ) : null}
              </motion.article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function ChatPanel({
  disabled,
  messages,
  question,
  streaming,
  onQuestionChange,
  onSubmit,
  onCitation
}: {
  disabled: boolean;
  messages: ChatMessage[];
  question: string;
  streaming: boolean;
  onQuestionChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onCitation: (citation: Citation) => void;
}) {
  return (
    <section className="grid min-h-0 grid-rows-[minmax(0,1fr)_auto] p-4">
      <div className="min-h-0 overflow-auto" aria-live="polite">
        <h2 className="mb-3 font-semibold">Questions</h2>
        <div className="space-y-3">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={cx(
                  "rounded-md border p-3 text-sm",
                  message.role === "user" ? "ml-8 border-[var(--accent)] bg-[var(--panel-muted)]" : "mr-8 border-[var(--border)]",
                  message.refused && "border-[var(--warning)]"
                )}
              >
                <div className="mb-1 flex items-center gap-2">
                  <Badge tone={message.role === "user" ? "success" : message.refused ? "warning" : "neutral"}>
                    {message.role === "user" ? "you" : message.refused ? "refusal" : "answer"}
                  </Badge>
                  {message.streaming ? <span className="text-xs">Streaming...</span> : null}
                </div>
                <p>{message.text || "..."}</p>
                {message.citations.length ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {message.citations.map((citation) => (
                      <button
                        key={citation.citation_id}
                        type="button"
                        onClick={() => onCitation(citation)}
                        className="rounded border border-[var(--accent)] px-2 py-1 text-xs hover:bg-[var(--panel-muted)]"
                      >
                        {citation.citation_id}
                      </button>
                    ))}
                  </div>
                ) : null}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
      <form className="mt-4 flex gap-2" onSubmit={onSubmit}>
        <label className="sr-only" htmlFor="question-input">
          Ask a grounded question
        </label>
        <input
          id="question-input"
          className="min-w-0 flex-1 rounded-md border border-[var(--border)] bg-[var(--panel)] px-3 text-sm"
          value={question}
          disabled={disabled || streaming}
          onChange={(event) => onQuestionChange(event.currentTarget.value)}
          placeholder={disabled ? "Upload a contract first" : "Ask about the contract"}
        />
        <Button type="submit" disabled={disabled || streaming || !question.trim()} aria-label="Send question">
          {streaming ? <AlertTriangle size={18} aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
        </Button>
      </form>
    </section>
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
