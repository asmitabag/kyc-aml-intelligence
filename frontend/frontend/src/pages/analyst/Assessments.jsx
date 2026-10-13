import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Gauge, Plus, Search } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import DataTable from '../../components/common/DataTable';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import RiskBadge from '../../components/common/RiskBadge';
import StatusBadge from '../../components/common/StatusBadge';
import Modal from '../../components/common/Modal';
import AssessmentView from '../../components/common/AssessmentView';
import CustomerPicker from '../../components/forms/CustomerPicker';
import SchemaForm from '../../components/forms/SchemaForm';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { customerService } from '../../services/customerService';
import { analystService } from '../../services/analystService';
import { formatScore } from '../../utils/formatters';

export default function Assessments() {
  const [params, setParams] = useSearchParams();
  const [customerId, setCustomerId] = useState(params.get('customer') || '');
  const [lookupId, setLookupId] = useState(params.get('assessment') || '');
  const [activeId, setActiveId] = useState(params.get('assessment') || '');
  const [creating, setCreating] = useState(false);

  const list = useAsync(() => customerService.assessments(customerId), [customerId], { enabled: !!customerId });
  const single = useAsync(() => analystService.getAssessment(activeId), [activeId], { enabled: !!activeId });

  // Keep the URL shareable.
  useEffect(() => {
    const next = {};
    if (customerId) next.customer = customerId;
    if (activeId) next.assessment = activeId;
    setParams(next, { replace: true });
  }, [customerId, activeId, setParams]);

  const rows = list.data || [];
  const selected = single.data || null;

  const columns = [
    { key: 'assessment_id', header: 'Assessment', render: (r) => <span className="font-mono text-xs">{r.assessment_id}</span> },
    { key: 'risk_level', header: 'Level', render: (r) => <RiskBadge level={r.risk_level} /> },
    { key: 'final_risk', header: 'Final risk', render: (r) => <span className="tnum">{formatScore(r.final_risk)}</span> },
    { key: 'fused_risk', header: 'Fused', render: (r) => <span className="tnum">{formatScore(r.fused_risk)}</span> },
    { key: 'priority', header: 'Priority' },
    { key: 'suspected_typology', header: 'Typology' },
    { key: 'human_review_required', header: 'Human review', render: (r) => (r.human_review_required ? <StatusBadge value="required" tone="amber" /> : <span className="text-slate-400">No</span>) },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
  ];

  return (
    <>
      <PageHeader
        title="Risk assessments"
        description="KYC, AML, fused and final risk with model versions, uncertainty and top factors."
        actions={
          <button type="button" className="btn-secondary" onClick={() => setCreating(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" /> New assessment
          </button>
        }
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <div className="panel p-4">
          <CustomerPicker value={customerId} onChange={setCustomerId} label="Browse by customer" id="assess-customer" />
        </div>
        <form
          className="panel p-4"
          onSubmit={(e) => {
            e.preventDefault();
            setActiveId(lookupId.trim());
          }}
        >
          <label htmlFor="assess-id" className="label">Look up by assessment ID</label>
          <div className="flex gap-2">
            <input id="assess-id" className="input" value={lookupId} onChange={(e) => setLookupId(e.target.value)} placeholder="Assessment ID" autoComplete="off" />
            <button type="submit" className="btn-primary" disabled={!lookupId.trim()}>
              <Search className="h-4 w-4" aria-hidden="true" /> Open
            </button>
          </div>
        </form>
      </div>

      {customerId && (
        <div className="mb-6">
          <DataTable
            columns={columns}
            rows={rows}
            loading={list.loading}
            error={list.error}
            onRetry={list.reload}
            rowKey={(r) => r.assessment_id}
            onRowClick={(r) => { setActiveId(r.assessment_id); setLookupId(r.assessment_id); }}
            caption="Assessments for the selected customer"
            empty={<EmptyState icon={Gauge} title="No assessments for this customer" description="Run an AML analysis to produce one." />}
          />
        </div>
      )}

      {!customerId && !activeId && (
        <div className="panel">
          <EmptyState icon={Gauge} title="Choose a customer or enter an assessment ID" description="There is no global assessments list in the API, so assessments are browsed per customer." />
        </div>
      )}

      {activeId && (
        <Panel title={`Assessment ${activeId}`}>
          {single.loading ? <PanelSkeleton lines={6} /> : single.error ? <ErrorState error={single.error} onRetry={single.reload} compact /> : <AssessmentView a={selected} />}
        </Panel>
      )}

      <Modal open={creating} onClose={() => setCreating(false)} title="New assessment" size="lg">
        <SchemaForm
          specPath="/api/v1/assessments"
          method="post"
          initialValues={customerId ? { customer_id: customerId } : undefined}
          submitLabel="Create assessment"
          onSubmit={(p) => analystService.createAssessment(p)}
          onSuccess={(res) => {
            toast.success('Assessment created.');
            setCreating(false);
            if (res?.assessment_id) { setActiveId(res.assessment_id); setLookupId(res.assessment_id); }
            if (customerId) list.reload();
          }}
          onCancel={() => setCreating(false)}
        />
      </Modal>
    </>
  );
}
