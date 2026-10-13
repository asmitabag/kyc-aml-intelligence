import { Link, useLocation, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import AuthShell from './AuthShell';
import SchemaForm from '../../components/forms/SchemaForm';
import { useAuth, homePathForRole } from '../../auth/AuthProvider';

// Used only if /openapi.json can't be read. Matches the expected LoginRequest.
const LOGIN_FALLBACK = [
  { name: 'email', type: 'string', format: 'email', required: true, title: 'Email' },
  { name: 'password', type: 'string', format: 'password', required: true, title: 'Password' },
];

export default function Login({ portal }) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isAnalyst = portal === 'analyst';

  const handleLogin = (credentials) => login(credentials);

  const onSuccess = (me) => {
    // The role from the backend decides the destination, not the page the user logged in from.
    if (isAnalyst && me.role !== 'analyst') toast('This is a customer account — opening the customer portal.');
    if (!isAnalyst && me.role === 'analyst') toast('Analyst account detected — opening the analyst workspace.');
    const from = location.state?.from;
    const allowedFrom = from && from.startsWith(`/${me.role}`) ? from : null;
    navigate(allowedFrom || homePathForRole(me.role), { replace: true });
  };

  return (
    <AuthShell
      title={isAnalyst ? 'Analyst sign in' : 'Sign in'}
      subtitle={isAnalyst ? 'Use the credentials issued to you by your administrator.' : 'Access your accounts and verification status.'}
      aside={
        isAnalyst
          ? { heading: 'Investigate with evidence you can explain.', body: 'Alerts, cases, model explanations and SAR drafts in one workspace. Every report stays a draft until a human reviews it.' }
          : { heading: 'Know where your verification stands.', body: 'See your identity check, accounts and recent activity in one place.' }
      }
      footer={
        isAnalyst ? (
          <>
            Not an analyst? <Link to="/login" className="font-medium text-indigo-600 hover:underline">Customer sign in</Link>
          </>
        ) : (
          <>
            New here? <Link to="/register" className="font-medium text-indigo-600 hover:underline">Create an account</Link>
            <span className="mx-2 text-slate-300">|</span>
            <Link to="/analyst/login" className="font-medium text-slate-600 hover:underline">Analyst sign in</Link>
          </>
        )
      }
    >
      <SchemaForm
        specPath="/api/v1/auth/login"
        method="post"
        fallbackFields={LOGIN_FALLBACK}
        submitLabel="Sign in"
        onSubmit={handleLogin}
        onSuccess={onSuccess}
      />
    </AuthShell>
  );
}
