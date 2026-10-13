import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardList } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import AutoTable from '../../components/common/AutoTable';
import EmptyState from '../../components/common/EmptyState';
import SearchInput from '../../components/common/SearchInput';
import FilterBar, { FilterSelect } from '../../components/common/FilterBar';
import Notice from '../../components/common/Notice';
import { useAsync } from '../../hooks/useAsync';
import { caseService } from '../../services/caseService';

export const caseIdOf = (c) => c?.case_id ?? c?.id;

export default function Cases() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(() => caseService.list(), []);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');

  const list = data || [];
  const statuses = useMemo(() => [...new Set(list.map((c) => c.status).filter(Boolean))], [list]);
  const priorities = useMemo(() => [...new Set(list.map((c) => c.priority).filter(Boolean))], [list]);
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return list.filter(
      (c) =>
        (!status || c.status === status) &&
        (!priority || c.priority === priority) &&
        (!needle || JSON.stringify(c).toLowerCase().includes(needle)),
    );
  }, [list, q, status, priority]);

  return (
    <>
      <PageHeader title="Cases" description="Investigations opened from alerts and risk assessments." />

      <Notice className="mb-4">
        Columns are built from the fields the API returns. Case creation is not offered here until the backend confirms it is analyst-protected.
      </Notice>

      <FilterBar active={!!(q || status || priority)} onReset={() => { setQ(''); setStatus(''); setPriority(''); }}>
        <div className="w-full max-w-xs">
          <SearchInput value={q} onChange={setQ} placeholder="Search cases" label="Search cases" />
        </div>
        {statuses.length > 0 && <FilterSelect label="Status" value={status} onChange={setStatus} options={statuses} />}
        {priorities.length > 0 && <FilterSelect label="Priority" value={priority} onChange={setPriority} options={priorities} />}
      </FilterBar>

      <AutoTable
        rows={rows}
        preferred={['case_id', 'customer_id', 'status', 'priority', 'created_at']}
        loading={loading}
        error={error}
        onRetry={reload}
        rowKey={caseIdOf}
        onRowClick={(r) => navigate(`/analyst/cases/${encodeURIComponent(caseIdOf(r))}`)}
        caption="Cases"
        empty={<EmptyState icon={ClipboardList} title="No cases" description={list.length ? 'Adjust or clear your filters.' : 'No cases have been opened.'} />}
      />
    </>
  );
}
