import { useState } from 'react';
import { Download, MessageSquareText } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Tabs from '../../components/common/Tabs';
import AutoTable from '../../components/common/AutoTable';
import EmptyState from '../../components/common/EmptyState';
import Notice from '../../components/common/Notice';
import { useAsync } from '../../hooks/useAsync';
import { analystService } from '../../services/analystService';
import { caseService } from '../../services/caseService';

const SOURCES = {
  feedback: { label: 'Analyst feedback', path: 'GET /api/v1/feedback', load: () => analystService.listFeedback() },
  dataset: { label: 'Feedback dataset', path: 'GET /api/v1/feedback/dataset', load: () => analystService.feedbackDataset() },
  cases: { label: 'Case feedback dataset', path: 'GET /cases/feedback/dataset', load: () => caseService.feedbackDataset() },
};

function downloadJson(name, data) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = `${name}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Feedback() {
  const [tab, setTab] = useState('feedback');
  const src = SOURCES[tab];
  // Each tab loads only when selected.
  const { data, loading, error, reload } = useAsync(src.load, [tab]);

  return (
    <>
      <PageHeader
        title="Feedback & datasets"
        description="Analyst decisions captured for model evaluation."
        actions={
          <button type="button" className="btn-secondary" disabled={!data?.length} onClick={() => downloadJson(tab, data)}>
            <Download className="h-4 w-4" aria-hidden="true" /> Download JSON
          </button>
        }
      />
      <Notice className="mb-4">These datasets may contain case details and analyst rationale. Handle exports according to your data-protection policy.</Notice>

      <Tabs value={tab} onChange={setTab} tabs={Object.entries(SOURCES).map(([id, s]) => ({ id, label: s.label }))} />
      <p className="mb-3 font-mono text-xs text-slate-400">{src.path}</p>

      <AutoTable
        key={tab}
        rows={data || []}
        loading={loading}
        error={error}
        onRetry={reload}
        maxColumns={8}
        empty={<EmptyState icon={MessageSquareText} title="No records" description="Nothing has been recorded here yet." />}
      />
    </>
  );
}
