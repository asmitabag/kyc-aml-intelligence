import { useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { BrainCircuit, Plus } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import Tabs from '../../components/common/Tabs';
import DetailList from '../../components/common/DetailList';
import DataTable from '../../components/common/DataTable';
import StatusBadge from '../../components/common/StatusBadge';
import RiskBadge from '../../components/common/RiskBadge';
import ErrorState from '../../components/common/ErrorState';
import EmptyState from '../../components/common/EmptyState';
import Modal from '../../components/common/Modal';
import AssessmentView from '../../components/common/AssessmentView';
import JsonBlock from '../../components/common/JsonBlock';
import SchemaForm from '../../components/forms/SchemaForm';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { customerService } from '../../services/customerService';
import { analystService } from '../../services/analystService';
import { formatCurrency, formatDateTime, formatScore, titleCase } from '../../utils/formatters';

export default function CustomerDetail() {
  const { customerId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');
  const [modal, setModal] = useState(null); // 'account' | 'transaction'
  const [txnAccount, setTxnAccount] = useState('');
  const [selectedAssessment, setSelectedAssessment] = useState(null);

  const customer = useAsync(() => customerService.get(customerId), [customerId]);
  const kyc = useAsync(() => customerService.latestKyc(customerId), [customerId]);
  const accounts = useAsync(() => customerService.accounts(customerId), [customerId]);
  const txns = useAsync(() => customerService.transactions(customerId), [customerId]);
  const assessments = useAsync(() => customerService.assessments(customerId), [customerId]);

  const c = customer.data;
  const accountList = accounts.data || [];
  const assessmentList = assessments.data || [];
  const activeAssessment = useMemo(
    () => assessmentList.find((a) => a.assessment_id === selectedAssessment) || assessmentList[assessmentList.length - 1] || null,
    [assessmentList, selectedAssessment],
  );

  if (customer.error) {
    return <div className="panel"><ErrorState error={customer.error} onRetry={customer.reload} title="Couldn't load customer" /></div>;
  }

  const accountColumns = [
    { key: 'account_id', header: 'Account', render: (r) => <span className="font-mono text-xs">{r.account_id}</span> },
    { key: 'account_type', header: 'Type', render: (r) => titleCase(r.account_type) },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
    { key: 'balance', header: 'Balance', className: 'text-right', render: (r) => <span className="tnum font-medium">{formatCurrency(r.balance, r.currency)}</span> },
    { key: 'currency', header: 'Currency' },
  ];
  const txnColumns = [
    { key: 'occurred_at', header: 'Date', render: (r) => <span className="whitespace-nowrap">{formatDateTime(r.occurred_at)}</span> },
    { key: 'transaction_id', header: 'Transaction', render: (r) => <span className="font-mono text-xs">{r.transaction_id}</span> },
    { key: 'account_id', header: 'Account', render: (r) => <span className="font-mono text-xs">{r.account_id}</span> },
    { key: 'direction', header: 'Direction', render: (r) => titleCase(r.direction) },
    { key: 'counterparty', header: 'Counterparty' },
    { key: 'amount', header: 'Amount', className: 'text-right', render: (r) => <span className="tnum font-medium">{formatCurrency(r.amount, r.currency)}</span> },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
    { key: 'data_origin', header: 'Origin', render: (r) => titleCase(r.data_origin) },
  ];
  const assessmentColumns = [
    { key: 'assessment_id', header: 'Assessment', render: (r) => <span className="font-mono text-xs">{r.assessment_id}</span> },
    { key: 'risk_level', header: 'Level', render: (r) => <RiskBadge level={r.risk_level} /> },
    { key: 'final_risk', header: 'Final risk', render: (r) => <span className="tnum">{formatScore(r.final_risk)}</span> },
    { key: 'priority', header: 'Priority' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
  ];

  const k = kyc.data;

  return (
    <>
      <PageHeader
        title={c?.full_name || customerId}
        description={c ? `${c.email || ''}${c.customer_type ? ` · ${titleCase(c.customer_type)}` : ''}` : 'Loading customer…'}
        actions={
          <>
            <button type="button" className="btn-secondary" onClick={() => setModal('account')}>
              <Plus className="h-4 w-4" aria-hidden="true" /> Add account
            </button>
            <button type="button" className="btn-secondary" onClick={() => { setTxnAccount(accountList[0]?.account_id || ''); setModal('transaction'); }} disabled={!accountList.length}>
              <Plus className="h-4 w-4" aria-hidden="true" /> Record transaction
            </button>
            <button type="button" className="btn-primary" onClick={() => navigate(`/analyst/aml?customer=${encodeURIComponent(customerId)}`)}>
              <BrainCircuit className="h-4 w-4" aria-hidden="true" /> Run AML analysis
            </button>
          </>
        }
      />

      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'kyc', label: 'KYC result' },
          { id: 'accounts', label: 'Accounts', count: accounts.data?.length },
          { id: 'transactions', label: 'Transactions', count: txns.data?.length },
          { id: 'assessments', label: 'Assessments', count: assessments.data?.length },
        ]}
      />

      {tab === 'overview' && (
        <Panel title="Customer record">
          {customer.loading ? (
            <PanelSkeleton lines={6} />
          ) : (
            <DetailList data={c} />
          )}
        </Panel>
      )}

      {tab === 'kyc' && (
        <Panel title="Latest KYC result" description="Model probabilities and evidence for the most recent submission.">
          {kyc.loading ? (
            <PanelSkeleton lines={5} />
          ) : kyc.error ? (
            <ErrorState error={kyc.error} onRetry={kyc.reload} compact />
          ) : !k ? (
            <EmptyState title="No KYC submission" description="This customer hasn't submitted KYC details yet." />
          ) : (
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  ['kyc_risk', 'KYC risk'],
                  ['document_tamper_probability', 'Document tamper'],
                  ['liveness_probability', 'Liveness'],
                  ['deepfake_probability', 'Deepfake'],
                ].map(([key, label]) => (
                  <div key={key} className="rounded-lg border border-slate-200 px-3 py-2.5">
                    <p className="text-xs text-slate-500">{label}</p>
                    <p className="tnum mt-0.5 text-lg font-semibold">{formatScore(k[key])}</p>
                  </div>
                ))}
              </div>
              <DetailList
                items={[
                  { key: 'kyc_id', label: 'KYC ID', value: k.kyc_id },
                  { key: 'status', label: 'Status', value: k.status },
                  { key: 'model_version', label: 'Model version', value: k.model_version },
                  { key: 'document_fingerprint', label: 'Document fingerprint', value: k.document_fingerprint },
                  { key: 'evidence_ids', label: 'Evidence IDs', value: k.evidence_ids },
                ]}
              />
              <JsonBlock data={k} />
            </div>
          )}
        </Panel>
      )}

      {tab === 'accounts' && <DataTable columns={accountColumns} rows={accountList} loading={accounts.loading} error={accounts.error} onRetry={accounts.reload} rowKey={(r) => r.account_id} empty={<EmptyState title="No accounts" description="This customer has no accounts yet." />} />}

      {tab === 'transactions' && <DataTable columns={txnColumns} rows={txns.data || []} loading={txns.loading} error={txns.error} onRetry={txns.reload} rowKey={(r) => r.transaction_id} empty={<EmptyState title="No transactions" description="No transactions recorded for this customer." />} />}

      {tab === 'assessments' && (
        <div className="space-y-6">
          <DataTable
            columns={assessmentColumns}
            rows={assessmentList}
            loading={assessments.loading}
            error={assessments.error}
            onRetry={assessments.reload}
            rowKey={(r) => r.assessment_id}
            onRowClick={(r) => setSelectedAssessment(r.assessment_id)}
            empty={<EmptyState title="No assessments" description="Run an AML analysis to produce one." action={<Link to={`/analyst/aml?customer=${encodeURIComponent(customerId)}`} className="btn-primary">Run AML analysis</Link>} />}
          />
          {activeAssessment && (
            <Panel title={`Assessment ${activeAssessment.assessment_id}`}>
              <AssessmentView a={activeAssessment} />
            </Panel>
          )}
        </div>
      )}

      <Modal open={modal === 'account'} onClose={() => setModal(null)} title="Add account">
        <SchemaForm
          specPath="/api/v1/customers/{customer_id}/accounts"
          method="post"
          lockedValues={{ customer_id: customerId }}
          submitLabel="Create account"
          onSubmit={(p) => analystService.createAccountForCustomer(customerId, p)}
          onSuccess={() => { toast.success('Account created.'); setModal(null); accounts.reload(); }}
          onCancel={() => setModal(null)}
        />
      </Modal>

      <Modal open={modal === 'transaction'} onClose={() => setModal(null)} title="Record transaction" size="lg">
        <label className="label" htmlFor="txn-account">Account</label>
        <select id="txn-account" className="input mb-4" value={txnAccount} onChange={(e) => setTxnAccount(e.target.value)}>
          {accountList.map((a) => (
            <option key={a.account_id} value={a.account_id}>{a.account_id} — {titleCase(a.account_type)}</option>
          ))}
        </select>
        {txnAccount && (
          <SchemaForm
            key={txnAccount}
            specPath="/api/v1/accounts/{account_id}/transactions"
            method="post"
            lockedValues={{ account_id: txnAccount }}
            submitLabel="Record transaction"
            onSubmit={(p) => analystService.createTransaction(txnAccount, p)}
            onSuccess={() => { toast.success('Transaction recorded.'); setModal(null); txns.reload(); accounts.reload(); }}
            onCancel={() => setModal(null)}
          />
        )}
      </Modal>
    </>
  );
}
