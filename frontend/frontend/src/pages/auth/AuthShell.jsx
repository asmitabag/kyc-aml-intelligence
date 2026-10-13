import { ShieldCheck } from 'lucide-react';

export default function AuthShell({ title, subtitle, children, footer, aside }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <div className="relative hidden flex-col justify-between bg-navy-900 p-12 text-slate-300 lg:flex">
        <div className="flex items-center gap-2.5 text-white">
          <ShieldCheck className="h-6 w-6 text-indigo-300" aria-hidden="true" />
          <span className="text-lg font-semibold">KYC·AML Intelligence</span>
        </div>
        <div className="max-w-md">
          <h2 className="text-3xl font-semibold leading-tight text-white">{aside.heading}</h2>
          <p className="mt-4 text-slate-400">{aside.body}</p>
        </div>
        <p className="text-xs text-slate-500">Explainable identity screening and transaction monitoring.</p>
      </div>

      <div className="flex items-center justify-center bg-surface px-5 py-12">
        <div className="w-full max-w-md">
          <div className="mb-6 flex items-center gap-2 lg:hidden">
            <ShieldCheck className="h-6 w-6 text-indigo-600" aria-hidden="true" />
            <span className="font-semibold">KYC·AML Intelligence</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
          <div className="panel mt-6 p-6">{children}</div>
          <div className="mt-5 text-center text-sm text-slate-500">{footer}</div>
        </div>
      </div>
    </div>
  );
}
