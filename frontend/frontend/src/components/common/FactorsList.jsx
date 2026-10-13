import { formatScore, isNil } from '../../utils/formatters';

// top_risk_factors can arrive as strings or objects; both are rendered as supplied.
export default function FactorsList({ factors }) {
  if (isNil(factors) || (Array.isArray(factors) && !factors.length)) {
    return <span className="text-slate-400">None supplied</span>;
  }
  const list = Array.isArray(factors) ? factors : typeof factors === 'object' ? Object.entries(factors).map(([k, v]) => ({ name: k, value: v })) : [factors];
  return (
    <ul className="space-y-1.5">
      {list.map((f, i) => {
        if (typeof f !== 'object' || f === null) {
          return (
            <li key={i} className="rounded-md bg-slate-50 px-2.5 py-1.5 text-sm text-slate-700">
              {String(f)}
            </li>
          );
        }
        const label = f.feature ?? f.name ?? f.factor ?? f.reason ?? f.label ?? null;
        const num = f.value ?? f.importance ?? f.weight ?? f.contribution ?? f.score ?? null;
        return (
          <li key={i} className="flex items-start justify-between gap-3 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm text-slate-700">
            <span className="min-w-0 break-words">{label !== null ? String(label) : JSON.stringify(f)}</span>
            {num !== null && typeof num !== 'object' && <span className="tnum shrink-0 font-medium text-slate-900">{typeof num === 'number' ? formatScore(num) : String(num)}</span>}
          </li>
        );
      })}
    </ul>
  );
}
