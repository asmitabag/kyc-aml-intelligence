import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { colorFor } from './palette';
import { titleCase } from '../../utils/formatters';

export default function DonutChart({ data, label = 'Distribution' }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  if (!total) return <p className="py-10 text-center text-sm text-slate-400">No data to chart yet.</p>;

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row">
      <div className="h-44 w-44 shrink-0" role="img" aria-label={`${label}: ${data.map((d) => `${titleCase(d.name)} ${d.value}`).join(', ')}`}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={52} outerRadius={78} paddingAngle={2} stroke="none">
              {data.map((d, i) => (
                <Cell key={d.name} fill={colorFor(d.name, i)} />
              ))}
            </Pie>
            <Tooltip formatter={(v, n) => [v, titleCase(n)]} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="w-full space-y-1.5 text-sm">
        {data.map((d, i) => (
          <li key={d.name} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: colorFor(d.name, i) }} aria-hidden="true" />
              {titleCase(d.name)}
            </span>
            <span className="tnum font-medium text-ink">{d.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
