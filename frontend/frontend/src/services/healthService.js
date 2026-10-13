import { api, unwrap } from '../api/client';

export const healthService = {
  root: () => unwrap(api.get('/health', { skipAuthRedirect: true })),
  api: () => unwrap(api.get('/api/v1/health', { skipAuthRedirect: true })),
};
