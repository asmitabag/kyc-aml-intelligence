import { useCallback, useEffect, useRef, useState } from 'react';

// Thin wrapper over getUserMedia. Needs HTTPS (or localhost) to work.
// Each start() is tagged; if stop() or a newer start() happens meanwhile (e.g. React StrictMode's
// double mount in dev), the older call discards its stream instead of fighting over the <video>.
export function useCamera({ facingMode = 'user' } = {}) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const startId = useRef(0);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);

  const stop = useCallback(() => {
    startId.current += 1;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setReady(false);
  }, []);

  const start = useCallback(async () => {
    const id = ++startId.current;
    setError(null);
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Camera access needs a secure (HTTPS) connection.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      if (id !== startId.current || !videoRef.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      if (id === startId.current) setReady(true);
    } catch (e) {
      if (e?.name === 'AbortError' || id !== startId.current) return;
      setError(
        e?.name === 'NotAllowedError'
          ? 'Camera permission was denied. Allow camera access in your browser and try again.'
          : e?.message || 'Could not start the camera.'
      );
    }
  }, [facingMode]);

  useEffect(() => stop, [stop]);

  return { videoRef, ready, error, start, stop };
}