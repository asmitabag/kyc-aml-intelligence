import { validateFields } from './documentParser';

const clamp = (x, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
const round3 = (x) => Math.round(x * 1000) / 1000;

async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', bytes); // available on HTTPS/localhost, same as the camera
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Fields the backend's KYCSubmit schema requires.
 *
 * IMPORTANT: the browser has no real tamper or deepfake detector. These are heuristic proxies built
 * from the signals we do have (liveness, document visibility, OCR quality, ID format). Treat them as
 * placeholders until your backend models compute them from the uploaded images.
 */
export async function deriveBackendSignals({ fields, ocr, live, result }) {
  const v = validateFields(fields);
  const liveRatio = (live.liveness.blink ? 0.5 : 0) + (live.liveness.turn ? 0.5 : 0);
  const docSeen = clamp((live.docPresenceRatio || 0) / 0.5);
  const ocrRatio = clamp(((ocr.confidence || 0) - 40) / 45);

  // 0.05 (no liveness cues) .. 0.95 (blink and head turn)
  const liveness_probability = 0.05 + 0.9 * liveRatio;

  // Higher when the ID number is malformed, text is hard to read, or the card wasn't seen live.
  const document_tamper_probability = clamp(1 - (0.4 * (v.idOk ? 1 : 0) + 0.3 * ocrRatio + 0.3 * docSeen), 0.02, 0.98);

  // Higher when there are no liveness cues and the document was never seen next to the face.
  const deepfake_probability = clamp(0.03 + 0.6 * (1 - liveRatio) + 0.2 * (1 - docSeen), 0.02, 0.98);

  // 0 = low risk, 1 = high risk. Rejections are floored so they never look low-risk.
  let risk = 1 - result.total / 100;
  if (result.decision === 'rejected') risk = Math.max(risk, 0.8);

  // Hash of the normalised ID number, for duplicate-document checks without sending the number again.
  // Unsalted hashes of short numbers can be brute-forced, so have the server re-hash with a secret (HMAC).
  const document_fingerprint = await sha256Hex(
    `${fields.id_type}:${(fields.id_number || '').replace(/[\s-]/g, '').toUpperCase()}`
  );

  return {
    liveness_probability: round3(liveness_probability),
    document_tamper_probability: round3(document_tamper_probability),
    deepfake_probability: round3(deepfake_probability),
    kyc_risk: round3(risk),
    document_fingerprint,
  };
}