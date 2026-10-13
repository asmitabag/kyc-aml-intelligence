import { AlertTriangle, Info } from 'lucide-react';

const TONES = {
  info: { cls: 'border-indigo-200 bg-indigo-50 text-indigo-900', Icon: Info },
  warn: { cls: 'border-amber-200 bg-amber-50 text-amber-900', Icon: AlertTriangle },
  error: { cls: 'border-red-200 bg-red-50 text-red-900', Icon: AlertTriangle },
};

export default function Notice({ tone = 'info', title, children, className = '' }) {
  const { cls, Icon } = TONES[tone];
  return (
    <div role={tone === 'error' ? 'alert' : 'note'} className={`flex items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-sm ${cls} ${className}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div className="min-w-0">
        {title && <p className="font-semibold">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  );
}
