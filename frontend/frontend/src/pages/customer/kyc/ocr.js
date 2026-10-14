import { createWorker } from 'tesseract.js';

// By default tesseract.js fetches its worker and language data from a CDN.
// For production, self-host them (workerPath / corePath / langPath options).
export async function runOcr(canvas, onProgress) {
  const worker = await createWorker('eng', 1, {
    logger: (m) => {
      if (m.status === 'recognizing text') onProgress?.(m.progress);
    },
  });
  try {
    const { data } = await worker.recognize(canvas);
    return { text: data.text || '', confidence: data.confidence || 0 };
  } finally {
    await worker.terminate();
  }
}
