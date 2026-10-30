/**
 * In-browser face analysis and proctoring for the mock interview (MediaPipe Face Landmarker).
 * Video never leaves the device. Per frame it produces:
 *   attention, eyeContact, smile, stress  – body-language estimates (0..1) for the main face
 *   faceCount                            – how many faces are visible (more than one = someone else is there)
 *   backgroundMotion                     – share of the background that changed since the last frame,
 *                                          with the candidate's own face and upper body masked out
 */
export interface FaceMetrics {
  facePresent: boolean;
  faceCount: number;
  phoneDetected: boolean;   // a mobile phone is visible (checked about once a second)
  personCount: number;      // people visible, including ones not facing the camera
  backgroundMotion: number;
  attention: number;
  eyeContact: number;
  smile: number;
  stress: number;
}

const VISION_VERSION = '0.10.14';
const VISION_URL = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${VISION_VERSION}`;
const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';

let landmarkerPromise: Promise<any> | null = null;
let detectorPromise: Promise<any> | null = null;
const OBJECT_MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/float16/1/efficientdet_lite0.tflite';

/** COCO object detector (recognises "cell phone" and "person"); optional, so failures are ignored. */
async function getObjectDetector(): Promise<any | null> {
  if (!detectorPromise) {
    detectorPromise = (async () => {
      const vision: any = await import(/* webpackIgnore: true */ `${VISION_URL}/vision_bundle.mjs`);
      const fileset = await vision.FilesetResolver.forVisionTasks(`${VISION_URL}/wasm`);
      const create = (delegate: 'GPU' | 'CPU') => vision.ObjectDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: OBJECT_MODEL_URL, delegate },
        runningMode: 'VIDEO', scoreThreshold: 0.35, maxResults: 8,
        categoryAllowlist: ['cell phone', 'person'],
      });
      try { return await create('GPU'); } catch (_) { return await create('CPU'); }
    })().catch(() => null);
  }
  return detectorPromise;
}

async function getLandmarker(): Promise<any> {
  if (!landmarkerPromise) {
    landmarkerPromise = (async () => {
      const vision: any = await import(/* webpackIgnore: true */ `${VISION_URL}/vision_bundle.mjs`);
      const fileset = await vision.FilesetResolver.forVisionTasks(`${VISION_URL}/wasm`);
      const create = (delegate: 'GPU' | 'CPU') => vision.FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate },
        runningMode: 'VIDEO',
        outputFaceBlendshapes: true,
        numFaces: 4,                       // detect extra people in the frame
        minFaceDetectionConfidence: 0.5,
        minFacePresenceConfidence: 0.5,
      });
      try { return await create('GPU'); } catch (_) { return await create('CPU'); }
    })().catch(err => { landmarkerPromise = null; throw err; });
  }
  return landmarkerPromise;
}

const clamp = (v: number) => Math.max(0, Math.min(1, v));

// The biggest face (closest to the camera) is treated as the candidate.
function mainFaceIndex(faces: any[]): number {
  let best = 0, bestArea = -1;
  faces.forEach((lm, i) => {
    let minX = 1, maxX = 0, minY = 1, maxY = 0;
    for (const p of lm) { minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x); minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y); }
    const area = (maxX - minX) * (maxY - minY);
    if (area > bestArea) { bestArea = area; best = i; }
  });
  return best;
}

function scoreFace(lm: any, shapesList: any[]): Pick<FaceMetrics, 'attention' | 'eyeContact' | 'smile' | 'stress'> {
  const shapes: Record<string, number> = {};
  for (const c of shapesList || []) shapes[c.categoryName] = c.score;
  const b = (name: string) => shapes[name] || 0;
  const nose = lm[1], left = lm[234], right = lm[454], top = lm[10], chin = lm[152];
  const yawRatio = (nose.x - left.x) / Math.max(1e-6, right.x - left.x);
  const pitchRatio = (nose.y - top.y) / Math.max(1e-6, chin.y - top.y);
  const attention = clamp(1 - Math.abs(yawRatio - 0.5) * 3.2 - Math.max(0, Math.abs(pitchRatio - 0.55) - 0.08) * 3);
  const gazeAway = Math.max(
    (b('eyeLookOutLeft') + b('eyeLookInRight')) / 2, (b('eyeLookInLeft') + b('eyeLookOutRight')) / 2,
    (b('eyeLookUpLeft') + b('eyeLookUpRight')) / 2, (b('eyeLookDownLeft') + b('eyeLookDownRight')) / 2,
  );
  return {
    attention,
    eyeContact: clamp((1 - gazeAway * 1.7) * (0.35 + 0.65 * attention)),
    smile: clamp((b('mouthSmileLeft') + b('mouthSmileRight')) / 2 * 1.3),
    stress: clamp(((b('browDownLeft') + b('browDownRight')) / 2) * 1.4 + ((b('mouthPressLeft') + b('mouthPressRight')) / 2) * 0.6),
  };
}

// ── background motion: compare small grayscale frames, ignoring the candidate's face + body ──
const W = 80, H = 60;

function makeMotionDetector() {
  const canvas = typeof document !== 'undefined' ? document.createElement('canvas') : null;
  if (canvas) { canvas.width = W; canvas.height = H; }
  const ctx = canvas?.getContext('2d', { willReadFrequently: true }) || null;
  let prev: Uint8ClampedArray | null = null;

  return (video: HTMLVideoElement, faceBox: { x0: number; x1: number; y0: number; y1: number } | null): number => {
    if (!ctx) return 0;
    ctx.drawImage(video, 0, 0, W, H);
    const data = ctx.getImageData(0, 0, W, H).data;
    const gray = new Uint8ClampedArray(W * H);
    for (let i = 0, j = 0; i < data.length; i += 4, j++) gray[j] = (data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114) | 0;
    if (!prev) { prev = gray; return 0; }

    // Mask: the face (padded) plus a wider column below it for neck, shoulders and hands while speaking
    let mx0 = -1, mx1 = -1, my0 = -1;
    if (faceBox) {
      const fw = faceBox.x1 - faceBox.x0;
      mx0 = Math.floor((faceBox.x0 - fw * 0.9) * W); mx1 = Math.ceil((faceBox.x1 + fw * 0.9) * W);
      my0 = Math.floor((faceBox.y0 - (faceBox.y1 - faceBox.y0) * 0.5) * H);
    }
    let changed = 0, counted = 0;
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        if (faceBox && x >= mx0 && x <= mx1 && y >= my0) continue;
        const k = y * W + x;
        counted++;
        if (Math.abs(gray[k] - prev[k]) > 28) changed++;
      }
    }
    prev = gray;
    const frac = counted ? changed / counted : 0;
    return frac > 0.65 ? 0 : frac;   // the whole frame changing at once is usually auto-exposure, not motion
  };
}

/**
 * Starts analysing the given <video> element; calls onMetrics about 6 times a second.
 * Resolves to a stop() function. Rejects if the model can't be loaded (offline, unsupported browser).
 */
export async function startFaceAnalysis(video: HTMLVideoElement, onMetrics: (m: FaceMetrics) => void): Promise<() => void> {
  const landmarker = await getLandmarker();
  const motionOf = makeMotionDetector();
  let detector: any = null;
  getObjectDetector().then(d => { detector = d; });
  let lastObjects = 0;
  let phoneSeen = false;
  let people = 0;
  let stopped = false;
  let last = 0;
  let smooth: FaceMetrics | null = null;
  const alpha = 0.3;

  const loop = (now: number) => {
    if (stopped) return;
    if (now - last > 160 && video.readyState >= 2 && video.videoWidth > 0) {
      last = now;
      try {
        const result = landmarker.detectForVideo(video, now);
        const faces: any[] = result?.faceLandmarks || [];
        let box = null;
        let m: FaceMetrics;
        if (faces.length) {
          const idx = mainFaceIndex(faces);
          const lm = faces[idx];
          let x0 = 1, x1 = 0, y0 = 1, y1 = 0;
          for (const p of lm) { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y); }
          box = { x0, x1, y0, y1 };
          m = { facePresent: true, faceCount: faces.length, phoneDetected: false, personCount: 0, backgroundMotion: 0, ...scoreFace(lm, result.faceBlendshapes?.[idx]?.categories) };
        } else {
          m = { facePresent: false, faceCount: 0, phoneDetected: false, personCount: 0, backgroundMotion: 0, attention: 0, eyeContact: 0, smile: 0, stress: 0 };
        }
        m.backgroundMotion = motionOf(video, box);
        if (detector && now - lastObjects > 900) {          // phone / person check about once a second
          lastObjects = now;
          try {
            const objects = detector.detectForVideo(video, now + 0.5)?.detections || [];
            phoneSeen = objects.some((o: any) => o.categories?.[0]?.categoryName === 'cell phone' && o.categories[0].score >= 0.45);
            people = objects.filter((o: any) => o.categories?.[0]?.categoryName === 'person' && o.categories[0].score >= 0.5).length;
          } catch (_) { /* ignore */ }
        }
        m.phoneDetected = phoneSeen;
        m.personCount = people;
        smooth = !smooth || !m.facePresent || !smooth.facePresent ? m : {
          ...m,
          attention: smooth.attention + alpha * (m.attention - smooth.attention),
          eyeContact: smooth.eyeContact + alpha * (m.eyeContact - smooth.eyeContact),
          smile: smooth.smile + alpha * (m.smile - smooth.smile),
          stress: smooth.stress + alpha * (m.stress - smooth.stress),
        };
        onMetrics(smooth);
      } catch (_) { /* skip a bad frame */ }
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
  return () => { stopped = true; };
}
