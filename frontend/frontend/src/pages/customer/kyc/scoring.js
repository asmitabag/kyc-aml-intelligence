import { validateFields } from './documentParser';

// Weights sum to 100. Tune them (and the thresholds) against your own test data.
export const WEIGHTS = {
  faceMatch: 40,
  liveness: 20,
  docPresence: 10,
  ocrQuality: 10,
  fieldsValid: 15,
  ageExpiry: 5,
};

export const THRESHOLDS = { verified: 80, review: 60 };
// face-api descriptors: lower distance = more similar. Document photos are small and noisy,
// so the "match" gate is looser than the usual 0.6 cut-off used for live-to-live comparison.
export const FACE = { best: 0.38, worst: 0.65, matchMax: 0.55 };

const clamp = (x, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));

export const faceSimilarity = (dist) =>
  dist == null ? 0 : clamp((FACE.worst - dist) / (FACE.worst - FACE.best));

export function computeKycScore({ faceDistance, liveness, docPresenceRatio, ocrConfidence, fields }) {
  const v = validateFields(fields);
  const live = (liveness.blink ? 0.5 : 0) + (liveness.turn ? 0.5 : 0);

  const parts = [
    {
      key: 'faceMatch',
      label: 'Face match',
      ratio: faceSimilarity(faceDistance),
      detail: faceDistance == null ? 'No comparison made' : `Embedding distance ${faceDistance.toFixed(2)}`,
    },
    {
      key: 'liveness',
      label: 'Liveness',
      ratio: live,
      detail: `Blink ${liveness.blink ? 'seen' : 'not seen'}, head turn ${liveness.turn ? 'seen' : 'not seen'}`,
    },
    {
      key: 'docPresence',
      label: 'Document in live view',
      ratio: clamp((docPresenceRatio || 0) / 0.5),
      detail: `Visible in ${Math.round((docPresenceRatio || 0) * 100)}% of frames`,
    },
    {
      key: 'ocrQuality',
      label: 'Text legibility',
      ratio: clamp(((ocrConfidence || 0) - 40) / 45),
      detail: `OCR confidence ${Math.round(ocrConfidence || 0)}%`,
    },
    {
      key: 'fieldsValid',
      label: 'Details are valid',
      ratio: ([v.nameOk, v.dobOk, v.idOk].filter(Boolean).length) / 3,
      detail: `Name ${v.nameOk ? 'ok' : 'invalid'}, birth date ${v.dobOk ? 'ok' : 'invalid'}, ID number ${v.idOk ? 'ok' : 'invalid'}`,
    },
    {
      key: 'ageExpiry',
      label: 'Age and validity',
      ratio: ((v.ageOk ? 1 : 0) + (v.notExpired ? 1 : 0)) / 2,
      detail: `${v.age != null ? `Age ${v.age}` : 'Age unknown'}, ${v.notExpired ? 'not expired' : 'expired'}`,
    },
  ].map((p) => ({ ...p, weight: WEIGHTS[p.key], points: +(p.ratio * WEIGHTS[p.key]).toFixed(1) }));

  const total = Math.round(parts.reduce((s, p) => s + p.points, 0));
  const flags = [];
  let decision = total >= THRESHOLDS.verified ? 'verified' : total >= THRESHOLDS.review ? 'manual_review' : 'rejected';

  const faceMatched = faceDistance != null && faceDistance <= FACE.matchMax;
  if (!faceMatched) {
    decision = 'rejected';
    flags.push('The face on the document does not match the live face.');
  }
  if (!v.ageOk) {
    decision = 'rejected';
    flags.push('Date of birth is missing, invalid, or under 18.');
  }
  if (!v.notExpired) {
    decision = 'rejected';
    flags.push('The document has expired.');
  }
  if (decision === 'verified' && !(liveness.blink || liveness.turn)) {
    decision = 'manual_review';
    flags.push('No liveness signal was detected.');
  }

  return { total, decision, parts, flags, validation: v };
}
