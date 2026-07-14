"use client";

import { Maximize2, Minus, Plus } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import type { Citation } from "@/types/api";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export function PdfPreview({
  fileUrl,
  activeCitation,
  pageNumber,
  onPageChange,
  onPageCountChange
}: {
  fileUrl: string;
  activeCitation: Citation | null;
  pageNumber: number;
  onPageChange: (page: number) => void;
  onPageCountChange: (count: number) => void;
}) {
  const [pageCount, setPageCount] = useState(1);
  const [zoom, setZoom] = useState(1);
  const activePage = activeCitation?.source_locator.source_type === "pdf" ? activeCitation.source_locator.page_number : pageNumber;
  const highlight = useMemo(() => {
    if (activeCitation?.source_locator.source_type !== "pdf" || activePage !== pageNumber) {
      return null;
    }
    return activeCitation.source_locator.bounding_boxes[0] ?? null;
  }, [activeCitation, activePage, pageNumber]);

  useEffect(() => {
    if (activeCitation?.source_locator.source_type === "pdf") {
      onPageChange(activeCitation.source_locator.page_number);
    }
  }, [activeCitation, onPageChange]);

  function handlePageCount(count: number) {
    setPageCount(count);
    onPageCountChange(count);
  }

  const pageWidth = Math.round(584 * zoom);

  return (
    <div className="cia-pdf-viewer" aria-label="PDF document viewer">
      <Document file={fileUrl} onLoadSuccess={({ numPages }) => handlePageCount(numPages)}>
        <div className="cia-pdf-page-shell">
          <div className="cia-pdf-page">
            <Page pageNumber={pageNumber} width={pageWidth} renderTextLayer renderAnnotationLayer={false} />
            {highlight ? (
              <div
                aria-label="Active PDF citation highlight"
                className="cia-pdf-highlight"
                style={{
                  left: `${Math.max(0, highlight.x0) * zoom}px`,
                  top: `${Math.max(0, highlight.y0) * zoom}px`,
                  width: `${Math.max(24, highlight.x1 - highlight.x0) * zoom}px`,
                  height: `${Math.max(18, highlight.y1 - highlight.y0) * zoom}px`
                }}
              />
            ) : null}
          </div>
          <span className="cia-printed-page">{pageNumber}</span>
        </div>
      </Document>
      <div className="cia-zoom-controls" aria-label="PDF zoom controls">
        <button type="button" aria-label="Zoom out" onClick={() => setZoom((value) => Math.max(0.75, value - 0.1))}>
          <Minus size={16} aria-hidden="true" />
        </button>
        <span>{Math.round(zoom * 100)}%</span>
        <button type="button" aria-label="Zoom in" onClick={() => setZoom((value) => Math.min(1.3, value + 0.1))}>
          <Plus size={16} aria-hidden="true" />
        </button>
        <button type="button" aria-label="Fit width" onClick={() => setZoom(1)}>
          <Maximize2 size={15} aria-hidden="true" />
        </button>
      </div>
      <p className="sr-only" aria-live="polite">
        Page {pageNumber} of {pageCount}
      </p>
    </div>
  );
}
