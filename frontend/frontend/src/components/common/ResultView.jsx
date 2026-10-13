import DetailList from './DetailList';
import JsonBlock from './JsonBlock';
import Notice from './Notice';
import StatusBadge from './StatusBadge';
import { isNil, titleCase } from '../../utils/formatters';

const ID_LINKS = {
  assessment_id: (v) => `/analyst/assessments?assessment=${encodeURIComponent(v)}`,
  alert_id: (v) => `/analyst/alerts/${encodeURIComponent(v)}`,
  case_id: (v) => `/analyst/cases/${encodeURIComponent(v)}`,
  customer_id: (v) => `/analyst/customers/${encodeURIComponent(v)}`,
};

const STATUS_FIELDS = ['status', 'model_status', 'analysis_status', 'aml_status', 'result_status'];

// Displays an analysis/scoring response honestly: fallback and unavailable states
// are surfaced prominently and are never styled as a successful model prediction.
export default function ResultView({ result }) {
  if (!result || typeof result !== 'object') return null;

  const statusKey = STATUS_FIELDS.find((k) => typeof result[k] === 'string');
  const status = statusKey ? result[statusKey] : null;
  const lower = String(status || '').toLowerCase();
  const isFallback = lower.includes('fallback') || result.fallback === true || result.fallback_used === true;
  const isUnavailable = lower.includes('unavailable');

  const errors = [result.error, result.errors, result.error_detail, result.error_message].filter((e) => !isNil(e) && !(Array.isArray(e) && !e.length));
  const explain = ['explanation', 'explanations', 'interpretation', 'rationale', 'summary'].filter((k) => !isNil(result[k]));

  const scalars = Object.entries(result).filter(
    ([k, v]) => (v === null || typeof v !== 'object') && !explain.includes(k) && k !== statusKey && !['error', 'error_detail', 'error_message', 'fallback', 'fallback_used'].includes(k),
  );
  const links = Object.fromEntries(Object.keys(ID_LINKS).map((k) => [k, ID_LINKS[k]]));

  return (
    <div className="space-y-4">
      {isUnavailable && (
        <Notice tone="error" title="Model unavailable">
          The backend reports the required model could not be used. No prediction was produced.
        </Notice>
      )}
      {isFallback && !isUnavailable && (
        <Notice tone="warn" title="Fallback result — not a full model prediction">
          The backend completed this request using a fallback path. Treat the output below as lower confidence and review it manually.
        </Notice>
      )}
      {errors.length > 0 && (
        <Notice tone="error" title="Errors reported">
          {errors.map((e, i) => (
            <pre key={i} className="whitespace-pre-wrap font-sans text-sm">
              {typeof e === 'string' ? e : JSON.stringify(e, null, 2)}
            </pre>
          ))}
        </Notice>
      )}

      {status && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-slate-500">{titleCase(statusKey)}</span>
          <StatusBadge value={status} />
        </div>
      )}

      {scalars.length > 0 && <DetailList items={scalars.map(([key, value]) => ({ key, value }))} links={links} />}

      {explain.map((k) => (
        <div key={k}>
          <h4 className="mb-1 text-sm font-semibold text-ink">{titleCase(k)}</h4>
          <div className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
            {typeof result[k] === 'string' ? result[k] : <pre className="text-xs">{JSON.stringify(result[k], null, 2)}</pre>}
          </div>
        </div>
      ))}

      <JsonBlock data={result} summary="Full response" />
    </div>
  );
}

