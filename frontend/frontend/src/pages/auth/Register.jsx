import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import AuthShell from './AuthShell';
import SchemaForm from '../../components/forms/SchemaForm';
import { authService } from '../../services/authService';

// VERIFY: used only if /openapi.json can't be read. Confirm against RegisterRequest.
const REGISTER_FALLBACK = [
  { name: 'full_name', type: 'string', required: true, title: 'Full name' },
  { name: 'email', type: 'string', format: 'email', required: true, title: 'Email' },
  { name: 'password', type: 'string', format: 'password', required: true, title: 'Password' },
];

// A user can never pick a role here; any role-like field is stripped before sending,
// and the backend must assign "customer" itself.
const ROLE_FIELDS = ['role', 'roles', 'is_admin', 'is_superuser', 'customer_id'];

export default function Register() {
  const navigate = useNavigate();

  return (
    <AuthShell
      title="Create your account"
      subtitle="Registration creates a customer account and your customer profile."
      aside={{ heading: 'Get verified in a few minutes.', body: 'Create an account, submit your details, and track your verification status.' }}
      footer={
        <>
          Already registered? <Link to="/login" className="font-medium text-indigo-600 hover:underline">Sign in</Link>
        </>
      }
    >
      <SchemaForm
        specPath="/api/v1/auth/register"
        method="post"
        fallbackFields={REGISTER_FALLBACK}
        hiddenFields={ROLE_FIELDS}
        submitLabel="Create account"
        onSubmit={(payload) => authService.register(payload)}
        onSuccess={(_res, payload) => {
          toast.success('Account created. Sign in to continue.');
          navigate('/login', { replace: true, state: { email: payload?.email } });
        }}
      />
    </AuthShell>
  );
}
