import { Link } from 'react-router-dom';
import { ArrowDownLeft, ArrowUpRight, CheckCircle2, Circle, CreditCard, FileCheck2, Gauge, Wallet } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import StatCard from '../../components/common/StatCard';
import StatusBadge from '../../components/common/StatusBadge';
import RiskBadge from '../../components/common/RiskBadge';
import ErrorState from '../../components/common/ErrorState';
import EmptyState from '../../components/common/EmptyState';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { useOwnCustomer } from '../../hooks/useOwnCustomer';
import { customerService } from '../../services/customerService';
import { formatCurrency, formatDateTime, pickLatest, sumByCurrency, titleCase } from '../../utils/formatters';
import { isKycComplete } from './kycHelpers';
import NotLinked from './NotLinked';

export default function Dashboard() {
  const { customerId, user, linked } = useOwnCustomer();
  const enabled = linked;

  const customer = useAsync(() => customerService.get(customerId), [customerId], { enabled });
  const kyc = useAsync(() => customerService.latestKyc(customerId), [customerId], { enabled });
  const accounts = useAsync(() => customerService.accounts(customerId), [customerId], { enabled });
  const txns = useAsync(() => customerService.transactions(customerId), [customerId], { enabled });
  const assessments = useAsync(() => customerService.assessments(customerId), [customerId], { enabled });

  if (!linked) return <NotLinked />;

  const c = customer.data;
  const totals = Object.entries(sumByCurrency(accounts.data || []));
  const latestAssessment = pickLatest(assessments.data || []);
  const recent = [...(txns.data || [])]
    .sort((a, b) => new Date(b.occurred_at || 0) - new Date(a.occurred_at || 0))
    .slice(0, 5);
  const kycDone = isKycComplete(c?.kyc_status);

  const steps = [
    { done: !!c, label: 'Account created' },
    { done: !!kyc.data || (!!c?.kyc_status && c.kyc_status !== 'not_started'), label: 'Verification details submitted' },
    { done: kycDone, label: 'Verification approved' },
  ];

  return (
    <>
      <PageHeader title={`Welcome${c?.full_name ? `, ${c.full_name.split(' ')[0]}` : ''}`} description={`Signed in as ${user?.email}.`} />

      {customer.error && <div className="panel mb-6"><ErrorState error={customer.error} onRetry={customer.reload} compact /></div>}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Verification status" loading={customer.loading} error={customer.error} value={c ? titleCase(c.kyc_status) : '—'} icon={FileCheck2} tone={kycDone ? 'green' : 'amber'} to="/customer/kyc" />
        <StatCard label="Onboarding" loading={customer.loading} error={customer.error} value={c ? titleCase(c.onboarding_status) : '—'} icon={CheckCircle2} tone="indigo" />
        <StatCard
          label="Total balance"
          loading={accounts.loading}
          error={accounts.error}
          value={totals.length ? totals.map(([cur, n]) => formatCurrency(n, cur === '—' ? undefined : cur)).join(' · ') : '—'}
          hint={totals.length ? `${accounts.data.length} account${accounts.data.length === 1 ? '' : 's'}` : 'No accounts yet'}
          icon={Wallet}
          tone="green"
          to="/customer/accounts"
        />
      </div>

      {!customer.loading && c && !kycDone && (
        <Panel className="mt-6" title="Finish your verification" description="Here's what's left before your account is fully verified.">
          <ol className="space-y-3">
            {steps.map((s) => (
              <li key={s.label} className="flex items-center gap-3 text-sm">
                {s.done ? <CheckCircle2 className="h-5 w-5 text-emerald-500" aria-hidden="true" /> : <Circle className="h-5 w-5 text-slate-300" aria-hidden="true" />}
                <span className={s.done ? 'text-slate-500' : 'font-medium text-ink'}>{s.label}</span>
              </li>
            ))}
          </ol>
          <Link to="/customer/kyc" className="btn-primary mt-5">
            {kyc.data ? 'View verification status' : 'Start verification'}
          </Link>
        </Panel>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <Panel className="lg:col-span-3" title="Recent transactions" actions={<Link to="/customer/transactions" className="text-sm font-medium text-indigo-600 hover:underline">View all</Link>} padded={false}>
          {txns.loading ? (
            <PanelSkeleton lines={5} />
          ) : txns.error ? (
            <ErrorState error={txns.error} onRetry={txns.reload} compact />
          ) : recent.length === 0 ? (
            <EmptyState icon={CreditCard} title="No transactions yet" description="Activity on your accounts will appear here." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {recent.map((t) => {
                const incoming = String(t.direction || '').toLowerCase().startsWith('in') || String(t.direction || '').toLowerCase() === 'credit';
                return (
                  <li key={t.transaction_id} className="flex items-center gap-3 px-5 py-3">
                    <span className={`rounded-full p-1.5 ${incoming ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'}`}>
                      {incoming ? <ArrowDownLeft className="h-4 w-4" aria-hidden="true" /> : <ArrowUpRight className="h-4 w-4" aria-hidden="true" />}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-ink">{t.counterparty || t.description || t.transaction_id}</p>
                      <p className="text-xs text-slate-500">{formatDateTime(t.occurred_at)}</p>
                    </div>
                    <p className="tnum text-sm font-medium">{formatCurrency(t.amount, t.currency)}</p>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>

        <Panel className="lg:col-span-2" title="Latest risk review" actions={<Link to="/customer/risk" className="text-sm font-medium text-indigo-600 hover:underline">Details</Link>}>
          {assessments.loading ? (
            <PanelSkeleton lines={3} />
          ) : assessments.error ? (
            <ErrorState error={assessments.error} onRetry={assessments.reload} compact />
          ) : !latestAssessment ? (
            <EmptyState icon={Gauge} title="No review yet" description="A risk review appears here after your information has been assessed." />
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Risk level</span>
                <RiskBadge level={latestAssessment.risk_level} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Status</span>
                <StatusBadge value={latestAssessment.status} />
              </div>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
