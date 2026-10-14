import { ID_TYPES, validateFields } from './documentParser';

const input = 'w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-ink focus:border-slate-400 focus:outline-none';

export default function DetailsStep({ thumb, ocrConfidence, fields, onChange, onBack, onNext }) {
  const v = validateFields(fields);
  const set = (k) => (e) => onChange({ ...fields, [k]: e.target.value });
  const bad = (ok) => (ok ? '' : 'border-red-300');

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        We read these from your document (text confidence {Math.round(ocrConfidence)}%). Fix anything that looks wrong.
      </p>
      <div className="grid gap-4 sm:grid-cols-[160px_1fr]">
        {thumb && <img src={thumb} alt="Captured document" className="w-full rounded-lg border border-slate-200 object-cover" />}
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm sm:col-span-2">
            <span className="mb-1 block text-slate-500">Full name</span>
            <input className={`${input} ${bad(v.nameOk)}`} value={fields.full_name} onChange={set('full_name')} />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-500">Date of birth</span>
            <input type="date" className={`${input} ${bad(v.dobOk && v.ageOk)}`} value={fields.date_of_birth} onChange={set('date_of_birth')} />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-500">Document type</span>
            <select className={input} value={fields.id_type} onChange={set('id_type')}>
              {Object.entries(ID_TYPES).map(([k, t]) => <option key={k} value={k}>{t.label}</option>)}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-500">Document number</span>
            <input className={`${input} ${bad(v.idOk)}`} value={fields.id_number} onChange={set('id_number')} />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-500">Expiry date (if any)</span>
            <input type="date" className={`${input} ${bad(v.notExpired)}`} value={fields.id_expiry} onChange={set('id_expiry')} />
          </label>
        </div>
      </div>
      <div className="flex gap-3">
        <button type="button" onClick={onBack} className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-ink">Rescan document</button>
        <button type="button" onClick={onNext} className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white">Continue to face check</button>
      </div>
    </div>
  );
}
