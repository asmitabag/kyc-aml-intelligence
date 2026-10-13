import { api, unwrap } from '../api/client';
import { enc, unwrapList } from '../utils/formatters';

export const alertService = {
  list: () => unwrap(api.get('/api/v1/alerts')).then(unwrapList),
  get: (alertId) => unwrap(api.get(`/api/v1/alerts/${enc(alertId)}`)),
  create: (payload) => unwrap(api.post('/api/v1/alerts', payload)),
  update: (alertId, payload) => unwrap(api.patch(`/api/v1/alerts/${enc(alertId)}`, payload)),
  updateStatus: (alertId, payload) => unwrap(api.patch(`/api/v1/alerts/${enc(alertId)}/status`, payload)),
  submitFeedback: (alertId, payload) => unwrap(api.post(`/api/v1/alerts/${enc(alertId)}/feedback`, payload)),
};
