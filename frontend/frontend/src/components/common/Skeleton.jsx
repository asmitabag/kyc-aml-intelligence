export default function Skeleton({ className = 'h-4 w-full' }) {
  return <div aria-hidden="true" className={`animate-pulse rounded bg-slate-200 ${className}`} />;
}

export function TableSkeleton({ rows = 6, cols = 5 }) {
  return (
    <div role="status" aria-label="Loading table" className="divide-y divide-slate-100">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 px-4 py-3.5">
          {Array.from({ length: cols }).map((__, c) => (
            <Skeleton key={c} className={`h-4 ${c === 0 ? 'w-28' : 'flex-1'}`} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function PanelSkeleton({ lines = 4 }) {
  return (
    <div role="status" aria-label="Loading" className="space-y-3 p-5">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-4 ${i === 0 ? 'w-1/3' : 'w-full'}`} />
      ))}
    </div>
  );
}
