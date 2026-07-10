"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import React from "react";
import { useMemo, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import type { Citation } from "@/types/api";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export function PdfPreview({ fileUrl, activeCitation }: { fileUrl: string; activeCitation: Citation | null }) {
  const [pageCount, setPageCount] = useState(1);
  const activePage = activeCitation?.source_locator.source_type === "pdf" ? activeCitation.source_locator.page_number : 1;
  const [pageNumber, setPageNumber] = useState(activePage);
  const highlight = useMemo(() => {
    if (activeCitation?.source_locator.source_type !== "pdf") {
      return null;
    }
    return activeCitation.source_locator.bounding_boxes[0] ?? null;
  }, [activeCitation]);

  return (
    <Panel className="flex h-full flex-col rounded-md" aria-label="PDF document viewer">
      <div className="flex items-center justify-between border-b border-[var(--border)] p-3">
        <Button type="button" variant="secondary" onClick={() => setPageNumber((page) => Math.max(1, page - 1))} aria-label="Previous page">
          <ChevronLeft size={18} aria-hidden="true" />
        </Button>
        <span className="text-sm">
          Page {pageNumber} of {pageCount}
        </span>
        <Button
          type="button"
          variant="secondary"
          onClick={() => setPageNumber((page) => Math.min(pageCount, page + 1))}
          aria-label="Next page"
        >
          <ChevronRight size={18} aria-hidden="true" />
        </Button>
      </div>
      <div className="relative min-h-0 flex-1 overflow-auto p-4">
        <Document file={fileUrl} onLoadSuccess={({ numPages }) => setPageCount(numPages)}>
          <div className="relative mx-auto w-fit">
            <Page pageNumber={pageNumber} width={720} renderTextLayer renderAnnotationLayer={false} />
            {highlight && pageNumber === activePage ? (
              <div
                aria-label="Active PDF citation highlight"
                className="pointer-events-none absolute border-2 border-[var(--accent)] bg-[color-mix(in_srgb,var(--accent),transparent_80%)]"
                style={{
                  left: `${Math.max(0, highlight.x0)}px`,
                  top: `${Math.max(0, highlight.y0)}px`,
                  width: `${Math.max(24, highlight.x1 - highlight.x0)}px`,
                  height: `${Math.max(18, highlight.y1 - highlight.y0)}px`
                }}
              />
            ) : null}
          </div>
        </Document>
      </div>
    </Panel>
  );
}
