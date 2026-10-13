import { CheckCircle2, Circle } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import Notice from '../../components/common/Notice';
import StatusBadge from '../../components/common/StatusBadge';
import ErrorState from '../../components/common/ErrorState';
import DetailList from '../../components/common/DetailList';
import { PanelSkeleton } from '../../components/common/Skeleton';
import SchemaForm from '../../components/forms/SchemaForm';
import { useAsync } from '../../hooks/useAsync';
import { useOwnCustomer } from '../../hooks/useOwnCustomer';
import { customerService } from '../../services/customerService';
import { formatDateTime } from '../../utils/formatters';
import { isKycComplete } from './kycHelpers';
import NotLinked from './NotLinked';

export default function KYC() {
  const { customerId, linked } = useOwnCustomer();
  const customer = useAsync(() => customerService.get(customerId), [customerId], { enabled: linked });
  const latest = useAsync(() => customerService.latestKyc(customerId), [customerId], { enabled: linked });

  if (!linked) return <NotLinked />;

  const reloadAll = () => {
    customer.reload();
    latest.reload();
  };
  const status = customer.data?.kyc_status;
  const submitted = !!latest.data;
  const done = isKycComplete(status);

  const steps = [
    { label: 'Details submitted', done: submitted },
    { label: 'Review', done: done },
  ];

  return (
    <>
      <PageHeader title="Identity verification" description="Submit your details so we can verify your identity." />

      <Notice tone="info" title="Demo workflow" className="mb-6">
        This environment verifies identity using a demonstration pipeline. Don't enter real identity documents or other sensitive personal data unless your administrator has told you this is a live system.
      </Notice>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="space-y-6 lg:col-span-2">
          <Panel title="Current status">
            {customer.loading || latest.loading ? (
              <PanelSkeleton lines={3} />
            ) : customer.error ? (
              <ErrorState error={customer.error} onRetry={reloadAll} compact />
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Verification</span>
                  <StatusBadge value={status} />
                </div>
                <ol className="space-y-2.5 border-t border-slate-100 pt-4">
                  {steps.map((s) => (
                    <li key={s.label} className="flex items-center gap-2.5 text-sm">
                      {s.done ? <CheckCircle2 className="h-4 w-4 text-emerald-500" aria-hidden="true" /> : <Circle className="h-4 w-4 text-slate-300" aria-hidden="true" />}
                      <span className={s.done ? 'text-slate-500' : 'text-ink'}>{s.label}</span>
                    </li>
                  ))}
                </ol>
                {latest.error ? (
                  <ErrorState error={latest.error} onRetry={latest.reload} compact />
                ) : latest.data ? (
                  <div className="border-t border-slate-100 pt-4">
                    <DetailList
                      columns={1}
                      items={[
                        { key: 'kyc_id', label: 'Reference', value: latest.data.kyc_id },
                        { key: 'status', label: 'Result status', value: latest.data.status },
                        { key: 'updated_at', label: 'Last updated', value: latest.data.updated_at || latest.data.created_at, render: formatDateTime(latest.data.updated_at || latest.data.created_at) },
                      ]}
                    />
                  </div>
                ) : (
                  <p className="border-t border-slate-100 pt-4 text-sm text-slate-500">You haven't submitted verification details yet.</p>
                )}
              </div>
            )}
          </Panel>
        </div>

        <Panel className="lg:col-span-3" title={submitted ? 'Submit updated details' : 'Verification details'} description="Fields come directly from the verification service.">
          <SchemaForm
            specPath="/api/v1/customers/{customer_id}/kyc"
            method="post"
            // customer_id is forced from the session; the user can't choose it.
            lockedValues={{ customer_id: customerId }}
            submitLabel="Submit for verification"
            // customer_id is only added to the body when the KYCSubmit schema defines it.
            onSubmit={(payload) => customerService.submitKyc(customerId, payload)}
            onSuccess={() => {
              toast.success('Verification details submitted.');
              reloadAll();
            }}
          />
        </Panel>
      </div>
    </>
  );
}
