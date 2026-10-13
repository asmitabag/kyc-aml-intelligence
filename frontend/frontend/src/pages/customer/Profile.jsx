import { LogOut } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import DetailList from '../../components/common/DetailList';
import ErrorState from '../../components/common/ErrorState';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAuth } from '../../auth/AuthProvider';
import { useAsync } from '../../hooks/useAsync';
import { customerService } from '../../services/customerService';
import { formatDateTime, titleCase } from '../../utils/formatters';
import NotLinked from './NotLinked';

export default function Profile() {
  const { user, customerId, logout } = useAuth();
  const { data, loading, error, reload } = useAsync(() => customerService.get(customerId), [customerId], { enabled: !!customerId });

  return (
    <>
      <PageHeader
        title="My profile"
        description="Your account and customer details."
        actions={
          <button type="button" onClick={logout} className="btn-secondary">
            <LogOut className="h-4 w-4" aria-hidden="true" /> Sign out
          </button>
        }
      />

      <div className="space-y-6">
        <Panel title="Login">
          <DetailList
            items={[
              { key: 'email', label: 'Email', value: user?.email },
              { key: 'role', label: 'Account type', value: titleCase(user?.role) },
              { key: 'customer_id', label: 'Customer ID', value: user?.customer_id },
            ]}
          />
        </Panel>

        {!customerId ? (
          <NotLinked />
        ) : (
          <Panel title="Customer details">
            {loading ? (
              <PanelSkeleton lines={5} />
            ) : error ? (
              <ErrorState error={error} onRetry={reload} compact />
            ) : (
              <DetailList
                items={[
                  { key: 'full_name', label: 'Full name', value: data?.full_name },
                  { key: 'email', label: 'Email', value: data?.email },
                  { key: 'phone', label: 'Phone', value: data?.phone },
                  { key: 'customer_type', label: 'Customer type', value: titleCase(data?.customer_type) },
                  { key: 'kyc_status', label: 'Verification status', value: data?.kyc_status },
                  { key: 'onboarding_status', label: 'Onboarding status', value: data?.onboarding_status },
                  { key: 'created_at', label: 'Member since', value: data?.created_at, render: formatDateTime(data?.created_at) },
                ]}
              />
            )}
          </Panel>
        )}
      </div>
    </>
  );
}
