import type { CaseRecord, CaseStatus, FeedbackPayload } from "../types/case";
import type { KYCResponse } from "../types/kyc";

const API_URL = import.meta.env.VITE_API_URL ?? "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });

  if (!response.ok) {
    const error = new Error(
      response.status === 404
        ? "Case not found"
        : "The backend could not complete this request.",
    );
    (error as Error & { status?: number }).status = response.status;
    throw error;
  }

  return response.json() as Promise<T>;
}

export function getCases(): Promise<CaseRecord[]> {
  return request<CaseRecord[]>("/cases");
}

export function createCase(kycData: KYCResponse): Promise<CaseRecord> {
  return request<CaseRecord>("/cases", {
    method: "POST",
    body: JSON.stringify(kycData),
  });
}

export function getCase(caseId: string): Promise<CaseRecord> {
  return request<CaseRecord>(`/cases/${encodeURIComponent(caseId)}`);
}

export function updateCaseStatus(
  caseId: string,
  status: CaseStatus,
): Promise<CaseRecord> {
  return request<CaseRecord>(`/cases/${encodeURIComponent(caseId)}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function submitCaseFeedback(
  caseId: string,
  feedback: FeedbackPayload,
): Promise<CaseRecord> {
  return request<CaseRecord>(`/cases/${encodeURIComponent(caseId)}/feedback`, {
    method: "POST",
    body: JSON.stringify(feedback),
  });
}
