import { Link } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { useAuth, homePathForRole } from '../../auth/AuthProvider';

export default function AccessDenied() {
  const { role, logout } = useAuth();
  const home = homePathForRole(role);
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface p-6">
      <div className="panel max-w-md p-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-600">
          <ShieldAlert className="h-6 w-6" aria-hidden="true" />
        </div>
        <h1 className="text-xl font-semibold">Access denied</h1>
        <p className="mt-2 text-sm text-slate-500">
          Your account{role ? ` (${role})` : ''} doesn't have permission to open that page.
        </p>
        <div className="mt-6 flex justify-center gap-2">
          {home !== '/access-denied' && (
            <Link to={home} className="btn-primary">
              Go to my portal
            </Link>
          )}
          <button type="button" onClick={logout} className="btn-secondary">
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
