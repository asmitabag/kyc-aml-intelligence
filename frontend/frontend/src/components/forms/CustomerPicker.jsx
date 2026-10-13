import { useAsync } from '../../hooks/useAsync';
import { analystService } from '../../services/analystService';

// Analyst-only helper: pick a customer from the directory (type to filter) or paste an ID.
export default function CustomerPicker({ value, onChange, label = 'Customer', id = 'customer-picker' }) {
  const { data, error } = useAsync(() => analystService.listCustomers(), []);
  const list = data || [];
  return (
    <div>
      <label htmlFor={id} className="label">{label}</label>
      <input
        id={id}
        list={`${id}-list`}
        value={value}
        onChange={(e) => onChange(e.target.value.trim())}
        placeholder="Type a name or paste a customer ID"
        className="input"
        autoComplete="off"
      />
      <datalist id={`${id}-list`}>
        {list.map((c) => (
          <option key={c.customer_id} value={c.customer_id}>{c.full_name}</option>
        ))}
      </datalist>
      {error && <p className="mt-1 text-xs text-amber-600">Directory unavailable ({error.message}). You can still paste a customer ID.</p>}
    </div>
  );
}
