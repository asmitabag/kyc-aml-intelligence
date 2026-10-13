import { api, unwrap } from '../api/client';
import { enc, unwrapList } from '../utils/formatters';

// Analyst-only: global directory, creation, imports, AML analysis, scoring.
export const analystService = {
  listCustomers: () => unwrap(api.get('/api/v1/customers')).then(unwrapList),
  createCustomer: (payload) => unwrap(api.post('/api/v1/customers', payload)),

  createAccountForCustomer: (customerId, payload) =>
    unwrap(api.post(`/api/v1/customers/${enc(customerId)}/accounts`, payload)),
  createAccount: (payload) => unwrap(api.post('/api/v1/accounts', payload)),

  listAccountTransactions: (accountId) =>
    unwrap(api.get(`/api/v1/accounts/${enc(accountId)}/transactions`)).then(unwrapList),
  createTransaction: (accountId, payload) =>
    unwrap(api.post(`/api/v1/accounts/${enc(accountId)}/transactions`, payload)),
  importTransactions: (payload) => unwrap(api.post('/api/v1/transactions/import', payload)),

  createAssessment: (payload) => unwrap(api.post('/api/v1/assessments', payload)),
  getAssessment: (assessmentId) => unwrap(api.get(`/api/v1/assessments/${enc(assessmentId)}`)),

  runAmlAnalysis: (customerId, payload) =>
    unwrap(api.post(`/api/v1/customers/${enc(customerId)}/aml-analysis`, payload)),
  scoreTransaction: (payload) => unwrap(api.post('/api/v1/aml/score-transaction', payload)),

  listFeedback: () => unwrap(api.get('/api/v1/feedback')).then(unwrapList),
  feedbackDataset: () => unwrap(api.get('/api/v1/feedback/dataset')).then(unwrapList),
};
