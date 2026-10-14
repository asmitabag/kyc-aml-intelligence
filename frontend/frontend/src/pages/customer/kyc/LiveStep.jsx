import { useEffect, useRef, useState } from 'react';
import CameraView from './CameraView';
import { useCamera } from './useCamera';
import { loadFaceModels, detectFaces, faceDistance, boxArea, eyeAspectRatio, yawProxy, median } from './faceEngine';

const MIN_SAMPLES = 8;      // face comparisons before auto-finish
const DOC_MAX_DISTANCE = 0.5; // a second face this close to the scanned portrait counts as "document in view"
const TURN_RANGE = 0.15;    // yaw-proxy range that counts as a head turn
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export default function LiveStep({ docDescriptor, onDone, onBack }) {
  const camera = useCamera({ facingMode: 'user' });
  const acc = useRef({
    distances: [], faceFrames: 0, docFrames: 0,
    blink: false, turn: false, wasClosed: false, earMax: 0, yawMin: 1, yawMax: -1,
  });
  const [ui, setUi] = useState({ hint: 'Loading face models…', samples: 0, docSeen: false, blink: false, turn: false });
  const [fatal, setFatal] = useState(null);

  const finish = () => {
    const a = acc.current;
    onDone({
      faceDistance: median(a.distances),
      samples: a.distances.length,
      liveness: { blink: a.blink, turn: a.turn },
      docPresenceRatio: a.faceFrames ? a.docFrames / a.faceFrames : 0,
    });
  };
  const finishRef = useRef(finish);
  finishRef.current = finish;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await loadFaceModels();
      if (cancelled) return;
      await camera.start();
      while (!cancelled) {
        const video = camera.videoRef.current;
        if (!video?.srcObject) return; // camera failed to start; error is shown by CameraView
        if (video.readyState < 2) { await sleep(100); continue; }

        const faces = (await detectFaces(video)).sort((a, b) => boxArea(b) - boxArea(a));
        const a = acc.current;
        let hint = 'Move into view so your face is visible.';
        let docSeen = false;

        const live = faces[0];
        const second = faces[1];
        const bigEnough = live && live.detection.box.width > video.videoWidth * 0.15;
        // If two faces are nearly the same size we can't tell the person from the document photo.
        const ambiguous = second && boxArea(live) < boxArea(second) * 1.2;

        if (bigEnough && !ambiguous) {
          a.faceFrames += 1;
          a.distances.push(faceDistance(live.descriptor, docDescriptor));

          if (second && faceDistance(second.descriptor, docDescriptor) < DOC_MAX_DISTANCE) {
            a.docFrames += 1;
            docSeen = true;
          }

          const ear = eyeAspectRatio(live.landmarks);
          a.earMax = Math.max(a.earMax, ear);
          const closed = ear < a.earMax * 0.75;
          if (a.wasClosed && !closed) a.blink = true;
          a.wasClosed = closed;

          const yaw = yawProxy(live.landmarks);
          a.yawMin = Math.min(a.yawMin, yaw);
          a.yawMax = Math.max(a.yawMax, yaw);
          if (a.yawMax - a.yawMin > TURN_RANGE) a.turn = true;

          if (!docSeen) hint = 'Hold the ID next to your face, photo towards the camera.';
          else if (!a.blink) hint = 'Blink naturally.';
          else if (!a.turn) hint = 'Slowly turn your head left, then right.';
          else hint = 'Hold still…';
        } else if (ambiguous) {
          hint = 'Keep your face closer to the camera than the ID.';
        }

        setUi({ hint, samples: a.distances.length, docSeen, blink: a.blink, turn: a.turn });

        if (a.distances.length >= MIN_SAMPLES && a.blink && a.turn) {
          finishRef.current();
          return;
        }
        await sleep(120); // give the main thread room to breathe between frames
      }
    })().catch(() => setFatal('Could not run the face check. Check that /models is served and try again.'));

    return () => {
      cancelled = true;
      camera.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const Check = ({ ok, children }) => (
    <li className={ok ? 'text-emerald-600' : 'text-slate-400'}>{ok ? '✓' : '○'} {children}</li>
  );

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">Keep your ID visible beside your face while we compare the two.</p>
      <CameraView camera={camera} mirrored>
        <div className="absolute inset-x-0 bottom-0 bg-black/55 px-4 py-2 text-center text-sm text-white">{ui.hint}</div>
      </CameraView>
      {fatal && <p className="text-sm text-red-600" role="alert">{fatal}</p>}
      <ul className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <Check ok={ui.samples >= MIN_SAMPLES}>Face compared ({Math.min(ui.samples, MIN_SAMPLES)}/{MIN_SAMPLES})</Check>
        <Check ok={ui.docSeen}>ID in view</Check>
        <Check ok={ui.blink}>Blink</Check>
        <Check ok={ui.turn}>Head turn</Check>
      </ul>
      <div className="flex gap-3">
        <button type="button" onClick={onBack} className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-ink">Back</button>
        <button
          type="button"
          onClick={finish}
          disabled={ui.samples < 5}
          className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-ink disabled:opacity-40"
        >
          Finish now
        </button>
      </div>
    </div>
  );
}