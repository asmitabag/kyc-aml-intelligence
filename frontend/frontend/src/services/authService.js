import { api, unwrap } from '../api/client';

export const authService = {
  // skipAuthRedirect: a 401 here means "wrong credentials", not "expired session".
  login: (payload) => unwrap(api.post('/api/v1/auth/login', payload, { skipAuthRedirect: true })),
  register: (payload) => unwrap(api.post('/api/v1/auth/register', payload, { skipAuthRedirect: true })),
  me: () => unwrap(api.get('/api/v1/auth/me')),
};
