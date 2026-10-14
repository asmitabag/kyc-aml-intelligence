import { useState } from 'react';
import DocumentStep from './DocumentStep';
import DetailsStep from './DetailsStep';
import LiveStep from './LiveStep';
import ResultStep from './ResultStep';
import { deriveBackendSignals } from './kycSignals';

const STEPS = ['Scan document', 'Check details', 'Face check', 'Result'];

// Maps the scan result to the request body. Align these keys with the KYCSubmit schema
// (see /openapi.json on your FastAPI backend).
async function buildPayload(customerId, fields, ocr, live, result) {
  const backendSignals = await deriveBackendSignals({ fields, ocr, live, result });
  return {
    ...backendSignals,
    customer_id: customerId,
    full_name: fields.full_name,
    date_of_birth: fields.date_of_birth,
    id_type: fields.id_type,
    id_number: fields.id_number,
    id_expiry: fields.id_expiry || null,
    verification_method: 'camera_ocr_face',
    kyc_score: result.total,
    kyc_decision: result.decision,
    score_breakdown: Object.fromEntries(result.parts.map((p) => [p.key, p.points])),
    signals: {
      face_distance: live.faceDistance,
      face_samples: live.samples,
      liveness_blink: live.liveness.blink,
      liveness_head_turn: live.liveness.turn,
      document_presence_ratio: live.docPresenceRatio,
      ocr_confidence: ocr.confidence,
    },
  };
}

export default function CameraKyc({ customerId, onSubmit, onSuccess }) {
  const [step, setStep] = useState(0);
  const [doc, setDoc] = useState(null); // { docDescriptor, ocr, thumb }
  const [fields, setFields] = useState(null);
  const [live, setLive] = useState(null);

  const restart = () => { setDoc(null); setFields(null); setLive(null); setStep(0); };

  return (
    <div className="space-y-5">
      <ol className="flex flex-wrap gap-x-5 gap-y-1 text-sm" aria-label="Progress">
        {STEPS.map((label, i) => (
          <li key={label} aria-current={i === step ? 'step' : undefined} className={i === step ? 'font-medium text-ink' : i < step ? 'text-slate-500' : 'text-slate-300'}>
            {label}
          </li>
        ))}
      </ol>

      {step === 0 && (
        <DocumentStep
          onDone={(d) => { setDoc(d); setFields(d.fields); setStep(1); }}
        />
      )}
      {step === 1 && doc && (
        <DetailsStep
          thumb={doc.thumb}
          ocrConfidence={doc.ocr.confidence}
          fields={fields}
          onChange={setFields}
          onBack={restart}
          onNext={() => setStep(2)}
        />
      )}
      {step === 2 && doc && (
        <LiveStep
          docDescriptor={doc.docDescriptor}
          onBack={() => setStep(1)}
          onDone={(l) => { setLive(l); setStep(3); }}
        />
      )}
      {step === 3 && doc && live && (
        <ResultStep
          fields={fields}
          ocr={doc.ocr}
          live={live}
          onRestart={restart}
          onSubmit={async (result) => {
            await onSubmit(await buildPayload(customerId, fields, doc.ocr, live, result));
            onSuccess?.();
          }}
        />
      )}
    </div>
  );
}