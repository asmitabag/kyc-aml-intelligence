import * as faceapi from '@vladmandic/face-api';

let loading = null;

// Models are served from /public/models (see setup notes).
export function loadFaceModels(url = '/models') {
  if (!loading) {
    loading = (async () => {
      // WebGL is far faster than the CPU backend; the CPU fallback can freeze the page.
      try { await faceapi.tf.setBackend('webgl'); } catch { /* keep the default backend */ }
      await faceapi.tf.ready();
      console.info('[kyc] TensorFlow backend:', faceapi.tf.getBackend());
      await Promise.all([
        faceapi.nets.ssdMobilenetv1.loadFromUri(url),
        faceapi.nets.faceLandmark68Net.loadFromUri(url),
        faceapi.nets.faceRecognitionNet.loadFromUri(url),
      ]);
    })().catch((e) => {
      loading = null;
      throw e;
    });
  }
  return loading;
}

const OPTIONS = () => new faceapi.SsdMobilenetv1Options({ minConfidence: 0.4 });

export const detectFaces = (input) =>
  faceapi.detectAllFaces(input, OPTIONS()).withFaceLandmarks().withFaceDescriptors();

export const faceDistance = (a, b) => faceapi.euclideanDistance(a, b);
export const boxArea = (f) => f.detection.box.width * f.detection.box.height;

const d = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

// Eye aspect ratio from the 68-point landmarks (left eye starts at 36, right at 42).
const ear = (p, i) => (d(p[i + 1], p[i + 5]) + d(p[i + 2], p[i + 4])) / (2 * d(p[i], p[i + 3]));
export function eyeAspectRatio(landmarks) {
  const p = landmarks.positions;
  return (ear(p, 36) + ear(p, 42)) / 2;
}

// Rough yaw proxy: nose tip offset from the jaw midpoint, normalised by jaw width.
export function yawProxy(landmarks) {
  const p = landmarks.positions;
  return (p[30].x - (p[0].x + p[16].x) / 2) / (p[16].x - p[0].x);
}

export function median(values) {
  if (!values.length) return null;
  const s = [...values].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}