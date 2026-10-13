import Value from './Value';
import { titleCase } from '../../utils/formatters';

// items: [{ key, label?, value }]  OR pass `data` to render every field of an object.
export default function DetailList({ items, data, exclude = [], links, columns = 2 }) {
  const rows = items || Object.entries(data || {}).filter(([k]) => !exclude.includes(k)).map(([key, value]) => ({ key, value }));
  const grid = columns === 1 ? '' : 'sm:grid-cols-2';
  return (
    <dl className={`grid grid-cols-1 gap-x-8 gap-y-4 ${grid}`}>
      {rows.map((r) => (
        <div key={r.key} className="min-w-0">
          <dt className="text-xs font-medium text-slate-500">{r.label || titleCase(r.key)}</dt>
          <dd className="mt-0.5 break-words text-sm text-ink">
            {r.render ? r.render : <Value name={r.key} value={r.value} links={links} />}
          </dd>
        </div>
      ))}
    </dl>
  );
}
