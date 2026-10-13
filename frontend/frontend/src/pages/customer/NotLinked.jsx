import EmptyState from '../../components/common/EmptyState';
import { UserX } from 'lucide-react';

export default function NotLinked() {
  return (
    <div className="panel">
      <EmptyState
        icon={UserX}
        title="Your account isn't linked to a customer profile"
        description="The server didn't return a customer ID for your login. Please contact support so your profile can be linked."
      />
    </div>
  );
}
