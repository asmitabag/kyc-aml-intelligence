import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUp, Plus, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import DataTable from '../../components/common/DataTable';
import EmptyState from '../../components/common/EmptyState';
import StatusBadge from '../../components/common/StatusBadge';
import SearchInput from '../../components/common/SearchInput';
import FilterBar, { FilterSelect } from '../../components/common/FilterBar';
import Modal from '../../components/common/Modal';
import SchemaForm from '../../components/forms/SchemaForm';
import ResultView from '../../components/common/ResultView';
import { useAsync } from '../../hooks/useAsync';
import { analystService } from '../../services/analystService';
import { formatDate, titleCase } from '../../utils/formatters';

const uniq = (list, key) => [...new Set(list.map((x) => x[key]).filter(Boolean))];

export default function Customers() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(() => analystService.listCustomers(), []);
  const [q, setQ] = useState('');
  const [kyc, setKyc] = useState('');
  const [onboarding, setOnboarding] = useState('');
  const [type, setType] = useState('');
  const [origin, setOrigin] = useState('');
  const [modal, setModal] = useState(null); // 'create' | 'import'
  const [importResult, setImportResult] = useState(null);

  const list = data || [];
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return list.filter(
      (c) =>
        (!kyc || c.kyc_status === kyc) &&
        (!onboarding || c.onboarding_status === onboarding) &&
        (!type || c.customer_type === type) &&
        (!origin || c.data_origin === origin) &&
        (!needle || [c.customer_id, c.full_name, c.email, c.phone].some((v) => String(v ?? '').toLowerCase().includes(needle))),
    );
  }, [list, q, kyc, onboarding, type, origin]);

  const columns = [
    { key: 'customer_id', header: 'Customer ID', render: (r) => <span className="font-mono text-xs">{r.customer_id}</span> },
    { key: 'full_name', header: 'Name', render: (r) => <span className="font-medium text-ink">{r.full_name}</span> },
    { key: 'email', header: 'Email' },
    { key: 'customer_type', header: 'Type', render: (r) => titleCase(r.customer_type) },
    { key: 'kyc_status', header: 'KYC', render: (r) => <StatusBadge value={r.kyc_status} /> },
    { key: 'onboarding_status', header: 'Onboarding', render: (r) => <StatusBadge value={r.onboarding_status} /> },
    { key: 'data_origin', header: 'Data origin', render: (r) => titleCase(r.data_origin) },
    { key: 'created_at', header: 'Created', render: (r) => formatDate(r.created_at) },
  ];

  return (
    <>
      <PageHeader
        title="Customers"
        description="Search the directory and open a customer to review KYC results, accounts, transactions and assessments."
        actions={
          <>
            <button type="button" className="btn-secondary" onClick={() => { setImportResult(null); setModal('import'); }}>
              <FileUp className="h-4 w-4" aria-hidden="true" /> Import transactions
            </button>
            <button type="button" className="btn-primary" onClick={() => setModal('create')}>
              <Plus className="h-4 w-4" aria-hidden="true" /> New customer
            </button>
          </>
        }
      />

      <FilterBar
        active={!!(q || kyc || onboarding || type || origin)}
        onReset={() => { setQ(''); setKyc(''); setOnboarding(''); setType(''); setOrigin(''); }}
      >
        <div className="w-full max-w-xs">
          <SearchInput value={q} onChange={setQ} placeholder="Search name, email, ID, phone" label="Search customers" />
        </div>
        <FilterSelect label="KYC status" value={kyc} onChange={setKyc} options={uniq(list, 'kyc_status')} />
        <FilterSelect label="Onboarding" value={onboarding} onChange={setOnboarding} options={uniq(list, 'onboarding_status')} />
        <FilterSelect label="Type" value={type} onChange={setType} options={uniq(list, 'customer_type')} />
        <FilterSelect label="Data origin" value={origin} onChange={setOrigin} options={uniq(list, 'data_origin')} />
      </FilterBar>

      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        error={error}
        onRetry={reload}
        rowKey={(r) => r.customer_id}
        onRowClick={(r) => navigate(`/analyst/customers/${encodeURIComponent(r.customer_id)}`)}
        caption="Customer directory"
        empty={<EmptyState icon={Users} title="No customers match" description={list.length ? 'Adjust or clear your filters.' : 'The directory is empty.'} />}
      />

      <Modal open={modal === 'create'} onClose={() => setModal(null)} title="New customer">
        <SchemaForm
          specPath="/api/v1/customers"
          method="post"
          submitLabel="Create customer"
          onSubmit={(p) => analystService.createCustomer(p)}
          onSuccess={() => { toast.success('Customer created.'); setModal(null); reload(); }}
          onCancel={() => setModal(null)}
        />
      </Modal>

      <Modal open={modal === 'import'} onClose={() => setModal(null)} title="Import transactions" size="lg">
        {importResult ? (
          <div className="space-y-4">
            <ResultView result={importResult} />
            <div className="flex justify-end"><button type="button" className="btn-primary" onClick={() => setModal(null)}>Done</button></div>
          </div>
        ) : (
          <SchemaForm
            specPath="/api/v1/transactions/import"
            method="post"
            submitLabel="Import"
            confirm={{ title: 'Import transactions?', message: 'This writes transaction records to the backend. It cannot be undone from this screen.' }}
            onSubmit={(p) => analystService.importTransactions(p)}
            onSuccess={(res) => { toast.success('Import request completed.'); setImportResult(res ?? { status: 'completed' }); }}
            onCancel={() => setModal(null)}
          />
        )}
      </Modal>
    </>
  );
}
