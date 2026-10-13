import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Plus } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import EmptyState from '../../components/common/EmptyState';
import StatusBadge from '../../components/common/StatusBadge';
import RiskBadge from '../../components/common/RiskBadge';
import SearchInput from '../../components/common/SearchInput';
import FilterBar, { FilterSelect } from '../../components/common/FilterBar';
import Modal from '../../components/common/Modal';
import SchemaForm from '../../components/forms/SchemaForm';
import { useAsync } from '../../hooks/useAsync';
import { alertService } from '../../services/alertService';
import { titleCase } from '../../utils/formatters';

const uniq = (list, key) => [...new Set(list.map((x) => x[key]).filter(Boolean))];

export default function Alerts() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(() => alertService.list(), []);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [severity, setSeverity] = useState('');
  const [type, setType] = useState('');
  const [creating, setCreating] = useState(false);

  const list = data || [];
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return list.filter(
      (a) =>
        (!status || a.status === status) &&
        (!severity || a.severity === severity) &&
        (!type || a.alert_type === type) &&
        (!needle || [a.alert_id, a.customer_id, a.account_id, a.case_id, a.reason_code, a.narrative].some((v) => String(v ?? '').toLowerCase().includes(needle))),
    );
  }, [list, q, status, severity, type]);

  const columns = [
    { key: 'alert_id', header: 'Alert', render: (r) => <span className="font-mono text-xs">{r.alert_id}</span> },
    { key: 'customer_id', header: 'Customer', render: (r) => <span className="font-mono text-xs">{r.customer_id}</span> },
    { key: 'alert_type', header: 'Type', render: (r) => titleCase(r.alert_type) },
    { key: 'reason_code', header: 'Reason', render: (r) => <span className="font-mono text-xs">{r.reason_code || '—'}</span> },
    { key: 'severity', header: 'Severity', render: (r) => <RiskBadge level={r.severity} /> },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
    { key: 'case_id', header: 'Case', render: (r) => <span className="font-mono text-xs">{r.case_id || '—'}</span> },
    { key: 'narrative', header: 'Narrative', sortable: false, render: (r) => <span className="line-clamp-2 max-w-xs text-slate-600">{r.narrative || '—'}</span> },
  ];

  return (
    <>
      <PageHeader
        title="Alerts"
        description="Triage monitoring alerts. Open an alert to update its status, severity and narrative."
        actions={
          <button type="button" className="btn-primary" onClick={() => setCreating(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" /> New alert
          </button>
        }
      />

      <FilterBar active={!!(q || status || severity || type)} onReset={() => { setQ(''); setStatus(''); setSeverity(''); setType(''); }}>
        <div className="w-full max-w-xs">
          <SearchInput value={q} onChange={setQ} placeholder="Search ID, customer, reason, narrative" label="Search alerts" />
        </div>
        <FilterSelect label="Status" value={status} onChange={setStatus} options={uniq(list, 'status')} />
        <FilterSelect label="Severity" value={severity} onChange={setSeverity} options={uniq(list, 'severity')} />
        <FilterSelect label="Type" value={type} onChange={setType} options={uniq(list, 'alert_type')} />
      </FilterBar>

      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        error={error}
        onRetry={reload}
        rowKey={(r) => r.alert_id}
        onRowClick={(r) => navigate(`/analyst/alerts/${encodeURIComponent(r.alert_id)}`)}
        caption="Alerts"
        empty={<EmptyState icon={AlertTriangle} title="No alerts" description={list.length ? 'Adjust or clear your filters.' : 'No alerts have been raised.'} />}
      />

      <Modal open={creating} onClose={() => setCreating(false)} title="New alert" size="lg">
        <SchemaForm
          specPath="/api/v1/alerts"
          method="post"
          submitLabel="Create alert"
          onSubmit={(p) => alertService.create(p)}
          onSuccess={() => { toast.success('Alert created.'); setCreating(false); reload(); }}
          onCancel={() => setCreating(false)}
        />
      </Modal>
    </>
  );
}
