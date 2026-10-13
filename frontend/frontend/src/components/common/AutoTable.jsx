import { useMemo } from 'react';
import DataTable from './DataTable';
import Value from './Value';
import { titleCase } from '../../utils/formatters';

// Builds columns from the keys the API actually returned, so schemas that
// aren't fully known (cases, feedback) are displayed truthfully instead of guessed.
export default function AutoTable({ rows, preferred = [], exclude = [], maxColumns = 7, links, ...rest }) {
  const columns = useMemo(() => {
    const first = (rows || [])[0];
    if (!first) return [];
    const keys = Object.keys(first).filter((k) => !exclude.includes(k));
    const primitive = keys.filter((k) => first[k] === null || typeof first[k] !== 'object');
    const ordered = [...preferred.filter((k) => primitive.includes(k)), ...primitive.filter((k) => !preferred.includes(k))].slice(0, maxColumns);
    return ordered.map((key) => ({
      key,
      header: titleCase(key),
      render: (row) => <Value name={key} value={row[key]} links={links} />,
    }));
  }, [rows, preferred, exclude, maxColumns, links]);

  return <DataTable columns={columns} rows={rows} {...rest} />;
}
