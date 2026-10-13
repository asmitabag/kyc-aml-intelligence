import { Gauge } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import Notice from '../../components/common/Notice';
import RiskBadge from '../../components/common/RiskBadge';
import StatusBadge from '../../components/common/StatusBadge';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { useOwnCustomer } from '../../hooks/useOwnCustomer';
import { customerService } from '../../services/customerService';
import { formatDateTime, pickLatest } from '../../utils/formatters';
import NotLinked from './NotLinked';

// Customer-safe view: ONLY the level and status are shown. Model scores, typology,
// priority, top risk factors, case IDs, etc. are analyst data and are never rendered
// here, even if the API happens to return them (the backend should also omit them).
export default function RiskAssessment() {
  const { customerId, linked } = useOwnCustomer();
  const { data, loading, error, reload } = useAsync(() => customerService.assessments(customerId), [customerId], { enabled: linked });

  if (!linked) return <NotLinked />;

  const latest = pickLatest(data || []);
  const history = [...(data || [])].reverse();

  return (
    <>
      <PageHeader title="My risk assessment" description="A summary of the reviews carried out on your profile." />

      <Notice tone="info" className="mb-6">
        Reviews help us meet our legal obligations to keep accounts safe. Detailed review notes are only visible to our compliance team.
      </Notice>

      {loading ? (
        <div className="panel"><PanelSkeleton lines={4} /></div>
      ) : error ? (
        <div className="panel"><ErrorState error={error} onRetry={reload} /></div>
      ) : !latest ? (
        <div className="panel">
          <EmptyState icon={Gauge} title="No assessment yet" description="Once your information has been reviewed, the result will be shown here." />
        </div>
      ) : (
        <div className="space-y-6">
          <Panel title="Latest assessment">
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <p className="mb-1.5 text-sm text-slate-500">Risk level</p>
                <RiskBadge level={latest.risk_level} />
              </div>
              <div>
                <p className="mb-1.5 text-sm text-slate-500">Review status</p>
                <StatusBadge value={latest.status} />
              </div>
            </div>
          </Panel>

          {history.length > 1 && (
            <Panel title="History" padded={false}>
              <ul className="divide-y divide-slate-100">
                {history.map((a) => (
                  <li key={a.assessment_id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 text-sm">
                    <span className="font-mono text-xs text-slate-500">{a.assessment_id}</span>
                    <span className="flex items-center gap-3">
                      {(a.created_at || a.updated_at) && <span className="text-xs text-slate-500">{formatDateTime(a.created_at || a.updated_at)}</span>}
                      <RiskBadge level={a.risk_level} />
                      <StatusBadge value={a.status} />
                    </span>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>
      )}
    </>
  );
}
