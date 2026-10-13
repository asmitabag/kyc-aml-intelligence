import { useEffect, useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useOperationSchema } from '../../hooks/useOperationSchema';
import { normalizeError } from '../../utils/errors';
import { titleCase } from '../../utils/formatters';
import Notice from '../common/Notice';
import ConfirmDialog from '../common/ConfirmDialog';
import { PanelSkeleton } from '../common/Skeleton';

const LONG_TEXT = /(narrative|rationale|notes?|description|comment|reason|explanation|feedback|summary|message)/i;

function initialValue(field, initial) {
  if (initial && initial[field.name] !== undefined && initial[field.name] !== null) {
    const v = initial[field.name];
    return field.type === 'array' && Array.isArray(v) ? v.join(', ') : field.type === 'object' ? JSON.stringify(v, null, 2) : v;
  }
  if (field.default !== undefined && field.default !== null) {
    return field.type === 'array' && Array.isArray(field.default)
      ? field.default.join(', ')
      : field.type === 'object'
        ? JSON.stringify(field.default, null, 2)
        : field.default;
  }
  return field.type === 'boolean' ? false : '';
}

function toIsoIfDateTime(field, raw) {
  if (field.format === 'date-time') {
    const d = new Date(raw);
    return Number.isNaN(d.getTime()) ? raw : d.toISOString();
  }
  return raw;
}

// Converts one field's raw input into the API value. Throws Error(message) on invalid input.
function coerce(field, raw) {
  if (field.type === 'boolean') return !!raw;
  if (raw === '' || raw === undefined || raw === null) return undefined;
  switch (field.type) {
    case 'integer':
    case 'number': {
      const n = Number(raw);
      if (Number.isNaN(n)) throw new Error('Enter a valid number');
      if (field.type === 'integer' && !Number.isInteger(n)) throw new Error('Enter a whole number');
      if (field.minimum !== undefined && n < field.minimum) throw new Error(`Must be at least ${field.minimum}`);
      if (field.maximum !== undefined && n > field.maximum) throw new Error(`Must be at most ${field.maximum}`);
      return n;
    }
    case 'array': {
      const text = String(raw).trim();
      if (text.startsWith('[')) {
        try {
          return JSON.parse(text);
        } catch {
          throw new Error('Enter a comma-separated list or valid JSON');
        }
      }
      const parts = text.split(',').map((p) => p.trim()).filter(Boolean);
      if (field.itemType === 'integer' || field.itemType === 'number') {
        const nums = parts.map(Number);
        if (nums.some(Number.isNaN)) throw new Error('All items must be numbers');
        return nums;
      }
      return parts;
    }
    case 'object':
      try {
        return JSON.parse(raw);
      } catch {
        throw new Error('Enter valid JSON');
      }
    default: {
      const s = String(raw);
      if (field.minLength !== undefined && s.length < field.minLength) throw new Error(`Must be at least ${field.minLength} characters`);
      if (field.maxLength !== undefined && s.length > field.maxLength) throw new Error(`Must be at most ${field.maxLength} characters`);
      if (field.pattern) {
        try {
          if (!new RegExp(field.pattern).test(s)) throw new Error('Does not match the required format');
        } catch (e) {
          if (e.message === 'Does not match the required format') throw e;
        }
      }
      return toIsoIfDateTime(field, s);
    }
  }
}

function inputType(field) {
  const n = field.name.toLowerCase();
  if (field.format === 'password' || field.writeOnly || n.includes('password')) return 'password';
  if (field.format === 'email' || n === 'email' || n.endsWith('_email')) return 'email';
  if (field.format === 'date-time') return 'datetime-local';
  if (field.format === 'date') return 'date';
  if (field.format === 'uri') return 'url';
  return 'text';
}

function FieldControl({ field, value, error, onChange, disabled }) {
  const id = `f-${field.name}`;
  const label = field.title && field.title.toLowerCase() !== field.name.replace(/_/g, ' ') ? field.title : titleCase(field.name);
  const describedBy = [error ? `${id}-err` : null, field.description ? `${id}-hint` : null].filter(Boolean).join(' ') || undefined;
  const common = { id, disabled, 'aria-invalid': !!error, 'aria-describedby': describedBy, 'aria-required': field.required };
  const cls = `input ${error ? 'input-error' : ''}`;

  let control;
  if (field.type === 'boolean') {
    control = (
      <label className="flex items-center gap-2 text-sm text-slate-700">
        <input type="checkbox" {...common} checked={!!value} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4 rounded border-slate-300 text-indigo-600" />
        {label}
      </label>
    );
  } else if (field.enum) {
    control = (
      <select {...common} value={value} onChange={(e) => onChange(e.target.value)} className={cls}>
        <option value="">{field.required ? 'Select…' : 'Not set'}</option>
        {field.enum.map((o) => (
          <option key={String(o)} value={o}>
            {String(o)}
          </option>
        ))}
      </select>
    );
  } else if (field.type === 'object' || (field.type === 'array' && field.itemType === 'object')) {
    control = <textarea {...common} rows={4} value={value} onChange={(e) => onChange(e.target.value)} className={`${cls} font-mono text-xs`} placeholder="JSON" spellCheck={false} />;
  } else if (field.type === 'string' && (LONG_TEXT.test(field.name) || (field.maxLength && field.maxLength > 200))) {
    control = <textarea {...common} rows={4} value={value} onChange={(e) => onChange(e.target.value)} className={cls} />;
  } else if (field.type === 'integer' || field.type === 'number') {
    control = <input {...common} type="number" step={field.type === 'integer' ? '1' : 'any'} value={value} onChange={(e) => onChange(e.target.value)} className={cls} />;
  } else if (field.type === 'array') {
    control = <input {...common} type="text" value={value} onChange={(e) => onChange(e.target.value)} className={cls} placeholder="Comma-separated values" />;
  } else {
    const t = inputType(field);
    control = (
      <input
        {...common}
        type={t}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cls}
        autoComplete={t === 'password' ? (field.name.toLowerCase().includes('new') || field.name === 'password' ? 'current-password' : 'off') : t === 'email' ? 'email' : 'off'}
      />
    );
  }

  return (
    <div>
      {field.type !== 'boolean' && (
        <label htmlFor={id} className="label">
          {label}
          {field.required && <span className="ml-0.5 text-red-500" aria-hidden="true">*</span>}
        </label>
      )}
      {control}
      {field.description && (
        <p id={`${id}-hint`} className="mt-1 text-xs text-slate-500">
          {field.description}
        </p>
      )}
      {error && (
        <p id={`${id}-err`} className="mt-1 text-xs font-medium text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

/**
 * Form generated from the backend's own OpenAPI request schema.
 *
 * Props
 *  specPath / method  – the OpenAPI path template, e.g. '/api/v1/alerts/{alert_id}/status'
 *  onSubmit(payload)  – async; receives the validated JSON body (undefined if the endpoint has no body)
 *  lockedValues       – fields forced by the app (e.g. customer_id from the session) and hidden from the user
 *  hiddenFields       – schema fields to omit
 *  initialValues      – prefilled values
 *  fallbackFields     – used ONLY if the schema can't be read; otherwise a raw JSON editor is shown
 *  confirm            – { title, message } to ask for confirmation before sending
 */
export default function SchemaForm({
  specPath,
  method = 'post',
  onSubmit,
  onSuccess,
  lockedValues = {},
  hiddenFields = [],
  initialValues,
  fallbackFields,
  submitLabel = 'Submit',
  confirm,
  onCancel,
}) {
  const { status, info, reason } = useOperationSchema(specPath, method);

  const usingFallback = status === 'unavailable' && !!fallbackFields;
  const fields = useMemo(() => {
    const base = status === 'ready' ? info?.fields : usingFallback ? fallbackFields : null;
    if (!base) return null;
    const locked = Object.keys(lockedValues);
    return base.filter((f) => !hiddenFields.includes(f.name) && !locked.includes(f.name));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, info, usingFallback, fallbackFields, hiddenFields.join('|'), Object.keys(lockedValues).join('|')]);

  // A locked value is only sent if the backend schema defines that field
  // (or we have no schema to check against), so we never send unknown fields.
  const applicableLocked = () => {
    if (status === 'ready' && info?.fields) {
      const names = new Set(info.fields.map((f) => f.name));
      return Object.fromEntries(Object.entries(lockedValues).filter(([k]) => names.has(k)));
    }
    return lockedValues;
  };

  const [values, setValues] = useState({});
  const [json, setJson] = useState('{\n  \n}');
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState(null);

  useEffect(() => {
    if (!fields) return;
    const next = {};
    fields.forEach((f) => {
      next[f.name] = initialValue(f, initialValues);
    });
    setValues(next);
    setErrors({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fields]);

  const buildPayload = () => {
    const payload = {};
    const errs = {};
    (fields || []).forEach((f) => {
      try {
        const v = coerce(f, values[f.name]);
        if (v === undefined) {
          if (f.required) errs[f.name] = 'This field is required';
        } else {
          payload[f.name] = v;
        }
      } catch (e) {
        errs[f.name] = e.message;
      }
    });
    return { payload: { ...payload, ...applicableLocked() }, errs };
  };

  const send = async (payload) => {
    setBusy(true);
    setFormError(null);
    try {
      const result = await onSubmit(payload);
      onSuccess?.(result, payload);
    } catch (e) {
      const err = normalizeError(e);
      setFormError(err);
      if (err.fieldErrors && Object.keys(err.fieldErrors).length) setErrors((p) => ({ ...p, ...err.fieldErrors }));
    } finally {
      setBusy(false);
      setPending(null);
    }
  };

  const submit = (e) => {
    e.preventDefault();
    setFormError(null);

    let payload;
    if (info && info.hasOperation && !info.hasBody) {
      payload = undefined;
    } else if (fields) {
      const { payload: p, errs } = buildPayload();
      setErrors(errs);
      if (Object.keys(errs).length) return;
      payload = p;
    } else {
      try {
        payload = { ...JSON.parse(json), ...applicableLocked() };
      } catch {
        setErrors({ __json: 'Enter valid JSON' });
        return;
      }
      setErrors({});
    }

    if (confirm) setPending({ payload });
    else send(payload);
  };

  if (status === 'loading') return <PanelSkeleton lines={4} />;

  const noBody = info?.hasOperation && !info.hasBody;
  const multipart = info?.hasBody && info.contentType !== 'application/json';

  return (
    <form onSubmit={submit} noValidate className="space-y-4">
      {usingFallback && (
        <Notice tone="warn" title="Using default fields">
          {reason} These fields are the expected defaults and are not verified against the backend schema.
        </Notice>
      )}

      {multipart && (
        <Notice tone="warn" title="Unsupported request format">
          This endpoint expects <code>{info.contentType}</code>, which this form does not send. It is not integrated until the backend contract is confirmed.
        </Notice>
      )}

      {!multipart && fields && fields.length === 0 && !noBody && Object.keys(lockedValues).length === 0 && (
        <p className="text-sm text-slate-500">This endpoint does not define any editable fields.</p>
      )}

      {!multipart && fields && fields.map((f) => (
        <FieldControl
          key={f.name}
          field={f}
          value={values[f.name] ?? (f.type === 'boolean' ? false : '')}
          error={errors[f.name]}
          disabled={busy}
          onChange={(v) => {
            setValues((s) => ({ ...s, [f.name]: v }));
            if (errors[f.name]) setErrors((s) => ({ ...s, [f.name]: undefined }));
          }}
        />
      ))}

      {!multipart && !fields && !noBody && (
        <div>
          <Notice tone="warn" title="Schema unavailable — enter the request body as JSON">
            {reason || 'This endpoint does not describe its fields in OpenAPI.'}
          </Notice>
          <label htmlFor="raw-json" className="label mt-3">
            Request body (JSON)
          </label>
          <textarea id="raw-json" rows={8} value={json} onChange={(e) => setJson(e.target.value)} className={`input font-mono text-xs ${errors.__json ? 'input-error' : ''}`} spellCheck={false} />
          {errors.__json && <p className="mt-1 text-xs font-medium text-red-600">{errors.__json}</p>}
        </div>
      )}

      {formError && (
        <Notice tone="error" title={formError.status ? `Request failed (HTTP ${formError.status})` : 'Request failed'}>
          {formError.message}
        </Notice>
      )}

      {!multipart && (
        <div className="flex justify-end gap-2 pt-1">
          {onCancel && (
            <button type="button" className="btn-secondary" onClick={onCancel} disabled={busy}>
              Cancel
            </button>
          )}
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
            {busy ? 'Sending…' : submitLabel}
          </button>
        </div>
      )}

      {confirm && (
        <ConfirmDialog
          open={!!pending}
          title={confirm.title}
          message={confirm.message}
          busy={busy}
          confirmLabel={submitLabel}
          onCancel={() => setPending(null)}
          onConfirm={() => send(pending.payload)}
        />
      )}
    </form>
  );
}
