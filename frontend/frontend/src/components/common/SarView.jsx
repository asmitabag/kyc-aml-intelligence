import DraftBanner from './DraftBanner';
import DetailList from './DetailList';
import JsonBlock from './JsonBlock';
import Notice from './Notice';
import StatusBadge from './StatusBadge';
import { isNil } from '../../utils/formatters';

const LINKS = {
  case_id: (v) => `/analyst/cases/${encodeURIComponent(v)}`,
  customer_id: (v) => `/analyst/customers/${encodeURIComponent(v)}`,
  alert_id: (v) => `/analyst/alerts/${encodeURIComponent(v)}`,
};

export default function SarView({ sar }) {
  if (!sar) return null;
  const unsupported = Array.isArray(sar.unsupported_claims) ? sar.unsupported_claims : isNil(sar.unsupported_claims) ? [] : [sar.unsupported_claims];

  return (
    <div className="space-y-5">
      <DraftBanner />

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
        <span className="flex items-center gap-2">
          <span className="text-slate-500">Review status</span>
          <StatusBadge value={sar.review_status} />
        </span>
        <span className="flex items-center gap-2">
          <span className="text-slate-500">Validation</span>
          <StatusBadge value={sar.validation_status} />
        </span>
      </div>

      {unsupported.length > 0 ? (
        <Notice tone="error" title={`${unsupported.length} unsupported claim${unsupported.length === 1 ? '' : 's'} found`}>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {unsupported.map((c, i) => (
              <li key={i}>{typeof c === 'string' ? c : JSON.stringify(c)}</li>
            ))}
          </ul>
          <p className="mt-2">Remove or substantiate these before the draft is approved.</p>
        </Notice>
      ) : (
        <p className="text-sm text-slate-500">No unsupported claims were reported by the validator.</p>
      )}

      <DetailList
        items={[
          { key: 'sar_id', label: 'SAR draft ID', value: sar.sar_id },
          { key: 'case_id', label: 'Case ID', value: sar.case_id },
          { key: 'customer_id', label: 'Customer ID', value: sar.customer_id },
          { key: 'alert_id', label: 'Alert ID', value: sar.alert_id },
          { key: 'evidence_ids_used', label: 'Evidence IDs used', value: sar.evidence_ids_used },
          { key: 'fincen_sources_used', label: 'FinCEN sources used', value: sar.fincen_sources_used },
        ]}
        links={LINKS}
      />

      <div>
        <h3 className="mb-2 text-sm font-semibold text-ink">Narrative (draft)</h3>
        {sar.narrative ? (
          <div className="whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-800">{sar.narrative}</div>
        ) : (
          <p className="text-sm text-slate-400">No narrative returned.</p>
        )}
      </div>

      <JsonBlock data={sar} summary="Full response" />
    </div>
  );
}
