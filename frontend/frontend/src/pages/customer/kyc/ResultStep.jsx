import { useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { computeKycScore, THRESHOLDS } from './scoring';

const DECISION = {
  verified: { label: 'Verified', cls: 'bg-emerald-50 text-emerald-700' },
  manual_review: { label: 'Needs manual review', cls: 'bg-amber-50 text-amber-700' },
  rejected: { label: 'Not verified', cls: 'bg-red-50 text-red-700' },
};

export default function ResultStep({ fields, ocr, live, onSubmit, onRestart }) {
  const result = useMemo(
    () =>
      computeKycScore({
        faceDistance: live.faceDistance,
        liveness: live.liveness,
        docPresenceRatio: live.docPresenceRatio,
        ocrConfidence: ocr.confidence,
        fields,
      }),
    [fields, ocr, live]
  );
  const [submitting, setSubmitting] = useState(false);
  const d = DECISION[result.decision];

  const submit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(result);
    } catch (e) {
      toast.error(e?.message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <div className="text-4xl font-semibold text-ink">{result.total}<span className="text-lg text-slate-400"> / 100</span></div>
          <p className="mt-1 text-xs text-slate-500">Verified at {THRESHOLDS.verified}+, manual review at {THRESHOLDS.review}+</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-medium ${d.cls}`}>{d.label}</span>
      </div>

      <ul className="space-y-3">
        {result.parts.map((p) => (
          <li key={p.key}>
            <div className="flex justify-between text-sm">
              <span className="text-ink">{p.label}</span>
              <span className="text-slate-500">{p.points} / {p.weight}</span>
            </div>
            <div className="mt-1 h-1.5 rounded-full bg-slate-100" role="presentation">
              <div className="h-full rounded-full bg-ink" style={{ width: `${p.ratio * 100}%` }} />
            </div>
            <p className="mt-1 text-xs text-slate-500">{p.detail}</p>
          </li>
        ))}
      </ul>

      {result.flags.length > 0 && (
        <ul className="space-y-1 rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
          {result.flags.map((f) => <li key={f}>{f}</li>)}
        </ul>
      )}

      <div className="flex gap-3">
        <button type="button" onClick={onRestart} className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-ink">Start over</button>
        <button type="button" onClick={submit} disabled={submitting} className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {submitting ? 'Submitting…' : 'Submit for verification'}
        </button>
      </div>
    </div>
  );
}