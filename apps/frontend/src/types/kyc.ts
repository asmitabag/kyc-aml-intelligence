export interface KYCResponse {
  customer_id: string;
  document_tamper_probability: number;
  liveness_probability: number;
  deepfake_probability: number;
  kyc_risk: number;
  document_fingerprint: string;
  tamper_mask_path: string | null;
  evidence_ids: string[];
}
