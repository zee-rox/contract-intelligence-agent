"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  ArrowUp,
  ChevronUp,
  FileUp,
  MoreHorizontal,
  Search,
  Upload
} from "lucide-react";
import dynamic from "next/dynamic";
import React from "react";
import { Button } from "@/components/ui/button";
import { cx } from "@/lib/utils";
import type {
  CandidateChunk,
  Citation,
  ClauseAnalysisResult,
  ExtractedClause,
  RiskAssessment,
  SourceLocator
} from "@/types/api";

const PdfPreview = dynamic(() => import("./pdf-preview").then((module) => module.PdfPreview), {
  ssr: false,
  loading: () => <SkeletonLoader variant="document" />
});

export type UploadState = "idle" | "uploading" | "analyzing" | "ready" | "error";
export type WorkspaceTab = "document" | "analysis";
export type ChatThreadMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations: Citation[];
  refused?: boolean;
  refusalReason?: string;
  streaming?: boolean;
};

type UploadHandler = (file: File) => void;

export function TopBar({
  title,
  meta,
  status,
  page,
  pageCount,
  hasDocument,
  onUpload
}: {
  title: string;
  meta: string | null;
  status: UploadState;
  page: number;
  pageCount: number;
  hasDocument: boolean;
  onUpload: UploadHandler;
}) {
  return (
    <header className="cia-topbar">
      <div className="cia-brand-mark" aria-hidden="true">
        C
      </div>
      <div className="cia-title-block">
        <h1>{hasDocument ? title : "Contract Intelligence"}</h1>
        {meta ? <p>{meta}</p> : null}
      </div>
      <StatusPill status={status} />
      <div className="cia-topbar-spacer" />
      {hasDocument && status === "ready" ? (
        <p className="cia-page-indicator" aria-live="polite">
          Page {page} of {Math.max(pageCount, page)}
        </p>
      ) : null}
      {hasDocument && status === "ready" ? (
        <>
          <label className="cia-icon-button" title="Upload another contract" aria-label="Upload another contract">
            <Upload size={19} aria-hidden="true" />
            <input className="sr-only" type="file" accept={acceptedFileTypes} onChange={(event) => pickFile(event, onUpload)} />
          </label>
          <button className="cia-icon-button cia-icon-button-ghost" type="button" aria-label="More document actions" title="More actions">
            <MoreHorizontal size={20} aria-hidden="true" />
          </button>
        </>
      ) : null}
    </header>
  );
}

export function MobileTabs({ activeTab, onChange }: { activeTab: WorkspaceTab; onChange: (tab: WorkspaceTab) => void }) {
  return (
    <div className="cia-mobile-tabs" role="tablist" aria-label="Workspace views">
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === "document"}
        className={activeTab === "document" ? "active" : undefined}
        onClick={() => onChange("document")}
      >
        Document
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === "analysis"}
        className={activeTab === "analysis" ? "active" : undefined}
        onClick={() => onChange("analysis")}
      >
        Analysis
      </button>
    </div>
  );
}

export function DocumentViewer({
  state,
  error,
  file,
  fileUrl,
  chunks,
  activeCitation,
  activePage,
  pageCount,
  docxRefs,
  onUpload,
  onPageChange,
  onPageCountChange
}: {
  state: UploadState;
  error: string | null;
  file: File | null;
  fileUrl: string | null;
  chunks: CandidateChunk[];
  activeCitation: Citation | null;
  activePage: number;
  pageCount: number;
  docxRefs: React.MutableRefObject<Record<string, HTMLElement | null>>;
  onUpload: UploadHandler;
  onPageChange: (page: number) => void;
  onPageCountChange: (count: number) => void;
}) {
  if (state === "idle") {
    return (
      <div className="cia-document-pane cia-document-empty">
        <EmptyState kind="upload" onUpload={onUpload} />
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="cia-document-pane cia-document-empty">
        <EmptyState kind="error" title="The contract could not be processed" body={error ?? "Upload failed."} onUpload={onUpload} />
      </div>
    );
  }

  if (state === "uploading" || state === "analyzing") {
    return (
      <div className="cia-document-pane">
        <SkeletonLoader variant="document" />
      </div>
    );
  }

  if (!file || !fileUrl) {
    return (
      <div className="cia-document-pane cia-document-empty">
        <EmptyState kind="upload" onUpload={onUpload} />
      </div>
    );
  }

  if (isPdf(file)) {
    return (
      <div className="cia-document-pane">
        <PageThumbnailRail activePage={activePage} pageCount={pageCount} onPageChange={onPageChange} />
        <PdfPreview
          fileUrl={fileUrl}
          activeCitation={activeCitation}
          pageNumber={activePage}
          onPageChange={onPageChange}
          onPageCountChange={onPageCountChange}
        />
      </div>
    );
  }

  return (
    <div className="cia-document-pane">
      <PageThumbnailRail activePage={activeDocxParagraph(activeCitation)} pageCount={Math.max(chunks.length, 1)} onPageChange={() => undefined} />
      <DocxPreview chunks={chunks} activeCitation={activeCitation} docxRefs={docxRefs} />
    </div>
  );
}

export function PageThumbnailRail({
  activePage,
  pageCount,
  onPageChange
}: {
  activePage: number;
  pageCount: number;
  onPageChange: (page: number) => void;
}) {
  const pages = visiblePages(activePage, pageCount);
  return (
    <nav className="cia-thumbnail-rail" aria-label="Document pages">
      {pages.map((page) => (
        <button
          key={page}
          type="button"
          className={page === activePage ? "active" : undefined}
          onClick={() => onPageChange(page)}
          aria-label={`Go to page ${page}`}
          aria-current={page === activePage ? "page" : undefined}
          title={`Page ${page}`}
        >
          <span />
          <strong>{page}</strong>
        </button>
      ))}
    </nav>
  );
}

function StatusPill({ status }: { status: UploadState }) {
  const labels: Record<UploadState, string> = {
    idle: "No document",
    uploading: "Parsing...",
    analyzing: "Parsing...",
    ready: "Ready",
    error: "Needs review"
  };
  return (
    <span className="cia-status-pill" aria-live="polite">
      {labels[status]}
    </span>
  );
}

export function ClauseSummaryTable({
  analysis,
  activeRiskByClause,
  onCitation
}: {
  analysis: ClauseAnalysisResult | null;
  activeRiskByClause: Map<string, RiskAssessment>;
  onCitation: (citation: Citation) => void;
}) {
  const clauses = analysis?.clauses ?? [];
  return (
    <section className="cia-clause-section" aria-labelledby="clause-summary-heading">
      <div className="cia-section-heading">
        <div>
          <h2 id="clause-summary-heading">Clause summary</h2>
          {analysis ? <span className="cia-count-pill">{clauses.length} clauses</span> : null}
        </div>
        {analysis ? (
          <button type="button" className="cia-sort-button" aria-label="Sort clauses by risk" title="Risk sorted high first">
            Risk: High first <ChevronUp size={16} aria-hidden="true" />
          </button>
        ) : null}
      </div>
      {!analysis ? (
        <p className="cia-muted-copy">Analysis appears after upload.</p>
      ) : (
        <div className="cia-clause-table" aria-label="Clause summary table">
          {clauses.map((clause, index) => {
            const risk = activeRiskByClause.get(clause.clause_id);
            const citation = citationFromClause(clause);
            return (
              <button
                key={clause.clause_id}
                type="button"
                className={cx("cia-clause-row", index === 0 && "active")}
                onClick={() => citation && onCitation(citation)}
                disabled={!citation}
                title={citation ? `Show source for ${readableClauseType(clause.clause_type)}` : undefined}
              >
                <span>
                  <strong>{clause.clause_heading ?? readableClauseType(clause.clause_type)}</strong>
                  <small>{summarizeClause(clause, risk)}</small>
                </span>
                {risk ? <RiskBadge level={risk.risk_level} /> : null}
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}

export function RiskBadge({ level }: { level: RiskAssessment["risk_level"] }) {
  return <span className={cx("cia-risk-badge", `risk-${level}`)}>{capitalize(level)}</span>;
}

export function AnalysisPane({
  state,
  error,
  analysis,
  activeRiskByClause,
  messages,
  question,
  streaming,
  onQuestionChange,
  onQuestionSubmit,
  onCitation
}: {
  state: UploadState;
  error: string | null;
  analysis: ClauseAnalysisResult | null;
  activeRiskByClause: Map<string, RiskAssessment>;
  messages: ChatThreadMessage[];
  question: string;
  streaming: boolean;
  onQuestionChange: (value: string) => void;
  onQuestionSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onCitation: (citation: Citation) => void;
}) {
  if (state === "idle") {
    return (
      <div className="cia-analysis-pane cia-analysis-centered">
        <EmptyState kind="analysis" />
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="cia-analysis-pane cia-analysis-centered">
        <EmptyState kind="error" title="Review unavailable" body={error ?? "Upload failed."} />
      </div>
    );
  }

  if (state === "uploading" || state === "analyzing") {
    return (
      <div className="cia-analysis-pane">
        <SkeletonLoader variant="analysis" />
        <div className="cia-processing-chat">
          <h2>Preparing your analysis</h2>
          <p>You can ask questions once indexing is complete.</p>
        </div>
        <ChatInput disabled value="" streaming={false} onChange={() => undefined} onSubmit={(event) => event.preventDefault()} />
      </div>
    );
  }

  return (
    <div className="cia-analysis-pane">
      <ClauseSummaryTable analysis={analysis} activeRiskByClause={activeRiskByClause} onCitation={onCitation} />
      <div className="cia-collapse-strip">
        <span>Clause summary</span>
        <ChevronUp size={16} aria-hidden="true" />
      </div>
      <ChatThread messages={messages} onCitation={onCitation} />
      <ChatInput
        disabled={state !== "ready"}
        value={question}
        streaming={streaming}
        onChange={onQuestionChange}
        onSubmit={onQuestionSubmit}
      />
    </div>
  );
}

export function ChatThread({
  messages,
  onCitation
}: {
  messages: ChatThreadMessage[];
  onCitation: (citation: Citation) => void;
}) {
  return (
    <section className="cia-chat-thread" aria-labelledby="chat-heading" aria-live="polite">
      <h2 id="chat-heading">Ask this contract</h2>
      {messages.length === 0 ? (
        <div className="cia-chat-placeholder">
          <p>Ask about termination terms, liability caps, renewal dates, or any clause in this contract.</p>
        </div>
      ) : (
        <div className="cia-message-list">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} onCitation={onCitation} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </section>
  );
}

export function ChatMessage({
  message,
  onCitation
}: {
  message: ChatThreadMessage;
  onCitation: (citation: Citation) => void;
}) {
  if (message.role === "user") {
    return (
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="cia-user-message">
        {message.text}
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="cia-assistant-message">
      <p className="cia-assistant-label">{message.refused ? "REFUSAL" : "CONTRACT INTELLIGENCE"}</p>
      <p>{message.text || (message.streaming ? "Reading the cited sections..." : "")}</p>
      {message.citations.length ? (
        <div className="cia-citation-row">
          {message.citations.map((citation) => (
            <CitationChip key={citation.citation_id} citation={citation} onClick={onCitation} />
          ))}
        </div>
      ) : null}
      {message.refused ? (
        <div className="cia-boundary-message">
          <p>
            {message.refusalReason
              ? `The document does not provide enough information. Reason: ${message.refusalReason}.`
              : "The document does not provide enough information to answer without guessing."}
          </p>
        </div>
      ) : null}
    </motion.div>
  );
}

export function CitationChip({ citation, onClick }: { citation: Citation; onClick: (citation: Citation) => void }) {
  const label = sourceLabel(citation.source_locator);
  return (
    <button
      type="button"
      className="cia-citation-chip"
      onClick={() => onClick(citation)}
      title={`Show citation ${citation.citation_id}: ${citation.quoted_snippet}`}
      aria-label={`Show citation ${citation.citation_id} from ${label}`}
    >
      {label}
    </button>
  );
}

export function ChatInput({
  disabled,
  value,
  streaming,
  onChange,
  onSubmit
}: {
  disabled: boolean;
  value: string;
  streaming: boolean;
  onChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form className="cia-chat-input" onSubmit={onSubmit}>
      <label className="sr-only" htmlFor="question-input">
        Ask a grounded question
      </label>
      <textarea
        id="question-input"
        value={value}
        disabled={disabled || streaming}
        onChange={(event) => onChange(event.currentTarget.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            event.currentTarget.form?.requestSubmit();
          }
        }}
        placeholder={disabled ? "Preparing document..." : "Ask about termination terms, liability caps, renewal dates..."}
      />
      <p>Enter to send • Shift + Enter for a new line</p>
      <Button type="submit" disabled={disabled || streaming || !value.trim()} aria-label="Send question" className="cia-send-button">
        {streaming ? <AlertCircle size={18} aria-hidden="true" /> : <ArrowUp size={18} aria-hidden="true" />}
      </Button>
    </form>
  );
}

export function EmptyState({
  kind,
  title,
  body,
  onUpload
}: {
  kind: "upload" | "analysis" | "error";
  title?: string;
  body?: string;
  onUpload?: UploadHandler;
}) {
  const isUpload = kind === "upload";
  const Icon = kind === "analysis" ? Search : kind === "error" ? AlertCircle : FileUp;
  return (
    <div className={cx("cia-empty-state", kind === "analysis" && "cia-empty-analysis", kind === "error" && "cia-empty-error")}>
      <div className="cia-empty-icon" aria-hidden="true">
        <Icon size={isUpload ? 42 : 36} strokeWidth={1.8} />
      </div>
      <h2>{title ?? (isUpload ? "Drop a contract here" : "Upload a document to get started")}</h2>
      <p>{body ?? (isUpload ? "or click to browse a PDF or DOCX from your computer" : "Clauses, risks, and source-backed answers will appear here.")}</p>
      {isUpload && onUpload ? (
        <>
          <label className="cia-primary-upload">
            Choose PDF
            <input className="sr-only" type="file" accept={acceptedFileTypes} onChange={(event) => pickFile(event, onUpload)} />
          </label>
          <small>PDF or DOCX up to 25 MB • Your document stays private</small>
        </>
      ) : null}
    </div>
  );
}

export function SkeletonLoader({ variant }: { variant: "document" | "analysis" }) {
  if (variant === "analysis") {
    return (
      <section className="cia-clause-section" aria-label="Loading clause analysis">
        <div className="cia-section-heading">
          <h2>Clause summary</h2>
        </div>
        <div className="cia-analysis-skeleton">
          {Array.from({ length: 5 }, (_, index) => (
            <div key={index} className="cia-skeleton-row">
              <span />
              <small />
              <strong />
            </div>
          ))}
        </div>
      </section>
    );
  }

  return (
    <div className="cia-document-skeleton" aria-label="Reading your contract">
      <div className="cia-faux-page">
        {Array.from({ length: 18 }, (_, index) => (
          <span key={index} style={{ width: `${[70, 62, 54, 46][index % 4]}%` }} />
        ))}
      </div>
      <div className="cia-progress-card" role="status" aria-live="polite">
        <h2>Reading your contract</h2>
        <p>Extracting text and preserving page references...</p>
        <div>
          <span />
        </div>
      </div>
    </div>
  );
}

function DocxPreview({
  chunks,
  activeCitation,
  docxRefs
}: {
  chunks: CandidateChunk[];
  activeCitation: Citation | null;
  docxRefs: React.MutableRefObject<Record<string, HTMLElement | null>>;
}) {
  return (
    <div className="cia-docx-scroll" aria-label="DOCX document viewer">
      <article className="cia-docx-page">
        {chunks.map((chunk) => {
          const locator = chunk.source_locators[0];
          const paragraphNumber = locator?.source_type === "docx" ? locator.paragraph_start : chunk.chunk_index + 1;
          const active =
            activeCitation?.source_locator.source_type === "docx" &&
            activeCitation.source_locator.paragraph_start === paragraphNumber;
          return (
            <section
              key={chunk.chunk_id}
              ref={(node) => {
                docxRefs.current[`p-${paragraphNumber}`] = node;
              }}
              className={cx("cia-docx-paragraph", active && "citation-highlight")}
              tabIndex={0}
            >
              <small>Paragraph {paragraphNumber}</small>
              {chunk.normalized_text.split("\n").map((line, index) => (
                <p key={`${chunk.chunk_id}-${index}`} className={line === chunk.detected_heading ? "heading" : undefined}>
                  {line}
                </p>
              ))}
            </section>
          );
        })}
      </article>
    </div>
  );
}

const acceptedFileTypes = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

function pickFile(event: React.ChangeEvent<HTMLInputElement>, onUpload: UploadHandler) {
  const selectedFile = event.currentTarget.files?.[0];
  if (selectedFile) {
    onUpload(selectedFile);
  }
}

function isPdf(file: File) {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

function visiblePages(activePage: number, pageCount: number) {
  const total = Math.max(pageCount, activePage, 1);
  const start = Math.min(Math.max(activePage - 1, 1), Math.max(total - 3, 1));
  return Array.from({ length: Math.min(4, total) }, (_, index) => start + index);
}

function activeDocxParagraph(citation: Citation | null) {
  return citation?.source_locator.source_type === "docx" ? citation.source_locator.paragraph_start : 1;
}

function citationFromClause(clause: ExtractedClause): Citation | null {
  const sourceLocator = clause.source_locators[0];
  const chunkId = clause.source_chunk_ids[0];
  if (!sourceLocator || !chunkId) {
    return null;
  }
  return {
    citation_id: clause.clause_id,
    chunk_id: chunkId,
    source_locator: sourceLocator,
    quoted_snippet: clause.clause_text.slice(0, 160)
  };
}

function readableClauseType(type: string) {
  return type.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function summarizeClause(clause: ExtractedClause, risk: RiskAssessment | undefined) {
  if (risk?.risk_reason) {
    return risk.risk_reason;
  }
  return clause.clause_text.replace(/\s+/g, " ").slice(0, 120);
}

function sourceLabel(locator: SourceLocator) {
  if (locator.source_type === "pdf") {
    return `p. ${locator.page_number}`;
  }
  return `para. ${locator.paragraph_start}`;
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
