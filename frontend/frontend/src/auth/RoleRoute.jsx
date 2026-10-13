import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './AuthProvider';

// UX guard only. The backend must enforce the same rule on every request.
export default function RoleRoute({ allow }) {
  const { role } = useAuth();
  if (!allow.includes(role)) return <Navigate to="/access-denied" replace />;
  return <Outlet />;
}
