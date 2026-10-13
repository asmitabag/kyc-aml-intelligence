import { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight } from 'lucide-react';
import { TableSkeleton } from './Skeleton';
import ErrorState from './ErrorState';
import EmptyState from './EmptyState';

// columns: [{ key, header, render?(row), sortValue?(row), className?, sortable? }]
export default function DataTable({
  columns,
  rows,
  loading,
  error,
  onRetry,
  onRowClick,
  rowKey,
  pageSize = 15,
  empty,
  caption,
}) {
  const [sort, setSort] = useState({ key: null, dir: 'asc' });
  const [page, setPage] = useState(0);

  useEffect(() => setPage(0), [rows]);

  const sorted = useMemo(() => {
    if (!rows) return [];
    if (!sort.key) return rows;
    const col = columns.find((c) => c.key === sort.key);
    const val = (r) => (col?.sortValue ? col.sortValue(r) : r[sort.key]);
    return [...rows].sort((a, b) => {
      const x = val(a);
      const y = val(b);
      if (x == null && y == null) return 0;
      if (x == null) return 1;
      if (y == null) return -1;
      const cmp = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true });
      return sort.dir === 'asc' ? cmp : -cmp;
    });
  }, [rows, sort, columns]);

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
  const current = Math.min(page, pageCount - 1);
  const visible = sorted.slice(current * pageSize, current * pageSize + pageSize);

  const toggleSort = (key) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }));

  return (
    <div className="panel overflow-hidden">
      {loading ? (
        <TableSkeleton cols={Math.min(columns.length, 6)} />
      ) : error ? (
        <ErrorState error={error} onRetry={onRetry} compact />
      ) : !rows || rows.length === 0 ? (
        empty || <EmptyState title="Nothing to show" description="No records were returned by the API." />
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              {caption && <caption className="sr-only">{caption}</caption>}
              <thead className="bg-slate-50/70">
                <tr>
                  {columns.map((c) => {
                    const sortable = c.sortable !== false;
                    const active = sort.key === c.key;
                    return (
                      <th
                        key={c.key}
                        scope="col"
                        aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                        className={`px-4 py-2.5 text-left text-xs font-medium text-slate-500 ${c.className || ''}`}
                      >
                        {sortable ? (
                          <button type="button" onClick={() => toggleSort(c.key)} className="inline-flex items-center gap-1 hover:text-slate-800">
                            {c.header}
                            {active && (sort.dir === 'asc' ? <ArrowUp className="h-3 w-3" aria-hidden="true" /> : <ArrowDown className="h-3 w-3" aria-hidden="true" />)}
                          </button>
                        ) : (
                          c.header
                        )}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visible.map((row, i) => (
                  <tr
                    key={rowKey ? rowKey(row) : i}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                    onKeyDown={onRowClick ? (e) => (e.key === 'Enter' ? onRowClick(row) : null) : undefined}
                    tabIndex={onRowClick ? 0 : undefined}
                    className={onRowClick ? 'cursor-pointer hover:bg-indigo-50/40 focus-visible:bg-indigo-50/60' : ''}
                  >
                    {columns.map((c) => (
                      <td key={c.key} className={`px-4 py-3 align-middle text-slate-700 ${c.className || ''}`}>
                        {c.render ? c.render(row) : row[c.key] ?? <span className="text-slate-400">—</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {sorted.length > pageSize && (
            <div className="flex items-center justify-between border-t border-slate-100 px-4 py-2.5 text-xs text-slate-500">
              <span className="tnum">
                {current * pageSize + 1}–{Math.min((current + 1) * pageSize, sorted.length)} of {sorted.length}
              </span>
              <div className="flex gap-1">
                <button type="button" className="btn-ghost btn-sm" onClick={() => setPage(current - 1)} disabled={current === 0} aria-label="Previous page">
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button type="button" className="btn-ghost btn-sm" onClick={() => setPage(current + 1)} disabled={current >= pageCount - 1} aria-label="Next page">
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
