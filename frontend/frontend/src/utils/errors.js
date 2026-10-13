const DEFAULT_MESSAGES = {
  400: 'The request was invalid.',
  401: 'Your session is missing or has expired. Please sign in again.',
  403: "You don't have permission to perform this action.",
  404: 'The requested resource was not found.',
  409: 'This record already exists (duplicate).',
  422: 'Some of the submitted values are invalid.',
  500: 'The server hit an error. Try again, and contact support if it keeps happening.',
  503: 'A required model or service is currently unavailable.',
};

export class ApiError extends Error {
  constructor({ status = 0, message, detail = null, fieldErrors = {}, isNetwork = false }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.fieldErrors = fieldErrors;
    this.isNetwork = isNetwork;
  }
}

function parseDetail(detail) {
  const fieldErrors = {};
  let message = null;

  if (typeof detail === 'string') {
    message = detail;
  } else if (Array.isArray(detail)) {
    const parts = [];
    for (const item of detail) {
      if (item && typeof item === 'object') {
        const loc = Array.isArray(item.loc) ? item.loc.filter((p) => p !== 'body' && p !== 'query' && p !== 'path') : [];
        const field = loc.length ? String(loc[loc.length - 1]) : null;
        const msg = item.msg || item.message || JSON.stringify(item);
        if (field) {
          fieldErrors[field] = msg;
          parts.push(`${field}: ${msg}`);
        } else {
          parts.push(msg);
        }
      } else {
        parts.push(String(item));
      }
    }
    message = parts.join('; ');
  } else if (detail && typeof detail === 'object') {
    message = detail.message || detail.detail || detail.error || JSON.stringify(detail);
  }
  return { message, fieldErrors };
}

export function normalizeError(err) {
  if (err instanceof ApiError) return err;

  if (err?.response) {
    const { status, data } = err.response;
    const raw = data && typeof data === 'object' && 'detail' in data ? data.detail : data;
    const { message, fieldErrors } = parseDetail(raw);
    return new ApiError({
      status,
      message: message || DEFAULT_MESSAGES[status] || `Request failed with status ${status}.`,
      detail: raw,
      fieldErrors,
    });
  }

  if (err?.request || err?.code === 'ERR_NETWORK' || err?.code === 'ECONNABORTED') {
    return new ApiError({
      status: 0,
      isNetwork: true,
      message:
        err.code === 'ECONNABORTED'
          ? 'The request timed out. The backend may be starting up — try again.'
          : 'Cannot reach the API. Check VITE_API_BASE_URL, that the backend is running, and that its CORS allowlist includes this origin.',
    });
  }

  return new ApiError({ status: 0, message: err?.message || 'Unexpected error.' });
}

export const isStatus = (err, ...codes) => codes.includes(err?.status);
