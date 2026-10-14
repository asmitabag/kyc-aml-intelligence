import { useEffect, useState } from 'react';
import { Camera } from 'lucide-react';
import CameraView from './CameraView';
import { useCamera } from './useCamera';
import { loadFaceModels, detectFaces, boxArea } from './faceEngine';
import { runOcr } from './ocr';
import { parseDocument } from './documentParser';

export default function DocumentStep({ onDone }) {
  const camera = useCamera({ facingMode: 'environment' });
  const [busy, setBusy] = useState(null); // 'face' | 'ocr' | null
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    camera.start();
    loadFaceModels().catch(() => setError('Could not load face models. Check that /models is served.'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const capture = async () => {
    const video = camera.videoRef.current;
    if (!video || !video.videoWidth) return;
    setError(null);
    try {
      const { videoWidth: w, videoHeight: h } = video;

      const plain = document.createElement('canvas');
      plain.width = w;
      plain.height = h;
      plain.getContext('2d').drawImage(video, 0, 0);

      // Higher-contrast greyscale copy for OCR.
      const ocrCanvas = document.createElement('canvas');
      ocrCanvas.width = w;
      ocrCanvas.height = h;
      const ctx = ocrCanvas.getContext('2d');
      ctx.filter = 'grayscale(1) contrast(1.4)';
      ctx.drawImage(video, 0, 0);

      setBusy('face');
      await loadFaceModels();
      const faces = await detectFaces(plain);
      if (!faces.length) {
        throw new Error('No portrait found on the document. Fill the frame, avoid glare, and try again.');
      }
      const portrait = [...faces].sort((a, b) => boxArea(b) - boxArea(a))[0];

      setBusy('ocr');
      const { text, confidence } = await runOcr(ocrCanvas, setProgress);
      if (!text.trim()) throw new Error('No text could be read. Hold the document steady in good light.');

      onDone({
        docDescriptor: portrait.descriptor,
        ocr: { text, confidence },
        fields: parseDocument(text),
        thumb: plain.toDataURL('image/jpeg', 0.6), // kept in memory only, never uploaded
      });
    } catch (e) {
      setError(e.message || 'Scan failed.');
    } finally {
      setBusy(null);
      setProgress(0);
    }
  };

  const guide = (
    <div className="pointer-events-none absolute inset-0 grid place-items-center">
      <div className="aspect-[1.586] w-[70%] rounded-xl border-2 border-dashed border-white/70" />
    </div>
  );

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Place your ID inside the frame with the photo and text clearly visible, then capture.
      </p>
      <CameraView camera={camera} guide={guide} />
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      <button
        type="button"
        onClick={capture}
        disabled={!camera.ready || !!busy}
        className="inline-flex items-center gap-2 rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        <Camera className="h-4 w-4" aria-hidden="true" />
        {busy === 'face' ? 'Finding portrait…' : busy === 'ocr' ? `Reading text… ${Math.round(progress * 100)}%` : 'Capture document'}
      </button>
    </div>
  );
}
