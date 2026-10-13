import { useMemo, useState } from 'react';
import { ArrowDownLeft, ArrowUpRight, ReceiptText } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import EmptyState from '../../components/common/EmptyState';
import StatusBadge from '../../components/common/StatusBadge';
import SearchInput from '../../components/common/SearchInput';
import FilterBar, { FilterSelect } from '../../components/common/FilterBar';
import { useAsync } from '../../hooks/useAsync';
import { useOwnCustomer } from '../../hooks/useOwnCustomer';
import { customerService } from '../../services/customerService';
import { formatCurrency, formatDateTime, titleCase } from '../../utils/formatters';
import NotLinked from './NotLinked';

const isIn = (d) => /^(in|incoming|credit|deposit)/i.test(String(d ?? ''));

export default function Transactions() {
  const { customerId, linked } = useOwnCustomer();
  const { data, loading, error, reload } = useAsync(() => customerService.transactions(customerId), [customerId], { enabled: linked });
  const [q, setQ] = useState('');
  const [direction, setDirection] = useState('');
  const [status, setStatus] = useState('');

  const directions = useMemo(() => [...new Set((data || []).map((t) => t.direction).filter(Boolean))], [data]);
  const statuses = useMemo(() => [...new Set((data || []).map((t) => t.status).filter(Boolean))], [data]);

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (data || []).filter(
      (t) =>
        (!direction || t.direction === direction) &&
        (!status || t.status === status) &&
        (!needle || [t.transaction_id, t.counterparty, t.description].some((v) => String(v ?? '').toLowerCase().includes(needle))),
    );
  }, [data, q, direction, status]);

  if (!linked) return <NotLinked />;

  const columns = [
    { key: 'occurred_at', header: 'Date', render: (r) => <span className="whitespace-nowrap">{formatDateTime(r.occurred_at)}</span> },
    {
      key: 'direction',
      header: 'Direction',
      render: (r) => (
        <span className="inline-flex items-center gap-1.5">
          {isIn(r.direction) ? <ArrowDownLeft className="h-4 w-4 text-emerald-600" aria-hidden="true" /> : <ArrowUpRight className="h-4 w-4 text-slate-500" aria-hidden="true" />}
          {titleCase(r.direction)}
        </span>
      ),
    },
    { key: 'counterparty', header: 'Counterparty' },
    { key: 'description', header: 'Description', render: (r) => <span className="line-clamp-2 max-w-xs">{r.description || '—'}</span> },
    { key: 'amount', header: 'Amount', className: 'text-right', render: (r) => <span className="tnum font-medium">{formatCurrency(r.amount, r.currency)}</span> },
    { key: 'currency', header: 'Currency' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
  ];

  return (
    <>
      <PageHeader title="My transactions" description="Money in and out of your accounts." />
      <FilterBar
        active={!!(q || direction || status)}
        onReset={() => {
          setQ('');
          setDirection('');
          setStatus('');
        }}
      >
        <div className="w-full max-w-xs">
          <SearchInput value={q} onChange={setQ} placeholder="Search counterparty or description" label="Search transactions" />
        </div>
        <FilterSelect label="Direction" value={direction} onChange={setDirection} options={directions} />
        <FilterSelect label="Status" value={status} onChange={setStatus} options={statuses} />
      </FilterBar>
      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        error={error}
        onRetry={reload}
        rowKey={(r) => r.transaction_id}
        caption="My transactions"
        empty={<EmptyState icon={ReceiptText} title="No transactions found" description={q || direction || status ? 'Try clearing your filters.' : 'Activity on your accounts will appear here.'} />}
      />
    </>
  );
}
