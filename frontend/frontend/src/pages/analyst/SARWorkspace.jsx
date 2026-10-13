import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FilePlus2, FileText, Search } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../../components/common/PageHeader';
import Panel from '../../components/common/Panel';
import Tabs from '../../components/common/Tabs';
import DraftBanner from '../../components/common/DraftBanner';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import Modal from '../../components/common/Modal';
import SarView from '../../components/common/SarView';
import ResultView from '../../components/common/ResultView';
import SchemaForm from '../../components/forms/SchemaForm';
import { PanelSkeleton } from '../../components/common/Skeleton';
import { useAsync } from '../../hooks/useAsync';
import { caseService } from '../../services/caseService';
import { sarService } from '../../services/sarService';
import { normalizeError } from '../../utils/errors';
import { titleCase, unwrapList } from '../../utils/formatters';
import { caseIdOf } from './Cases';

export default function SARWorkspace() {
  const [params] = useSearchParams();
  const [caseId, setCaseId] = useState(params.get('case') || '');
  const [sarLookup, setSarLookup] = useState('');
  const [tab, setTab] = useState('case');
  const [creating, setCreating] = useState(false);

  const cases = useAsync(() => caseService.list(), []);
  const drafts = useAsync(async () => {
    const data = await sarService.getForCase(caseId);
    return Array.isArray(data) ? data : unwrapList(data).length ? unwrapList(data) : data ? [data] : [];
  }, [caseId], { enabled: !!caseId && tab === 'case' });

  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [lookup, setLookup] = useState({ data: null, error: null, loading: false });
  const [activeSar, setActiveSar] = useState(null);

  const run = async (kind, fn, okMsg) => {
    setBusy(kind);
    setActionError(null);
    try {
      const res = await fn();
      toast.success(okMsg);
      return res;
    } catch (e) {
      setActionError(normalizeError(e));
      return null;
    } finally {
      setBusy(null);
    }
  };

  const generatePreview = async () => {
    const res = await run('preview', () => caseService.generateSarPreview(caseId), 'SAR preview generated (not saved).');
    if (res) setPreview(res);
  };
  const createDraft = async () => {
    const res = await run('draft', () => sarService.createFromCase(caseId), 'SAR draft created — pending human review.');
    if (res) {
      setActiveSar(res);
      drafts.reload();
    }
  };

  const findDraft = async (e) => {
    e.preventDefault();
    setLookup({ data: null, error: null, loading: true });
    try {
      const data = await sarService.getDraft(sarLookup.trim());
      setLookup({ data, error: null, loading: false });
    } catch (err) {
      setLookup({ data: null, error: normalizeError(err), loading: false });
    }
  };

  const draftList = drafts.data || [];
  const shownDraft = activeSar || null;

  return (
    <>
      <PageHeader title="SAR workspace" description="Prepare suspicious activity report drafts from cases. Nothing here is filed with any authority." />
      <DraftBanner className="mb-6" />

      <Tabs value={tab} onChange={setTab} tabs={[{ id: 'case', label: 'From a case' }, { id: 'lookup', label: 'Find a draft' }]} />

      {tab === 'case' && (
        <div className="space-y-6">
          <Panel title="Select a case">
            <label htmlFor="sar-case" className="label">Case ID</label>
            <input
              id="sar-case"
              list="sar-case-list"
              className="input max-w-md"
              value={caseId}
              onChange={(e) => { setCaseId(e.target.value.trim()); setPreview(null); setActiveSar(null); setActionError(null); }}
              placeholder="Type or paste a case ID"
              autoComplete="off"
            />
            <datalist id="sar-case-list">
              {(cases.data || []).map((c) => (
                <option key={caseIdOf(c)} value={caseIdOf(c)}>{c.status ? titleCase(c.status) : ''}</option>
              ))}
            </datalist>
            {cases.error && <p className="mt-1 text-xs text-amber-600">Case list unavailable ({cases.error.message}). Paste a case ID instead.</p>}

            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" className="btn-secondary" disabled={!caseId || !!busy} onClick={generatePreview}>
                <FileText className="h-4 w-4" aria-hidden="true" /> {busy === 'preview' ? 'Generating…' : 'Generate preview'}
              </button>
              <button type="button" className="btn-primary" disabled={!caseId || !!busy} onClick={createDraft}>
                <FilePlus2 className="h-4 w-4" aria-hidden="true" /> {busy === 'draft' ? 'Creating…' : 'Create draft from case'}
              </button>
              <button type="button" className="btn-ghost" disabled={!caseId} onClick={() => setCreating(true)}>
                Create draft manually
              </button>
            </div>
            {actionError && (
              <div className="mt-4"><ErrorState error={actionError} compact /></div>
            )}
          </Panel>

          {preview && (
            <Panel title="Preview (not saved)" description="Generated on request. Create a draft to keep it.">
              {preview.narrative !== undefined || preview.review_status !== undefined ? <SarView sar={preview} /> : <ResultView result={preview} />}
            </Panel>
          )}

          {shownDraft && (
            <Panel title="Draft just created">
              <SarView sar={shownDraft} />
            </Panel>
          )}

          {caseId && (
            <Panel title="Saved drafts for this case" padded={false}>
              {drafts.loading ? (
                <PanelSkeleton lines={4} />
              ) : drafts.error ? (
                drafts.error.status === 404 ? (
                  <EmptyState icon={FileText} title="No drafts yet" description="Create a draft from this case to start the review." />
                ) : (
                  <ErrorState error={drafts.error} onRetry={drafts.reload} compact />
                )
              ) : draftList.length === 0 ? (
                <EmptyState icon={FileText} title="No drafts yet" description="Create a draft from this case to start the review." />
              ) : (
                <div className="divide-y divide-slate-100">
                  {draftList.map((d, i) => (
                    <div key={d.sar_id ?? i} className="space-y-6 p-5">
                      <SarView sar={d} />
                      {d.sar_id && (
                        <div className="rounded-lg border border-slate-200 p-4">
                          <h3 className="mb-3 text-sm font-semibold text-ink">Update review status</h3>
                          <SchemaForm
                            key={d.sar_id}
                            specPath="/api/v1/sar-drafts/{sar_id}/status"
                            method="patch"
                            submitLabel="Update review status"
                            confirm={{ title: 'Update review status?', message: 'This records a review decision on the draft. It does not file the report with any authority.' }}
                            onSubmit={(p) => sarService.updateStatus(d.sar_id, p)}
                            onSuccess={() => { toast.success('Review status updated.'); drafts.reload(); }}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          )}
        </div>
      )}

      {tab === 'lookup' && (
        <div className="space-y-6">
          <form onSubmit={findDraft} className="panel flex flex-col gap-3 p-5 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label htmlFor="sar-id" className="label">SAR draft ID</label>
              <input id="sar-id" className="input" value={sarLookup} onChange={(e) => setSarLookup(e.target.value)} autoComplete="off" />
            </div>
            <button type="submit" className="btn-primary" disabled={!sarLookup.trim() || lookup.loading}>
              <Search className="h-4 w-4" aria-hidden="true" /> {lookup.loading ? 'Searching…' : 'Find draft'}
            </button>
          </form>

          {lookup.error && <div className="panel"><ErrorState error={lookup.error} compact /></div>}
          {lookup.data && (
            <Panel title={`Draft ${lookup.data.sar_id ?? sarLookup}`}>
              <div className="space-y-6">
                <SarView sar={lookup.data} />
                <div className="rounded-lg border border-slate-200 p-4">
                  <h3 className="mb-3 text-sm font-semibold text-ink">Update review status</h3>
                  <SchemaForm
                    key={lookup.data.sar_id ?? sarLookup}
                    specPath="/api/v1/sar-drafts/{sar_id}/status"
                    method="patch"
                    submitLabel="Update review status"
                    confirm={{ title: 'Update review status?', message: 'This records a review decision on the draft. It does not file the report with any authority.' }}
                    onSubmit={(p) => sarService.updateStatus(lookup.data.sar_id ?? sarLookup.trim(), p)}
                    onSuccess={async () => {
                      toast.success('Review status updated.');
                      try { setLookup({ data: await sarService.getDraft(sarLookup.trim()), error: null, loading: false }); } catch { /* keep previous view */ }
                    }}
                  />
                </div>
              </div>
            </Panel>
          )}
        </div>
      )}

      <Modal open={creating} onClose={() => setCreating(false)} title="Create SAR draft manually" size="lg">
        <SchemaForm
          specPath="/api/v1/sar-drafts"
          method="post"
          initialValues={{ case_id: caseId }}
          submitLabel="Create draft"
          onSubmit={(p) => sarService.createDraft(p)}
          onSuccess={(res) => { toast.success('SAR draft created — pending human review.'); setCreating(false); if (res) setActiveSar(res); drafts.reload(); }}
          onCancel={() => setCreating(false)}
        />
      </Modal>
    </>
  );
}
