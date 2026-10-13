import { AlertTriangle, Lock, ServerCrash, WifiOff } from 'lucide-react';

// Shows the real API error. A 403 is presented as "access denied" rather than a failure.
export default function ErrorState({ error, title, onRetry, compact = false }) {
  const status = error?.status;
  let Icon = AlertTriangle;
  let heading = title || 'Something went wrong';
  let tone = 'text-red-600 bg-red-50';

  if (status === 403) {
    Icon = Lock;
    heading = 'Access denied';
    tone = 'text-amber-600 bg-amber-50';
  } else if (status === 503) {
    Icon = ServerCrash;
    heading = 'Service unavailable';
    tone = 'text-amber-600 bg-amber-50';
  } else if (error?.isNetwork) {
    Icon = WifiOff;
    heading = 'Cannot reach the API';
  } else if (status === 404) {
    heading = title || 'Not found';
  }

  return (
    <div role="alert" className={`flex flex-col items-center text-center ${compact ? 'px-4 py-6' : 'px-6 py-12'}`}>
      <div className={`mb-3 rounded-full p-3 ${tone}`}>
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>
      <h3 className="text-sm font-semibold text-slate-800">{heading}</h3>
      <p className="mt-1 max-w-md text-sm text-slate-500">{error?.message || 'An unexpected error occurred.'}</p>
      {status ? <p className="mt-1 text-xs text-slate-400">HTTP {status}</p> : null}
      {onRetry && status !== 403 && (
        <button type="button" onClick={onRetry} className="btn-secondary btn-sm mt-4">
          Try again
        </button>
      )}
    </div>
  );
}
