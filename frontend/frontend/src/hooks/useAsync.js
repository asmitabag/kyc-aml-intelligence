import { useCallback, useEffect, useRef, useState } from 'react';
import { normalizeError } from '../utils/errors';

// Runs an async loader and tracks { data, error, loading }.
// `enabled: false` skips loading (e.g. waiting for a selection).
export function useAsync(loader, deps = [], { enabled = true } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: enabled });
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const runId = useRef(0);

  const run = useCallback(async () => {
    const id = ++runId.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await loaderRef.current();
      if (id === runId.current) setState({ data, error: null, loading: false });
      return data;
    } catch (e) {
      if (id === runId.current) setState({ data: null, error: normalizeError(e), loading: false });
      return null;
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      setState({ data: null, error: null, loading: false });
      return undefined;
    }
    run();
    return () => {
      runId.current += 1;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps]);

  return { ...state, reload: run };
}
