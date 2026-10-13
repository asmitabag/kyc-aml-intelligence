import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authService } from '../services/authService';
import { tokenStore } from './tokenStore';
import { UNAUTHORIZED_EVENT } from '../api/client';

const AuthContext = createContext(null);

export function homePathForRole(role) {
  if (role === 'customer') return '/customer/dashboard';
  if (role === 'analyst') return '/analyst/dashboard';
  return '/access-denied';
}

// status: 'loading' | 'authenticated' | 'unauthenticated' | 'error'
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(tokenStore.get() ? 'loading' : 'unauthenticated');
  const [bootError, setBootError] = useState(null);

  const clear = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setBootError(null);
    setStatus('unauthenticated');
  }, []);

  // The role ALWAYS comes from the backend (/auth/me), never from storage.
  // Only the token is persisted, so editing browser storage cannot change a role.
  const restore = useCallback(async () => {
    if (!tokenStore.get()) {
      setStatus('unauthenticated');
      return;
    }
    setStatus('loading');
    try {
      const me = await authService.me();
      setUser(me);
      setBootError(null);
      setStatus('authenticated');
    } catch (e) {
      if (e.status === 401) {
        clear();
      } else {
        setBootError(e);
        setStatus('error');
      }
    }
  }, [clear]);

  useEffect(() => {
    restore();
  }, [restore]);

  // Any protected call that returns 401 clears the session globally.
  useEffect(() => {
    const onUnauthorized = () => {
      if (tokenStore.get()) clear();
    };
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, [clear]);

  const login = useCallback(async (credentials) => {
    const res = await authService.login(credentials);
    const token = res?.access_token;
    if (!token) throw new Error('The login response did not include an access_token.');
    tokenStore.set(token);
    try {
      // Re-validate with /auth/me so the role is authoritative.
      const me = await authService.me();
      setUser(me);
      setStatus('authenticated');
      return me;
    } catch (e) {
      tokenStore.clear();
      setStatus('unauthenticated');
      throw e;
    }
  }, []);

  const logout = useCallback(() => clear(), [clear]);

  const value = useMemo(
    () => ({
      user,
      status,
      bootError,
      role: user?.role ?? null,
      customerId: user?.customer_id ?? null,
      isAuthenticated: status === 'authenticated',
      login,
      logout,
      refresh: restore,
    }),
    [user, status, bootError, login, logout, restore],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
