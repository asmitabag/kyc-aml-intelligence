export const isNil = (v) => v === null || v === undefined || v === '';

export function titleCase(value) {
  if (isNil(value)) return '—';
  const s = String(value).replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function formatDate(value) {
  if (isNil(value)) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export function formatDateTime(value) {
  if (isNil(value)) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Never assumes a currency: if the API gave none, only the number is formatted.
export function formatCurrency(amount, currency) {
  if (isNil(amount)) return '—';
  const n = Number(amount);
  if (Number.isNaN(n)) return String(amount);
  if (!currency) return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(n);
  } catch {
    return `${n.toLocaleString(undefined, { minimumFractionDigits: 2 })} ${currency}`;
  }
}

export function formatNumber(value) {
  if (isNil(value)) return '—';
  const n = Number(value);
  return Number.isNaN(n) ? String(value) : n.toLocaleString();
}

// Risk scores are shown exactly as supplied (rounded for readability only).
export function formatScore(value) {
  if (isNil(value)) return '—';
  const n = Number(value);
  return Number.isNaN(n) ? String(value) : n.toFixed(3);
}

export function formatBool(value) {
  if (value === null || value === undefined) return '—';
  return value ? 'Yes' : 'No';
}

// FastAPI list endpoints may return a bare array or an envelope.
export function unwrapList(data) {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    for (const key of ['items', 'results', 'data', 'records', 'customers', 'alerts', 'cases', 'accounts', 'transactions', 'assessments', 'feedback', 'sar_drafts']) {
      if (Array.isArray(data[key])) return data[key];
    }
  }
  return [];
}

export function sumByCurrency(accounts) {
  const totals = {};
  for (const a of accounts) {
    const n = Number(a.balance);
    if (Number.isNaN(n)) continue;
    const c = a.currency || '—';
    totals[c] = (totals[c] || 0) + n;
  }
  return totals;
}

export function pickLatest(list) {
  if (!list.length) return null;
  const dated = list.filter((x) => x.created_at || x.updated_at);
  if (dated.length === list.length) {
    return [...list].sort(
      (a, b) => new Date(b.created_at || b.updated_at) - new Date(a.created_at || a.updated_at),
    )[0];
  }
  return list[list.length - 1];
}

export function countBy(list, key) {
  const out = {};
  for (const item of list) {
    const k = isNil(item?.[key]) ? 'unspecified' : String(item[key]);
    out[k] = (out[k] || 0) + 1;
  }
  return Object.entries(out).map(([name, value]) => ({ name, value }));
}

export const enc = (v) => encodeURIComponent(v);
