import "@testing-library/jest-dom/vitest";
import React from "react";
import { vi } from "vitest";

class MockEventSource {
  url: string;
  onmessage: ((event: MessageEvent) => void) | null = null;
  listeners: Record<string, Array<(event: MessageEvent) => void>> = {};

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  static instances: MockEventSource[] = [];

  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    this.listeners[type] = [...(this.listeners[type] ?? []), listener];
  }

  close() {}

  emit(type: string, data: unknown) {
    const event = new MessageEvent(type, { data: JSON.stringify(data) });
    for (const listener of this.listeners[type] ?? []) {
      listener(event);
    }
  }
}

Object.defineProperty(window, "EventSource", {
  value: MockEventSource,
  writable: true
});

Object.defineProperty(URL, "createObjectURL", {
  value: () => "blob:contract-preview",
  writable: true
});

Object.defineProperty(URL, "revokeObjectURL", {
  value: () => undefined,
  writable: true
});

vi.mock("react-pdf", () => ({
  pdfjs: { version: "mock", GlobalWorkerOptions: { workerSrc: "" } },
  Document: ({ children }: { children: React.ReactNode }) => <div data-testid="pdf-document">{children}</div>,
  Page: ({ pageNumber }: { pageNumber: number }) => <div data-testid="pdf-page">PDF page {pageNumber}</div>
}));

vi.mock("framer-motion", () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    article: ({ children, ...props }: React.HTMLAttributes<HTMLElement>) => <article {...props}>{children}</article>,
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>
  }
}));

export { MockEventSource };
