import { useAsync } from '../../hooks/useAsync';
import { healthService } from '../../services/healthService';
import { toneForStatus } from '../common/StatusBadge';

const DOT = { green: 'bg-emerald-500', amber: 'bg-amber-500', red: 'bg-red-500', blue: 'bg-indigo-500', slate: 'bg-slate-400' };

export default function HealthPill() {
  const { data, error, loading } = useAsync(() => healthService.api(), []);
  const status = error ? 'unreachable' : data?.status ?? (loading ? 'checking' : 'unknown');
  const tone = error ? 'red' : loading ? 'slate' : toneForStatus(status);
  return (
    <span
      className="hidden items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600 sm:inline-flex"
      title={error ? error.message : 'GET /api/v1/health'}
    >
      <span className={`h-2 w-2 rounded-full ${DOT[tone]}`} aria-hidden="true" />
      API: {String(status)}
    </span>
  );
}
