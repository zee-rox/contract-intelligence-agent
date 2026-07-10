import type { ClauseAnalysisResult, DocumentIngestionResponse, QAResponse } from "@/types/api";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function parseJson<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      payload?.error?.message ?? payload?.detail?.message ?? payload?.detail ?? "Backend request failed";
    throw new Error(typeof message === "string" ? message : "Backend request failed");
  }
  return payload as T;
}

export async function uploadDocument(file: File): Promise<DocumentIngestionResponse> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: "POST",
    body: form
  });
  return parseJson<DocumentIngestionResponse>(response);
}

export async function fetchClauseAnalysis(documentId: string): Promise<ClauseAnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/clauses`);
  return parseJson<ClauseAnalysisResult>(response);
}

export async function askQuestion(documentId: string, question: string): Promise<QAResponse> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });
  return parseJson<QAResponse>(response);
}

export function questionStreamUrl(documentId: string, question: string) {
  const url = new URL(`${API_BASE_URL}/documents/${documentId}/questions/stream`);
  url.searchParams.set("question", question);
  return url.toString();
}
