import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function AppLayout({ nav, portalLabel, showHealth = false, maxWidth = 'max-w-7xl' }) {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => setOpen(false), [pathname]);

  return (
    <div className="flex min-h-screen bg-surface">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:shadow">
        Skip to content
      </a>
      <Sidebar items={nav} portalLabel={portalLabel} open={open} onClose={() => setOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenu={() => setOpen(true)} showHealth={showHealth} />
        <main id="main" className={`mx-auto w-full flex-1 px-4 py-6 sm:px-6 lg:px-8 ${maxWidth}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
