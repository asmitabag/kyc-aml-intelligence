import { X } from 'lucide-react';

export default function FilterBar({ children, onReset, active }) {
  return (
    <div className="mb-4 flex flex-wrap items-end gap-3">
      {children}
      {onReset && active && (
        <button type="button" onClick={onReset} className="btn-ghost btn-sm">
          <X className="h-3.5 w-3.5" aria-hidden="true" /> Clear filters
        </button>
      )}
    </div>
  );
}

export function FilterSelect({ label, value, onChange, options, allLabel = 'All' }) {
  return (
    <label className="block min-w-[9rem] text-sm">
      <span className="mb-1 block text-xs font-medium text-slate-500">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input py-1.5">
        <option value="">{allLabel}</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}
