import { titleCase } from '../../utils/formatters';

const TONES = {
  red: 'bg-red-50 text-red-700 ring-red-600/20',
  amber: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  slate: 'bg-slate-100 text-slate-600 ring-slate-500/20',
};

// Colours only by the LEVEL WORD supplied by the backend. Numeric scores are
// never bucketed into levels here because no thresholds are defined.
export function toneForRisk(level) {
  const v = String(level ?? '').toLowerCase();
  if (/(critical|severe|high)/.test(v)) return 'red';
  if (/(medium|moderate|elevated)/.test(v)) return 'amber';
  if (/(low|minimal|none)/.test(v)) return 'green';
  return 'slate';
}

export default function RiskBadge({ level }) {
  if (level === null || level === undefined || level === '') {
    return <span className="text-slate-400">—</span>;
  }
  return (
    <span className={`inline-flex items-center whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${TONES[toneForRisk(level)]}`}>
      {titleCase(level)}
    </span>
  );
}
