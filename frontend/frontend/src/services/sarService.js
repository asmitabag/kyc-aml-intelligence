import { api, unwrap } from '../api/client';
import { enc } from '../utils/formatters';

// Every result from these endpoints is a DRAFT pending human review.
export const sarService = {
  createFromCase: (caseId) => unwrap(api.post(`/api/v1/cases/${enc(caseId)}/sar`)),
  getForCase: (caseId) => unwrap(api.get(`/api/v1/cases/${enc(caseId)}/sar`)),
  createDraft: (payload) => unwrap(api.post('/api/v1/sar-drafts', payload)),
  getDraft: (sarId) => unwrap(api.get(`/api/v1/sar-drafts/${enc(sarId)}`)),
  updateStatus: (sarId, payload) => unwrap(api.patch(`/api/v1/sar-drafts/${enc(sarId)}/status`, payload)),
};
