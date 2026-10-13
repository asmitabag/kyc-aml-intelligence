import { FileWarning } from 'lucide-react';

export default function DraftBanner({ className = '' }) {
  return (
    <div role="note" className={`flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-sm text-amber-900 ${className}`}>
      <FileWarning className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <p>
        <strong className="font-semibold">Draft — pending human review.</strong> This report has not been filed with any authority. A qualified analyst must verify every statement against the evidence before any filing decision.
      </p>
    </div>
  );
}
