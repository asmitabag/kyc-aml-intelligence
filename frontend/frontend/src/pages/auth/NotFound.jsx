import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface p-6">
      <div className="panel max-w-md p-8 text-center">
        <p className="tnum text-4xl font-semibold text-indigo-600">404</p>
        <h1 className="mt-2 text-xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-slate-500">That address doesn't exist in this application.</p>
        <Link to="/" className="btn-primary mt-6">
          Back to start
        </Link>
      </div>
    </div>
  );
}
