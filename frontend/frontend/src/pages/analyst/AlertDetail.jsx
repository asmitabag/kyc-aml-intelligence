import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import Tabs from '../../components/common/Tabs';
import DetailList from '../../components/common/DetailList';
import ErrorState from '../../components/common/ErrorState';
import RiskBadge from '../../components/common/RiskBadge';
import StatusBadge from '../../components/common/StatusBadge';
import SchemaForm from '../../components/forms/SchemaForm';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { alertService } from '../../services/alertService';

const LINKS = {
  customer_id: (v) => `/analyst/customers/${encodeURIComponent(v)}`,
  case_id: (v) => `/analyst/cases/${encodeURIComponent(v)}`,
  assessment_id: (v) => `/analyst/assessments?assessment=${encodeURIComponent(v)}`,
};

export default function AlertDetail() {
  const { alertId } = useParams();
  const [tab, setTab] = useState('details');
  const { data: a, loading, error, reload } = useAsync(() => alertService.get(alertId), [alertId]);

  if (error) return <div className="panel"><ErrorState error={error} onRetry={reload} title="Couldn't load alert" /></div>;

  return (
    <>
      <PageHeader
        title={`Alert ${alertId}`}
        description={a?.reason_code ? `Reason code ${a.reason_code}` : undefined}
        actions={a && <span className="flex items-center gap-2"><RiskBadge level={a.severity} /><StatusBadge value={a.status} /></span>}
      />

      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          { id: 'details', label: 'Details' },
          { id: 'update', label: 'Edit alert' },
          { id: 'status', label: 'Change status' },
          { id: 'feedback', label: 'Feedback' },
        ]}
      />

      {tab === 'details' && (
        <div className="space-y-6">
          <Panel title="Alert">
            {loading ? <PanelSkeleton lines={6} /> : <DetailList data={a} exclude={['narrative']} links={LINKS} />}
          </Panel>
          {a && (
            <Panel title="Narrative">
              {a.narrative ? <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">{a.narrative}</p> : <p className="text-sm text-slate-400">No narrative recorded.</p>}
            </Panel>
          )}
        </div>
      )}

      {tab === 'update' && (
        <Panel title="Edit alert" description="Update status, severity and narrative. Fields come from the backend schema.">
          <SchemaForm
            specPath="/api/v1/alerts/{alert_id}"
            method="patch"
            initialValues={a || undefined}
            submitLabel="Save changes"
            confirm={{ title: 'Save changes to this alert?', message: 'The updated values replace the current ones.' }}
            onSubmit={(p) => alertService.update(alertId, p)}
            onSuccess={() => { toast.success('Alert updated.'); reload(); setTab('details'); }}
          />
        </Panel>
      )}

      {tab === 'status' && (
        <Panel title="Change status" description="A quick status change without editing other fields.">
          <SchemaForm
            specPath="/api/v1/alerts/{alert_id}/status"
            method="patch"
            initialValues={a ? { status: a.status } : undefined}
            submitLabel="Update status"
            onSubmit={(p) => alertService.updateStatus(alertId, p)}
            onSuccess={() => { toast.success('Alert status updated.'); reload(); setTab('details'); }}
          />
        </Panel>
      )}

      {tab === 'feedback' && (
        <Panel title="Alert feedback" description="Tell the team whether this alert was useful. Stored for model evaluation.">
          <SchemaForm
            specPath="/api/v1/alerts/{alert_id}/feedback"
            method="post"
            submitLabel="Submit feedback"
            onSubmit={(p) => alertService.submitFeedback(alertId, p)}
            onSuccess={() => toast.success('Feedback submitted.')}
          />
        </Panel>
      )}

      <p className="mt-6 text-sm text-slate-500">
        <Link to="/analyst/alerts" className="text-indigo-600 hover:underline">← Back to alerts</Link>
      </p>
    </>
  );
}
