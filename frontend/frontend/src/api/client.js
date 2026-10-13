import axios from 'axios';
import { tokenStore } from '../auth/tokenStore';
import { normalizeError } from '../utils/errors';

// The ONLY place the backend URL is read.
const baseURL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

if (!baseURL) {
  // eslint-disable-next-line no-console
  console.error('VITE_API_BASE_URL is not set. Copy .env.example to .env and restart the dev server.');
}

export const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: { Accept: 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const UNAUTHORIZED_EVENT = 'auth:unauthorized';

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = normalizeError(error);
    // A 401 on a protected call means the token is missing/expired. Login
    // attempts opt out (skipAuthRedirect) so wrong passwords are shown inline.
    if (normalized.status === 401 && !error.config?.skipAuthRedirect) {
      window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
    }
    return Promise.reject(normalized);
  },
);

export const unwrap = (promise) => promise.then((r) => r.data);

export const API_BASE_URL = baseURL;
