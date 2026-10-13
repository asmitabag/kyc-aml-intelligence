import { useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertTriangle, ClipboardList, Gauge, Users } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import StatCard from '../../components/common/StatCard';
import DataTable from '../../components/common/DataTable';
import AutoTable from '../../components/common/AutoTable';
import RiskBadge from '../../components/common/RiskBadge';
import StatusBadge from '../../components/common/StatusBadge';
import ErrorState from '../../components/common/ErrorState';
import Notice from '../../components/common/Notice';
import DonutChart from '../../components/charts/DonutChart';
import BarChartCard from '../../components/charts/BarChartCard';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { analystService } from '../../services/analystService';
import { alertService } from '../../services/alertService';
import { caseService } from '../../services/caseService';
import { customerService } from '../../services/customerService';
import { countBy, formatNumber } from '../../utils/formatters';

// There is no global assessments endpoint, so risk figures are sampled from the
// first N customers' assessments (GET /customers/{id}/assessments).
const SAMPLE_SIZE = 25;
const HIGH = /(high|critical|urgent|severe)/i;

async function sampleAssessments(customers) {
  const sample = customers.slice(0, SAMPLE_SIZE);
  const results = await Promise.allSettled(sample.map((c) => customerService.assessments(c.customer_id)));
  const ok = results.filter((r) => r.status === 'fulfilled').flatMap((r) => r.value);
  const failed = results.filter((r) => r.status === 'rejected').length;
  return { assessments: ok, failed, sampled: sample.length };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const customers = useAsync(() => analystService.listCustomers(), []);
  const alerts = useAsync(() => alertService.list(), []);
  const cases = useAsync(() => caseService.list(), []);
  const sample = useAsync(() => sampleAssessments(customers.data), [customers.data], { enabled: !!customers.data && customers.data.length > 0 });

  const alertList = alerts.data || [];
  const caseList = cases.data || [];
  const openAlerts = alertList.filter((a) => String(a.status).toLowerCase() === 'open').length;
  const highCases = caseList.filter((c) => HIGH.test(String(c.priority ?? c.severity ?? c.risk_level ?? ''))).length;

  const riskData = useMemo(() => countBy(sample.data?.assessments || [], 'risk_level'), [sample.data]);
  const alertStatusData = useMemo(() => countBy(alertList, 'status'), [alertList]);
  const recentAlerts = useMemo(() => {
    const list = [...alertList];
    const dated = list.every((a) => a.created_at);
    return (dated ? list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) : list.reverse()).slice(0, 6);
  }, [alertList]);
  const recentCases = useMemo(() => [...caseList].reverse().slice(0, 6), [caseList]);

  const alertColumns = [
    { key: 'alert_id', header: 'Alert', render: (r) => <span className="font-mono text-xs">{r.alert_id}</span> },
    { key: 'alert_type', header: 'Type' },
    { key: 'severity', header: 'Severity', render: (r) => <RiskBadge level={r.severity} /> },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge value={r.status} /> },
  ];

  return (
    <>
      <PageHeader title="Dashboard" description="Monitoring overview across customers, alerts and investigations." />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total customers" icon={Users} loading={customers.loading} error={customers.error} value={formatNumber(customers.data?.length)} to="/analyst/customers" />
        <StatCard label="Open alerts" icon={AlertTriangle} tone="amber" loading={alerts.loading} error={alerts.error} value={formatNumber(openAlerts)} hint={`of ${alertList.length} total`} to="/analyst/alerts" />
        <StatCard label="High-priority cases" icon={ClipboardList} tone="red" loading={cases.loading} error={cases.error} value={formatNumber(highCases)} hint={`of ${caseList.length} total`} to="/analyst/cases" />
        <StatCard
          label="Assessments reviewed"
          icon={Gauge}
          tone="slate"
          loading={customers.loading || sample.loading}
          error={sample.error}
          value={formatNumber(sample.data?.assessments.length ?? 0)}
          hint={sample.data ? `sampled from ${sample.data.sampled} customer${sample.data.sampled === 1 ? '' : 's'}` : undefined}
          to="/analyst/assessments"
        />
      </div>

      {sample.data && (customers.data?.length || 0) > SAMPLE_SIZE && (
        <Notice className="mt-4">
          Risk-level figures are sampled from the first {SAMPLE_SIZE} of {customers.data.length} customers, because the API has no global assessments endpoint.
        </Notice>
      )}
      {sample.data?.failed > 0 && (
        <Notice tone="warn" className="mt-4">
          Assessments could not be loaded for {sample.data.failed} sampled customer{sample.data.failed === 1 ? '' : 's'}; the charts exclude them.
        </Notice>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel title="Risk levels" description="From sampled risk assessments">
          {customers.loading || sample.loading ? <PanelSkeleton lines={5} /> : sample.error ? <ErrorState error={sample.error} onRetry={sample.reload} compact /> : <DonutChart data={riskData} label="Risk levels" />}
        </Panel>
        <Panel title="Alert statuses" description="From all alerts">
          {alerts.loading ? <PanelSkeleton lines={5} /> : alerts.error ? <ErrorState error={alerts.error} onRetry={alerts.reload} compact /> : <BarChartCard data={alertStatusData} label="Alert statuses" />}
        </Panel>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Panel title="Recent alerts" actions={<Link to="/analyst/alerts" className="text-sm font-medium text-indigo-600 hover:underline">All alerts</Link>} padded={false}>
          <DataTable columns={alertColumns} rows={recentAlerts} loading={alerts.loading} error={alerts.error} onRetry={alerts.reload} rowKey={(r) => r.alert_id} onRowClick={(r) => navigate(`/analyst/alerts/${encodeURIComponent(r.alert_id)}`)} pageSize={6} />
        </Panel>
        <Panel title="Recent investigations" actions={<Link to="/analyst/cases" className="text-sm font-medium text-indigo-600 hover:underline">All cases</Link>} padded={false}>
          <AutoTable
            rows={recentCases}
            preferred={['case_id', 'customer_id', 'status', 'priority']}
            maxColumns={4}
            loading={cases.loading}
            error={cases.error}
            onRetry={cases.reload}
            rowKey={(r) => r.case_id ?? r.id}
            onRowClick={(r) => navigate(`/analyst/cases/${encodeURIComponent(r.case_id ?? r.id)}`)}
            pageSize={6}
          />
        </Panel>
      </div>
    </>
  );
}
