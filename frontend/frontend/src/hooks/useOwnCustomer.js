import { useAuth } from '../auth/AuthProvider';

// The customer id ALWAYS comes from the authenticated session (/auth/me),
// never from a URL, form field or other user-controlled input.
export function useOwnCustomer() {
  const { customerId, user } = useAuth();
  return { customerId, user, linked: !!customerId };
}
