import { Link } from 'react-router-dom';
import StatusBadge from './StatusBadge';
import RiskBadge from './RiskBadge';
import { formatBool, formatDateTime, formatScore, isNil, titleCase } from '../../utils/formatters';

const STATUS_KEYS = /(^|_)status$/;
const RISK_KEYS = /^(risk_level|severity|priority)$/;
const SCORE_KEYS = /(risk|probability|uncertainty|score)$/;
const DATE_KEYS = /(_at|_date)$|^(date|timestamp)$/;

// Renders any API value sensibly, keyed by field name.
export default function Value({ name = '', value, links }) {
  if (isNil(value)) return <span className="text-slate-400">—</span>;

  if (typeof value === 'boolean') return <>{formatBool(value)}</>;
  if (STATUS_KEYS.test(name) && typeof value === 'string') return <StatusBadge value={value} />;
  if (RISK_KEYS.test(name) && typeof value === 'string') return <RiskBadge level={value} />;
  if (DATE_KEYS.test(name)) return <>{formatDateTime(value)}</>;
  if (typeof value === 'number' && SCORE_KEYS.test(name)) return <span className="tnum">{formatScore(value)}</span>;

  if (Array.isArray(value)) {
    if (value.every((v) => typeof v !== 'object' || v === null)) {
      return value.length ? (
        <span className="flex flex-wrap gap-1">
          {value.map((v, i) => (
            <span key={i} className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-700">
              {String(v)}
            </span>
          ))}
        </span>
      ) : (
        <span className="text-slate-400">None</span>
      );
    }
    return <pre className="max-h-48 overflow-auto rounded bg-slate-50 p-2 text-xs">{JSON.stringify(value, null, 2)}</pre>;
  }

  if (typeof value === 'object') {
    return <pre className="max-h-48 overflow-auto rounded bg-slate-50 p-2 text-xs">{JSON.stringify(value, null, 2)}</pre>;
  }

  if (links && links[name]) {
    return (
      <Link to={links[name](value)} className="font-mono text-xs text-indigo-600 hover:underline">
        {String(value)}
      </Link>
    );
  }
  if (typeof value === 'number') return <span className="tnum">{value}</span>;
  return <>{String(value)}</>;
}

export { titleCase };
