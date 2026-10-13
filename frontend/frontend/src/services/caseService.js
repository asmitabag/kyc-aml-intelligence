import { api, unwrap } from '../api/client';
import { enc, unwrapList } from '../utils/formatters';

// NOTE: these case routes are NOT under /api/v1 in the backend.
export const caseService = {
  // Creation may not be protected by require_analyst yet — see README.
  // It is intentionally not exposed in the UI until the backend confirms it.
  list: () => unwrap(api.get('/cases')).then(unwrapList),
  get: (caseId) => unwrap(api.get(`/cases/${enc(caseId)}`)),
  updateStatus: (caseId, payload) => unwrap(api.patch(`/cases/${enc(caseId)}/status`, payload)),
  submitFeedback: (caseId, payload) => unwrap(api.post(`/cases/${enc(caseId)}/feedback`, payload)),
  feedbackDataset: () => unwrap(api.get('/cases/feedback/dataset')).then(unwrapList),
  generateSarPreview: (caseId) => unwrap(api.post(`/cases/${enc(caseId)}/sar`)),
};
