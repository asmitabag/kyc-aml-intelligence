// Single place that knows where the bearer token lives.
//
// Trade-off (see README "Token storage"): any browser-readable storage can be
// read by injected JavaScript (XSS). sessionStorage is used instead of
// localStorage so the token is scoped to one tab and disappears when the tab
// closes. The safest architecture is an HttpOnly, Secure, SameSite cookie set by
// the backend; that needs a backend change, so it is not assumed here.
const KEY = 'kyc_aml_access_token';

export const tokenStore = {
  get() {
    try {
      return sessionStorage.getItem(KEY);
    } catch {
      return null;
    }
  },
  set(token) {
    try {
      sessionStorage.setItem(KEY, token);
    } catch {
      /* storage unavailable */
    }
  },
  clear() {
    try {
      sessionStorage.removeItem(KEY);
    } catch {
      /* storage unavailable */
    }
  },
};
