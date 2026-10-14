// Turns raw OCR text into structured fields, and validates them.
// Tuned for Indian IDs (PAN, Aadhaar, passport, driving licence); extend ID_TYPES for others.

export const ID_TYPES = {
  pan: { label: 'PAN card', re: /^[A-Z]{5}\d{4}[A-Z]$/ },
  aadhaar: { label: 'Aadhaar', re: /^[2-9]\d{11}$/ },
  passport: { label: 'Passport', re: /^[A-PR-WY][1-9]\d{5}[1-9]$/ },
  driving_licence: { label: 'Driving licence', re: /^[A-Z]{2}\d{2}\d{4}\d{7}$/ },
  other: { label: 'Other', re: /^[A-Z0-9]{6,}$/ },
};

const FIND = {
  pan: /\b[A-Z]{5}[0-9]{4}[A-Z]\b/,
  aadhaar: /\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b/,
  passport: /\b[A-PR-WY][1-9]\d\s?\d{4}[1-9]\b/,
  driving_licence: /\b[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{7}\b/,
};

const STOP =
  /(INCOME|TAX|GOVT|GOVERNMENT|INDIA|DEPARTMENT|PERMANENT|ACCOUNT|NUMBER|REPUBLIC|PASSPORT|DRIVING|LICEN[CS]E|FATHER|CARD|UNIQUE|IDENTIFICATION|AUTHORITY|SIGNATURE|DATE|BIRTH|ADDRESS|MALE|FEMALE)/i;

const DATE = /(\d{2})[/\-. ](\d{2})[/\-. ](\d{4})/;

function toISO(dd, mm, yyyy) {
  if (mm < 1 || mm > 12 || dd < 1 || dd > 31 || yyyy < 1900 || yyyy > 2100) return '';
  const iso = `${yyyy}-${String(mm).padStart(2, '0')}-${String(dd).padStart(2, '0')}`;
  const t = new Date(iso);
  return Number.isNaN(t.getTime()) ? '' : iso;
}

export function parseDocument(raw = '') {
  const lines = raw.split('\n').map((l) => l.trim()).filter(Boolean);
  const flat = raw.toUpperCase();

  let id_type = 'other';
  let id_number = '';
  for (const key of ['pan', 'passport', 'driving_licence', 'aadhaar']) {
    const m = flat.match(FIND[key]);
    if (m) {
      id_type = key;
      id_number = m[0].replace(/[\s-]/g, '');
      break;
    }
  }

  let dob = '';
  let expiry = '';
  const dates = [];
  for (const line of lines) {
    const m = line.match(DATE);
    if (!m) continue;
    const iso = toISO(+m[1], +m[2], +m[3]);
    if (!iso) continue;
    dates.push(iso);
    if (/birth|dob|d\.o\.b/i.test(line)) dob ||= iso;
    else if (/valid|expir|exp\b/i.test(line)) expiry ||= iso;
  }
  if (!dob && dates.length) dob = [...dates].sort()[0];

  let full_name = '';
  for (const line of lines) {
    const m = line.match(/^name\s*[:\-]?\s*([A-Za-z .]{3,})$/i);
    if (m && !/father/i.test(line)) {
      full_name = m[1].trim();
      break;
    }
  }
  if (!full_name) {
    full_name =
      lines.find((l) => {
        const words = l.split(/\s+/);
        return /^[A-Z][A-Z .]{4,}$/.test(l) && words.length >= 2 && words.length <= 4 && !STOP.test(l);
      }) || '';
  }

  return { full_name, date_of_birth: dob, id_type, id_number, id_expiry: expiry };
}

export function validateFields(f, now = new Date()) {
  const idRule = ID_TYPES[f.id_type] || ID_TYPES.other;
  const nameOk = /^[A-Za-z][A-Za-z .'-]{2,}$/.test((f.full_name || '').trim());
  const dobDate = f.date_of_birth ? new Date(f.date_of_birth) : null;
  const dobOk = !!dobDate && !Number.isNaN(dobDate.getTime()) && dobDate < now;
  const idOk = idRule.re.test((f.id_number || '').replace(/[\s-]/g, '').toUpperCase());

  let age = null;
  if (dobOk) {
    age = now.getFullYear() - dobDate.getFullYear();
    const hadBirthday =
      now.getMonth() > dobDate.getMonth() ||
      (now.getMonth() === dobDate.getMonth() && now.getDate() >= dobDate.getDate());
    if (!hadBirthday) age -= 1;
  }
  const ageOk = age !== null && age >= 18 && age < 120;
  // PAN and Aadhaar have no expiry; only fail when an expiry is present and in the past.
  const notExpired = !f.id_expiry || new Date(f.id_expiry) >= now;

  return { nameOk, dobOk, idOk, ageOk, notExpired, age };
}
