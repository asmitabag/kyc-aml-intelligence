import { titleCase } from '../../utils/formatters';

const TONES = {
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  amber: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  red: 'bg-red-50 text-red-700 ring-red-600/20',
  blue: 'bg-indigo-50 text-indigo-700 ring-indigo-600/20',
  slate: 'bg-slate-100 text-slate-600 ring-slate-500/20',
};

const DOT = { green: 'bg-emerald-500', amber: 'bg-amber-500', red: 'bg-red-500', blue: 'bg-indigo-500', slate: 'bg-slate-400' };

// Colours a status string by keyword. The label always shows the real value.
export function toneForStatus(value) {
  const v = String(value ?? '').toLowerCase();
  if (!v) return 'slate';
  if (/^(verified|approved|active|completed|complete|closed|resolved|cleared|success|succeeded|passed|accepted|available|ok|healthy|ready|reviewed)$/.test(v)) return 'green';
  if (/(reject|fail|block|unavailable|error|frozen|suspend|denied|declined|degraded)/.test(v)) return 'red';
  if (/(fallback|pending|review|open|draft|submitted|progress|new|investigat|escalat|incomplete|not_started|unverified)/.test(v)) return 'amber';
  return 'blue';
}

export default function StatusBadge({ value, tone }) {
  const t = tone || toneForStatus(value);
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[t]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${DOT[t]}`} aria-hidden="true" />
      {titleCase(value)}
    </span>
  );
}
