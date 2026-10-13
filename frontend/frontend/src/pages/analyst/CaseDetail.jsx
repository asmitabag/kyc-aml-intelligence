import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import Tabs from '../../components/common/Tabs';
import DetailList from '../../components/common/DetailList';
import ErrorState from '../../components/common/ErrorState';
import Notice from '../../components/common/Notice';
import DataTable from '../../components/common/DataTable';
import RiskBadge from '../../components/common/RiskBadge';
import StatusBadge from '../../components/common/StatusBadge';
import SchemaForm from '../../components/forms/SchemaForm';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { caseService } from '../../services/caseService';
import { alertService } from '../../services/alertService';

const LINKS = {
  customer_id: (v) => `/analyst/customers/${encodeURIComponent(v)}`,
  alert_id: (v) => `/analyst/alerts/${encodeURIComponent(v)}`,
  assessment_id: (v) => `/analyst/assessments?assessment=${encodeURIComponent(v)}`,
};

export default function CaseDetail() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState('details');

  const detail = useAsync(() => caseService.get(caseId), [caseId]);
  // No "alerts by case" endpoint exists, so linked alerts are matched client-side.
  const alerts = useAsync(() => alertService.list(), []);
  const linked = (alerts.data || []).filter((a) => String(a.case_id) === String(caseId));

  if (detail.error) return <div className="panel"><ErrorState error={detail.error} onRetry={detail.reload} title="Couldn't load case" /></div>;

  const c = detail.data;
  const alertColumns = [
    { key: 'alert_id', header: 'Alert', render: (r) => <span className="font-mono text-xs">{r.alert_id}</span> },
    { key: 'alert_type', header: 'Type' },
    { key: 'severity', header: 'Severity', render: (r) => <RiskBadge level={r.severity} /> },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
  ];

  return (
    <>
      <PageHeader
        title={`Case ${caseId}`}
        description="Review the investigation, update its status and record your decision for model feedback."
        actions={
          <button type="button" className="btn-primary" onClick={() => navigate(`/analyst/sar?case=${encodeURIComponent(caseId)}`)}>
            <FileText className="h-4 w-4" aria-hidden="true" /> Open SAR workspace
          </button>
        }
      />

      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          { id: 'details', label: 'Details' },
          { id: 'alerts', label: 'Linked alerts', count: alerts.data ? linked.length : undefined },
          { id: 'status', label: 'Update status' },
          { id: 'feedback', label: 'Analyst feedback' },
        ]}
      />

      {tab === 'details' && (
        <Panel title="Investigation details">
          {detail.loading ? <PanelSkeleton lines={6} /> : <DetailList data={c} links={LINKS} />}
        </Panel>
      )}

      {tab === 'alerts' &&
        (alerts.error ? (
          <div className="panel"><ErrorState error={alerts.error} onRetry={alerts.reload} compact /></div>
        ) : (
          <DataTable
            columns={alertColumns}
            rows={linked}
            loading={alerts.loading}
            rowKey={(r) => r.alert_id}
            onRowClick={(r) => navigate(`/analyst/alerts/${encodeURIComponent(r.alert_id)}`)}
            empty={<p className="px-6 py-10 text-center text-sm text-slate-500">No alerts reference this case.</p>}
          />
        ))}

      {tab === 'status' && (
        <Panel title="Update case status" description="Allowed values come from the backend schema.">
          <SchemaForm
            specPath="/cases/{case_id}/status"
            method="patch"
            submitLabel="Update status"
            confirm={{ title: 'Update case status?', message: 'This changes the status of the case for everyone on the team.' }}
            onSubmit={(p) => caseService.updateStatus(caseId, p)}
            onSuccess={() => { toast.success('Case status updated.'); detail.reload(); setTab('details'); }}
          />
        </Panel>
      )}

      {tab === 'feedback' && (
        <Panel title="Analyst feedback" description="Your decision and rationale are stored for model evaluation.">
          <Notice className="mb-4">Feedback is added to the feedback dataset used to evaluate the models. Be specific about why you agree or disagree with the system's assessment.</Notice>
          <SchemaForm
            specPath="/cases/{case_id}/feedback"
            method="post"
            submitLabel="Submit feedback"
            onSubmit={(p) => caseService.submitFeedback(caseId, p)}
            onSuccess={() => toast.success('Feedback submitted.')}
          />
        </Panel>
      )}

      <p className="mt-6 text-sm text-slate-500">
        <Link to="/analyst/cases" className="text-indigo-600 hover:underline">← Back to cases</Link>
      </p>
    </>
  );
}
