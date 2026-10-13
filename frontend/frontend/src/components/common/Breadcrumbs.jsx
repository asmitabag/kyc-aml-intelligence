import { Link, useLocation } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { titleCase } from '../../utils/formatters';

const LABELS = { aml: 'AML analysis', sar: 'SAR workspace', kyc: 'KYC verification', risk: 'Risk assessment' };

export default function Breadcrumbs() {
  const { pathname } = useLocation();
  const parts = pathname.split('/').filter(Boolean);
  if (parts.length < 2) return null;

  const crumbs = parts.map((seg, i) => ({
    label: LABELS[seg] || (i >= 2 ? decodeURIComponent(seg) : titleCase(seg)),
    to: '/' + parts.slice(0, i + 1).join('/'),
    // /analyst and /customer have no page of their own
    linkable: i > 0 && i < parts.length - 1,
  }));

  return (
    <nav aria-label="Breadcrumb" className="min-w-0">
      <ol className="flex items-center gap-1 text-sm text-slate-500">
        {crumbs.map((c, i) => (
          <li key={c.to} className="flex min-w-0 items-center gap-1">
            {i > 0 && <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-300" aria-hidden="true" />}
            {c.linkable ? (
              <Link to={c.to} className="truncate hover:text-indigo-600">
                {c.label}
              </Link>
            ) : (
              <span className={`truncate ${i === crumbs.length - 1 ? 'font-medium text-slate-800' : ''}`} aria-current={i === crumbs.length - 1 ? 'page' : undefined}>
                {c.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
