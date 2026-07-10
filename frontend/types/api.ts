export type SourceLocator =
  | {
      source_type: "pdf";
      page_number: number;
      char_offset_start: number | null;
      char_offset_end: number | null;
      bounding_boxes: Array<{ x0: number; y0: number; x1: number; y1: number }>;
    }
  | {
      source_type: "docx";
      section_number: number | null;
      paragraph_start: number;
      paragraph_end: number;
      char_offset_start: number | null;
      char_offset_end: number | null;
    };

export type CandidateChunk = {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  normalized_text: string;
  detected_heading: string | null;
  source_locators: SourceLocator[];
  char_count: number;
  token_count_estimate: number;
  splitter_strategy: string;
};

export type DocumentRecord = {
  document_id: string;
  original_filename: string;
  sanitized_filename: string;
  source_type: "pdf" | "docx";
  content_type: string;
  file_size_bytes: number;
  sha256: string;
  status: string;
  created_at: string;
  updated_at: string;
  parser_version: string;
  error_code: string | null;
  error_message: string | null;
};

export type DocumentIngestionResponse = {
  document: DocumentRecord;
  chunks: CandidateChunk[];
};

export type ExtractedClause = {
  clause_id: string;
  document_id: string;
  clause_type: string;
  clause_heading: string | null;
  clause_text: string;
  source_chunk_ids: string[];
  source_locators: SourceLocator[];
  confidence: "high" | "medium" | "low";
  extraction_notes: string | null;
};

export type RiskAssessment = {
  clause_id: string;
  risk_level: "low" | "medium" | "high";
  risk_reason: string;
  observed_factors: string[];
  missing_expected_elements: string[];
  confidence: "high" | "medium" | "low";
  baseline_version: string;
};

export type ClauseAnalysisResult = {
  document_id: string;
  clauses: ExtractedClause[];
  risks: RiskAssessment[];
  manifest: {
    document_id: string;
    status: "completed" | "partial_failure" | "failed";
    prompt_version: string;
    risk_baseline_version: string;
    provider: string;
    model: string;
    graph_version: string;
    created_at: string;
    warnings: string[];
  };
};

export type Citation = {
  citation_id: string;
  chunk_id: string;
  source_locator: SourceLocator;
  quoted_snippet: string;
};

export type QAResponse = {
  answer: string;
  citations: Citation[];
  confidence: "high" | "medium" | "low";
  refused: boolean;
  refusal_reason: string | null;
};
