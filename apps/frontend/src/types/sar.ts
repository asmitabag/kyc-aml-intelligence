export interface SARResponse {
  case_id: string;
  sar_draft: string;
  evidence_ids_used: string[];
  validation_status: string;
  unsupported_claims: string[];
}

export type SARFiveWOneH = {
  who: string;
  what: string;
  when: string;
  where: string;
  why: string;
  how: string;
};
