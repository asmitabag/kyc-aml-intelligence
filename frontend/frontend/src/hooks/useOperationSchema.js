import { useEffect, useState } from 'react';
import { loadSpec, describeRequestBody } from '../api/openapi';

// Looks up the real request-body schema for an endpoint from /openapi.json.
// status: 'loading' | 'ready' | 'unavailable'
export function useOperationSchema(path, method) {
  const [state, setState] = useState({ status: 'loading', info: null, reason: null });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading', info: null, reason: null });
    loadSpec()
      .then((spec) => {
        if (cancelled) return;
        const info = describeRequestBody(spec, path, method);
        if (!info.hasOperation) {
          setState({ status: 'unavailable', info, reason: `${method.toUpperCase()} ${path} was not found in the API's OpenAPI document.` });
        } else {
          setState({ status: 'ready', info, reason: null });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState({
            status: 'unavailable',
            info: null,
            reason: "Could not read the API's /openapi.json (it may be disabled on the server).",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [path, method]);

  return state;
}
