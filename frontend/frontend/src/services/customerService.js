import { api, unwrap } from '../api/client';
import { enc, unwrapList } from '../utils/formatters';

// Customer-scoped reads. The customer portal calls these with the
// authenticated user's own customer_id ONLY. The backend must still enforce
// ownership (see README).
export const customerService = {
  get: (customerId) => unwrap(api.get(`/api/v1/customers/${enc(customerId)}`)),

  // 404 means "no KYC submitted yet", which is a normal state, not an error.
  latestKyc: async (customerId) => {
    try {
      return await unwrap(api.get(`/api/v1/customers/${enc(customerId)}/kyc/latest`));
    } catch (e) {
      if (e.status === 404) return null;
      throw e;
    }
  },
  submitKyc: (customerId, payload) => unwrap(api.post(`/api/v1/customers/${enc(customerId)}/kyc`, payload)),

  accounts: (customerId) => unwrap(api.get(`/api/v1/customers/${enc(customerId)}/accounts`)).then(unwrapList),
  transactions: (customerId) => unwrap(api.get(`/api/v1/customers/${enc(customerId)}/transactions`)).then(unwrapList),
  assessments: (customerId) => unwrap(api.get(`/api/v1/customers/${enc(customerId)}/assessments`)).then(unwrapList),
};
