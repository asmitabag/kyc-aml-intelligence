export default function JsonBlock({ data, summary = 'Raw response' }) {
  if (data === undefined || data === null) return null;
  return (
    <details className="group rounded-lg border border-slate-200 bg-slate-50">
      <summary className="cursor-pointer select-none px-3 py-2 text-xs font-medium text-slate-600">{summary}</summary>
      <pre className="max-h-80 overflow-auto border-t border-slate-200 p-3 font-mono text-xs text-slate-700">{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}
