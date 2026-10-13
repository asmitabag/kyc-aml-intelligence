import { Link } from 'react-router-dom';
import Skeleton from './Skeleton';

const TONES = {
  indigo: 'bg-indigo-50 text-indigo-600',
  red: 'bg-red-50 text-red-600',
  amber: 'bg-amber-50 text-amber-600',
  green: 'bg-emerald-50 text-emerald-600',
  slate: 'bg-slate-100 text-slate-600',
};

export default function StatCard({ label, value, hint, icon: Icon, tone = 'indigo', loading, to, error }) {
  const body = (
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <p className="text-sm text-slate-500">{label}</p>
        {loading ? (
          <Skeleton className="mt-2 h-7 w-20" />
        ) : error ? (
          <p className="mt-1 text-sm font-medium text-red-600" title={error.message}>
            Unavailable
          </p>
        ) : (
          <p className="tnum mt-1 truncate text-2xl font-semibold text-ink">{value}</p>
        )}
        {hint && !loading && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
      </div>
      {Icon && (
        <div className={`shrink-0 rounded-lg p-2 ${TONES[tone]}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      )}
    </div>
  );
  const cls = 'panel block p-4';
  return to ? (
    <Link to={to} className={`${cls} transition-shadow hover:shadow-md`}>
      {body}
    </Link>
  ) : (
    <div className={cls}>{body}</div>
  );
}
