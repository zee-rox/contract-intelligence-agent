import { render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import React from "react";
import { act } from "react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ContractWorkspace } from "@/features/workspace/contract-workspace";
import { MockEventSource } from "./setup";

const docxUploadResponse = {
  document: {
    document_id: "doc-1",
    original_filename: "sample.docx",
    sanitized_filename: "sample.docx",
    source_type: "docx",
    content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    file_size_bytes: 123,
    sha256: "abc",
    status: "ready",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    parser_version: "test",
    error_code: null,
    error_message: null
  },
  chunks: [
    {
      chunk_id: "chunk_1",
      document_id: "doc-1",
      chunk_index: 0,
      text: "Payment\nInvoices are due within thirty days.",
      normalized_text: "Payment\nInvoices are due within thirty days.",
      detected_heading: "Payment",
      source_locators: [
        {
          source_type: "docx",
          section_number: 1,
          paragraph_start: 1,
          paragraph_end: 1,
          char_offset_start: 0,
          char_offset_end: 43
        }
      ],
      char_count: 43,
      token_count_estimate: 7,
      splitter_strategy: "structural"
    }
  ]
};

const analysisResponse = {
  document_id: "doc-1",
  clauses: [
    {
      clause_id: "clause_1",
      document_id: "doc-1",
      clause_type: "payment_terms",
      clause_heading: "Payment",
      clause_text: "Payment\nInvoices are due within thirty days.",
      source_chunk_ids: ["chunk_1"],
      source_locators: docxUploadResponse.chunks[0].source_locators,
      confidence: "medium",
      extraction_notes: null
    }
  ],
  risks: [
    {
      clause_id: "clause_1",
      risk_level: "low",
      risk_reason: "No obvious baseline concern was detected.",
      observed_factors: [],
      missing_expected_elements: [],
      confidence: "medium",
      baseline_version: "risk-baseline-v1"
    }
  ],
  manifest: {
    document_id: "doc-1",
    status: "completed",
    prompt_version: "test",
    risk_baseline_version: "risk-baseline-v1",
    provider: "fake",
    model: "fake",
    graph_version: "analysis-graph-v1",
    created_at: "2026-01-01T00:00:00Z",
    warnings: []
  }
};

describe("ContractWorkspace", () => {
  beforeEach(() => {
    MockEventSource.instances = [];
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uploads a DOCX, renders clauses, and navigates citation chips", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/documents")) {
        return jsonResponse(docxUploadResponse);
      }
      if (url.endsWith("/documents/doc-1/clauses")) {
        return jsonResponse(analysisResponse);
      }
      return jsonResponse({}, 404);
    });

    render(<ContractWorkspace />);
    const fileInput = screen.getByLabelText(/choose pdf/i);
    await userEvent.upload(
      fileInput,
      new File(["contract"], "sample.docx", {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      })
    );

    expect((await screen.findAllByText("Payment")).length).toBeGreaterThan(0);
    await userEvent.click(screen.getByRole("button", { name: /payment/i }));
    expect(screen.getByText(/Paragraph 1/i).parentElement).toHaveClass("citation-highlight");
  });

  it("streams supported answers and refused answers distinctly", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/documents")) {
        return jsonResponse(docxUploadResponse);
      }
      if (url.endsWith("/documents/doc-1/clauses")) {
        return jsonResponse(analysisResponse);
      }
      return jsonResponse({}, 404);
    });

    render(<ContractWorkspace />);
    await userEvent.upload(
      screen.getByLabelText(/choose pdf/i),
      new File(["contract"], "sample.docx", {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      })
    );
    await screen.findAllByText("Payment");

    await userEvent.type(screen.getByLabelText(/ask a grounded question/i), "When are invoices due?");
    await userEvent.click(screen.getByRole("button", { name: /send question/i }));
    const source = MockEventSource.instances[0];
    act(() => {
      source.emit("answer_delta", { text: "Invoices are due within thirty days. " });
      source.emit("citation", {
        citation_id: "cit_0000",
        chunk_id: "chunk_1",
        quoted_snippet: "Invoices are due within thirty days.",
        source_locator: docxUploadResponse.chunks[0].source_locators[0]
      });
      source.emit("final", {
        answer: "Invoices are due within thirty days. [cit_0000]",
        citations: [
          {
            citation_id: "cit_0000",
            chunk_id: "chunk_1",
            quoted_snippet: "Invoices are due within thirty days.",
            source_locator: docxUploadResponse.chunks[0].source_locators[0]
          }
        ],
        confidence: "medium",
        refused: false,
        refusal_reason: null
      });
    });

    await waitFor(() => expect(screen.getAllByRole("button", { name: /show citation cit_0000/i }).length).toBeGreaterThan(0));

    await userEvent.type(screen.getByLabelText(/ask a grounded question/i), "What insurance is required?");
    await userEvent.click(screen.getByRole("button", { name: /send question/i }));
    const refusalSource = MockEventSource.instances[1];
    act(() => {
      refusalSource.emit("refusal", {
        answer: "The document does not provide enough information.",
        reason: "insufficient_evidence"
      });
      refusalSource.emit("final", {
        answer: "The document does not provide enough information.",
        citations: [],
        confidence: "low",
        refused: true,
        refusal_reason: "insufficient_evidence"
      });
    });

    const messages = screen.getAllByText(/refusal/i);
    expect(messages.length).toBeGreaterThan(0);
  });

  it("renders a PDF preview and backend errors", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: { message: "unsupported file type" } }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      })
    );

    render(<ContractWorkspace />);
    await userEvent.upload(screen.getByLabelText(/choose pdf/i), new File(["%PDF"], "bad.pdf", { type: "application/pdf" }));

    expect((await screen.findAllByText(/unsupported file type/i)).length).toBeGreaterThan(0);
  });

  it("switches between mobile workspace tabs from the keyboard", async () => {
    render(<ContractWorkspace />);
    const analysisTab = screen.getByRole("tab", { name: /analysis/i });
    analysisTab.focus();
    await userEvent.keyboard("{Enter}");
    expect(analysisTab).toHaveAttribute("aria-selected", "true");
  });

  it("has no critical accessibility violations in the empty workspace", async () => {
    const { container } = render(<ContractWorkspace />);
    const results = await axe(container);
    const critical = results.violations.filter((violation) => violation.impact === "critical");
    expect(critical).toEqual([]);
  });
});

function jsonResponse(payload: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), {
      status,
      headers: { "Content-Type": "application/json" }
    })
  );
}
