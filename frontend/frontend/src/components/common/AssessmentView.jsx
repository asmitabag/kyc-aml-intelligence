import { Eye } from 'lucide-react';
import DetailList from './DetailList';
import FactorsList from './FactorsList';
import RiskBadge from './RiskBadge';
import StatusBadge from './StatusBadge';
import Notice from './Notice';
import { formatScore } from '../../utils/formatters';

// Full analyst view of a risk assessment. Values are displayed exactly as the backend supplied them.
export default function AssessmentView({ a }) {
  if (!a) return null;
  const scores = [
    ['kyc_risk', 'KYC risk'],
    ['aml_risk', 'AML risk'],
    ['fused_risk', 'Fused risk'],
    ['gnn_risk', 'GNN risk'],
    ['xgboost_risk', 'XGBoost risk'],
    ['final_risk', 'Final risk'],
    ['uncertainty', 'Uncertainty'],
  ];

  return (
    <div className="space-y-5">
      {a.human_review_required && (
        <Notice tone="warn" title="Human review required">
          The backend flagged this assessment for manual review before any decision is made.
        </Notice>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm text-slate-500">Risk level</span>
        <RiskBadge level={a.risk_level} />
        <span className="text-sm text-slate-500">Status</span>
        <StatusBadge value={a.status} />
        {a.priority !== undefined && a.priority !== null && (
          <>
            <span className="text-sm text-slate-500">Priority</span>
            <span className="tnum rounded bg-slate-100 px-1.5 py-0.5 text-sm font-medium">{String(a.priority)}</span>
          </>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {scores.map(([key, label]) => (
          <div key={key} className="rounded-lg border border-slate-200 px-3 py-2.5">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="tnum mt-0.5 text-lg font-semibold text-ink">{formatScore(a[key])}</p>
          </div>
        ))}
      </div>

      <DetailList
        items={[
          { key: 'assessment_id', label: 'Assessment ID', value: a.assessment_id },
          { key: 'customer_id', label: 'Customer ID', value: a.customer_id },
          { key: 'case_id', label: 'Case ID', value: a.case_id },
          { key: 'suspected_typology', label: 'Suspected typology', value: a.suspected_typology },
          { key: 'gnn_model_version', label: 'GNN model version', value: a.gnn_model_version },
          { key: 'xgboost_model_version', label: 'XGBoost model version', value: a.xgboost_model_version },
        ]}
      />

      <div>
        <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-ink">
          <Eye className="h-4 w-4 text-slate-400" aria-hidden="true" /> Top risk factors
        </h3>
        <FactorsList factors={a.top_risk_factors} />
      </div>
    </div>
  );
}
