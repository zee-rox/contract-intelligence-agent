"use client";

import { Maximize2, Minus, Plus } from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import type { Citation } from "@/types/api";
import "react-pdf/dist/Page/TextLayer.css";

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
  const [fitWidth, setFitWidth] = useState(584);
  const [renderedSize, setRenderedSize] = useState({ width: 584, height: 824 });
  const viewerRef = useRef<HTMLDivElement>(null);
  const pageRef = useRef<HTMLDivElement>(null);
  const activePage = activeCitation?.source_locator.source_type === "pdf" ? activeCitation.source_locator.page_number : pageNumber;
  const fallbackBoxes = useMemo(() => {
    if (activeCitation?.source_locator.source_type !== "pdf" || activePage !== pageNumber) {
      return [];
    }
    return activeCitation.source_locator.bounding_boxes;
  }, [activeCitation, activePage, pageNumber]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    const resize = () => setFitWidth(Math.max(280, viewer.clientWidth - 32));
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(viewer);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (activeCitation?.source_locator.source_type === "pdf") {
      onPageChange(activeCitation.source_locator.page_number);
    }
  }, [activeCitation, onPageChange]);

  useEffect(() => {
    pageRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [pageNumber]);

  function handlePageCount(count: number) {
    setPageCount(count);
    onPageCountChange(count);
  }

  const pageWidth = Math.round(fitWidth * zoom);

  return (
    <div ref={viewerRef} className="cia-pdf-viewer" aria-label="PDF document viewer">
      <Document file={fileUrl} onLoadSuccess={({ numPages }) => handlePageCount(numPages)}>
        <div ref={pageRef} className="cia-pdf-page-shell cia-pdf-page-shell-enter">
          <div className="cia-pdf-page">
            <Page
              pageNumber={pageNumber}
              width={pageWidth}
              renderTextLayer
              renderAnnotationLayer={false}
              onRenderSuccess={(page) => setRenderedSize({ width: page.width, height: page.height })}
            />
            <PdfCitationHighlight
              pageRef={pageRef}
              citation={activeCitation}
              pageNumber={pageNumber}
              fallbackBoxes={fallbackBoxes}
              renderedSize={renderedSize}
            />
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
        <button type="button" aria-label="Fit width" title="Fit to pane width" onClick={() => setZoom(1)}>
          <Maximize2 size={15} aria-hidden="true" />
        </button>
      </div>
      <p className="sr-only" aria-live="polite">
        Page {pageNumber} of {pageCount}
      </p>
    </div>
  );
}

function PdfCitationHighlight({
  pageRef,
  citation,
  pageNumber,
  fallbackBoxes,
  renderedSize
}: {
  pageRef: React.RefObject<HTMLDivElement | null>;
  citation: Citation | null;
  pageNumber: number;
  fallbackBoxes: Array<{ x0: number; y0: number; x1: number; y1: number }>;
  renderedSize: { width: number; height: number };
}) {
  const [rects, setRects] = useState<Array<{ left: number; top: number; width: number; height: number }>>([]);

  useEffect(() => {
    const page = pageRef.current;
    if (!page || citation?.source_locator.source_type !== "pdf" || citation.source_locator.page_number !== pageNumber) {
      setRects([]);
      return;
    }
    const textLayer = page.querySelector(".react-pdf__Page__textContent");
    const spans = textLayer ? Array.from(textLayer.querySelectorAll("span")) : [];
    const snippet = citation.quoted_snippet.trim().replace(/\s+/g, " ");
    const mapped: Array<{ node: Text; start: number; end: number }> = [];
    let text = "";
    for (const span of spans) {
      const node = span.firstChild;
      if (!(node instanceof Text)) continue;
      const start = text.length;
      text += `${node.textContent ?? ""} `;
      mapped.push({ node, start, end: text.length });
    }
    const normalizedText = text.replace(/\s+/g, " ");
    const matchStart = normalizedText.toLowerCase().indexOf(snippet.toLowerCase());
    if (matchStart >= 0) {
      const matchEnd = matchStart + snippet.length;
      const startEntry = mapped.find((entry) => matchStart >= entry.start && matchStart < entry.end);
      const endEntry = mapped.find((entry) => matchEnd > entry.start && matchEnd <= entry.end);
      if (startEntry && endEntry) {
        const range = document.createRange();
        range.setStart(startEntry.node, Math.max(0, matchStart - startEntry.start));
        range.setEnd(endEntry.node, Math.min(endEntry.node.length, matchEnd - endEntry.start));
        const pageBox = page.getBoundingClientRect();
        setRects(Array.from(range.getClientRects()).map((rect) => ({
          left: rect.left - pageBox.left,
          top: rect.top - pageBox.top,
          width: rect.width,
          height: Math.max(14, rect.height)
        })));
        return;
      }
    }
    const scaleX = renderedSize.width / 612;
    const scaleY = renderedSize.height / 792;
    setRects(fallbackBoxes.map((box) => ({
      left: Math.max(0, box.x0 * scaleX),
      top: Math.max(0, box.y0 * scaleY),
      width: Math.max(24, (box.x1 - box.x0) * scaleX),
      height: Math.max(18, (box.y1 - box.y0) * scaleY)
    })));
  }, [citation, fallbackBoxes, pageNumber, pageRef, renderedSize]);

  return (
    <>
      {rects.map((rect, index) => (
        <div key={index} aria-label={index === 0 ? "Active clause citation highlight" : undefined} className="cia-pdf-highlight" style={rect} />
      ))}
    </>
  );
}
