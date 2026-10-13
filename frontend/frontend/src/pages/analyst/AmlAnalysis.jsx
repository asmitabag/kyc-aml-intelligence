import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { BrainCircuit } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import Tabs from '../../components/common/Tabs';
import Notice from '../../components/common/Notice';
import ResultView from '../../components/common/ResultView';
import EmptyState from '../../components/common/EmptyState';
import CustomerPicker from '../../components/forms/CustomerPicker';
import SchemaForm from '../../components/forms/SchemaForm';
import { useAsync } from '../../hooks/useAsync';
import { healthService } from '../../services/healthService';
import { analystService } from '../../services/analystService';
import JsonBlock from '../../components/common/JsonBlock';

export default function AmlAnalysis() {
  const [params] = useSearchParams();
  const [tab, setTab] = useState('customer');
  const [customerId, setCustomerId] = useState(params.get('customer') || '');
  const [analysis, setAnalysis] = useState(null);
  const [score, setScore] = useState(null);
  const health = useAsync(() => healthService.api(), []);

  return (
    <>
      <PageHeader title="AML analysis" description="Run the AML workflow for a customer or score a single transaction. Fallback and unavailable states are shown as returned." />

      <Panel title="Model availability" description="GET /api/v1/health" className="mb-6">
        {health.loading ? (
          <p className="text-sm text-slate-500">Checking…</p>
        ) : health.error ? (
          <Notice tone="error" title="Health check failed">{health.error.message}</Notice>
        ) : (
          <JsonBlock data={health.data} summary="Health response" />
        )}
      </Panel>

      <Tabs value={tab} onChange={setTab} tabs={[{ id: 'customer', label: 'Customer analysis' }, { id: 'transaction', label: 'Transaction scoring' }]} />

      {tab === 'customer' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Panel title="Run analysis">
            <div className="space-y-4">
              <CustomerPicker value={customerId} onChange={(v) => { setCustomerId(v); setAnalysis(null); }} id="aml-customer" />
              {customerId ? (
                <SchemaForm
                  key={customerId}
                  specPath="/api/v1/customers/{customer_id}/aml-analysis"
                  method="post"
                  lockedValues={{ customer_id: customerId }}
                  submitLabel="Run AML analysis"
                  confirm={{ title: 'Run AML analysis?', message: `This runs the analysis for ${customerId} and may create a risk assessment and alerts.` }}
                  onSubmit={(p) => analystService.runAmlAnalysis(customerId, p)}
                  onSuccess={(res) => { setAnalysis(res ?? { status: 'completed' }); toast.success('AML analysis request finished.'); }}
                />
              ) : (
                <p className="text-sm text-slate-500">Select a customer to continue.</p>
              )}
            </div>
          </Panel>
          <Panel title="Result">
            {analysis ? <ResultView result={analysis} /> : <EmptyState icon={BrainCircuit} title="No result yet" description="The analysis response, model status and any created assessment or alert IDs appear here." />}
          </Panel>
        </div>
      )}

      {tab === 'transaction' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Panel title="Score a transaction" description="Fields come from TransactionAMLRequest.">
            <SchemaForm
              specPath="/api/v1/aml/score-transaction"
              method="post"
              submitLabel="Score transaction"
              onSubmit={(p) => analystService.scoreTransaction(p)}
              onSuccess={(res) => setScore(res)}
            />
          </Panel>
          <Panel title="Result">
            {score ? <ResultView result={score} /> : <EmptyState icon={BrainCircuit} title="No score yet" description="Model name, version, status, ranking score, feature count and interpretation appear here." />}
          </Panel>
        </div>
      )}
    </>
  );
}
