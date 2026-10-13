import { Menu } from 'lucide-react';
import Breadcrumbs from '../common/Breadcrumbs';
import HealthPill from './HealthPill';

export default function Topbar({ onMenu, showHealth }) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-6">
      <button type="button" onClick={onMenu} className="rounded-md p-2 text-slate-500 hover:bg-slate-100 lg:hidden" aria-label="Open navigation">
        <Menu className="h-5 w-5" />
      </button>
      <div className="min-w-0 flex-1">
        <Breadcrumbs />
      </div>
      {showHealth && <HealthPill />}
    </header>
  );
}
