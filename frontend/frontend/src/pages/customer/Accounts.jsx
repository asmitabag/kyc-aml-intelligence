import { useMemo, useState } from 'react';
import { CreditCard } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import EmptyState from '../../components/common/EmptyState';
import StatusBadge from '../../components/common/StatusBadge';
import SearchInput from '../../components/common/SearchInput';
import FilterBar from '../../components/common/FilterBar';
import { useAsync } from '../../hooks/useAsync';
import { useOwnCustomer } from '../../hooks/useOwnCustomer';
import { customerService } from '../../services/customerService';
import { formatCurrency, titleCase } from '../../utils/formatters';
import NotLinked from './NotLinked';

export default function Accounts() {
  const { customerId, linked } = useOwnCustomer();
  const { data, loading, error, reload } = useAsync(() => customerService.accounts(customerId), [customerId], { enabled: linked });
  const [q, setQ] = useState('');

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (data || []).filter((a) => !needle || [a.account_id, a.account_type].some((v) => String(v ?? '').toLowerCase().includes(needle)));
  }, [data, q]);

  if (!linked) return <NotLinked />;

  const columns = [
    { key: 'account_id', header: 'Account', render: (r) => <span className="font-mono text-xs">{r.account_id}</span> },
    { key: 'account_type', header: 'Type', render: (r) => titleCase(r.account_type) },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
    { key: 'balance', header: 'Balance', className: 'text-right', render: (r) => <span className="tnum font-medium">{formatCurrency(r.balance, r.currency)}</span> },
    { key: 'currency', header: 'Currency' },
  ];

  return (
    <>
      <PageHeader title="My accounts" description="Accounts held under your profile." />
      <FilterBar>
        <div className="w-full max-w-xs">
          <SearchInput value={q} onChange={setQ} placeholder="Search by ID or type" label="Search accounts" />
        </div>
      </FilterBar>
      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        error={error}
        onRetry={reload}
        rowKey={(r) => r.account_id}
        caption="My accounts"
        empty={<EmptyState icon={CreditCard} title="No accounts yet" description="Accounts opened for you will show up here." />}
      />
    </>
  );
}
