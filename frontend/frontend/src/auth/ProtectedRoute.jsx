import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth, homePathForRole } from './AuthProvider';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

function FullScreen({ children }) {
  return <div className="flex min-h-screen items-center justify-center bg-surface p-6">{children}</div>;
}

// Requires an authenticated session. Redirects to /login otherwise.
export default function ProtectedRoute() {
  const { status, bootError, refresh } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return (
      <FullScreen>
        <LoadingState label="Restoring your session…" />
      </FullScreen>
    );
  }
  if (status === 'error') {
    return (
      <FullScreen>
        <div className="w-full max-w-md">
          <ErrorState error={bootError} title="Couldn't verify your session" onRetry={refresh} />
        </div>
      </FullScreen>
    );
  }
  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

// Login / register pages: signed-in users are sent to their own portal.
export function PublicRoute() {
  const { status, role } = useAuth();
  if (status === 'loading') {
    return (
      <FullScreen>
        <LoadingState label="Checking session…" />
      </FullScreen>
    );
  }
  if (status === 'authenticated') return <Navigate to={homePathForRole(role)} replace />;
  return <Outlet />;
}
