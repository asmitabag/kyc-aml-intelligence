import { NavLink } from 'react-router-dom';
import { LogOut, ShieldCheck, X } from 'lucide-react';
import { useAuth } from '../../auth/AuthProvider';

export default function Sidebar({ items, portalLabel, open, onClose }) {
  const { user, logout } = useAuth();

  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-navy-950/60 lg:hidden" onClick={onClose} aria-hidden="true" />}
      <aside
        aria-label="Main navigation"
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-navy-900 text-slate-300 transition-transform duration-200 lg:static lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex h-16 items-center justify-between px-5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/15 text-indigo-300">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold text-white">KYC·AML Intelligence</p>
              <p className="text-xs text-slate-400">{portalLabel}</p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="rounded p-1 text-slate-400 hover:text-white lg:hidden" aria-label="Close navigation">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-3">
          {items.map((item) =>
            item.divider ? (
              <p key={item.divider} className="px-3 pb-1 pt-4 text-xs font-medium text-slate-500">
                {item.divider}
              </p>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                    isActive ? 'bg-indigo-500/15 font-medium text-white' : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
                  }`
                }
              >
                <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                {item.label}
              </NavLink>
            ),
          )}
        </nav>

        <div className="border-t border-white/10 p-3">
          <div className="mb-2 px-2">
            <p className="truncate text-sm text-slate-200">{user?.email}</p>
            <p className="text-xs capitalize text-slate-500">{user?.role}</p>
          </div>
          <button type="button" onClick={logout} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5 hover:text-white">
            <LogOut className="h-4 w-4" aria-hidden="true" /> Sign out
          </button>
        </div>
      </aside>
    </>
  );
}
