/**
 * In-browser face analysis for the mock interview, using MediaPipe Face Landmarker.
 * Video never leaves the device; only four summary numbers (0..1) are produced:
 *   attention   – how directly the head faces the camera
 *   eyeContact  – how centred the eye gaze is
 *   smile       – smile intensity
 *   stress      – brow tension / pressed lips (a rough proxy)
 */
export interface FaceMetrics {
  facePresent: boolean;
  attention: number;
  eyeContact: number;
  smile: number;
  stress: number;
}

const VISION_VERSION = '0.10.14';
const VISION_URL = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${VISION_VERSION}`;
const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';

let landmarkerPromise: Promise<any> | null = null;

async function getLandmarker(): Promise<any> {
  if (!landmarkerPromise) {
    landmarkerPromise = (async () => {
      const vision: any = await import(/* webpackIgnore: true */ `${VISION_URL}/vision_bundle.mjs`);
      const fileset = await vision.FilesetResolver.forVisionTasks(`${VISION_URL}/wasm`);
      const create = (delegate: 'GPU' | 'CPU') => vision.FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate },
        runningMode: 'VIDEO',
        outputFaceBlendshapes: true,
        numFaces: 1,
      });
      try { return await create('GPU'); } catch (_) { return await create('CPU'); }
    })().catch(err => { landmarkerPromise = null; throw err; });
  }
  return landmarkerPromise;
}

const clamp = (v: number) => Math.max(0, Math.min(1, v));

function scoreFrame(result: any): FaceMetrics {
  const lm = result?.faceLandmarks?.[0];
  if (!lm) return { facePresent: false, attention: 0, eyeContact: 0, smile: 0, stress: 0 };
  const shapes: Record<string, number> = {};
  for (const c of result.faceBlendshapes?.[0]?.categories || []) shapes[c.categoryName] = c.score;
  const b = (name: string) => shapes[name] || 0;

  // Head yaw/pitch from landmark geometry: nose tip (1), cheeks (234, 454), forehead (10), chin (152)
  const nose = lm[1], left = lm[234], right = lm[454], top = lm[10], chin = lm[152];
  const yawRatio = (nose.x - left.x) / Math.max(1e-6, right.x - left.x);     // ~0.5 when facing camera
  const pitchRatio = (nose.y - top.y) / Math.max(1e-6, chin.y - top.y);      // ~0.5–0.6 when level
  const attention = clamp(1 - Math.abs(yawRatio - 0.5) * 3.2 - Math.max(0, Math.abs(pitchRatio - 0.55) - 0.08) * 3);

  const gazeAway = Math.max(
    (b('eyeLookOutLeft') + b('eyeLookInRight')) / 2,
    (b('eyeLookInLeft') + b('eyeLookOutRight')) / 2,
    (b('eyeLookUpLeft') + b('eyeLookUpRight')) / 2,
    (b('eyeLookDownLeft') + b('eyeLookDownRight')) / 2,
  );
  const eyeContact = clamp((1 - gazeAway * 1.7) * (0.35 + 0.65 * attention));
  const smile = clamp((b('mouthSmileLeft') + b('mouthSmileRight')) / 2 * 1.3);
  const stress = clamp(((b('browDownLeft') + b('browDownRight')) / 2) * 1.4 + ((b('mouthPressLeft') + b('mouthPressRight')) / 2) * 0.6);
  return { facePresent: true, attention, eyeContact, smile, stress };
}

/**
 * Starts analysing the given <video> element. Calls onMetrics ~6 times per second with smoothed values.
 * Resolves to a stop() function. Rejects if the model can't be loaded (offline, unsupported browser).
 */
export async function startFaceAnalysis(video: HTMLVideoElement, onMetrics: (m: FaceMetrics) => void): Promise<() => void> {
  const landmarker = await getLandmarker();
  let stopped = false;
  let last = 0;
  let smooth: FaceMetrics | null = null;
  const alpha = 0.3;

  const loop = (now: number) => {
    if (stopped) return;
    if (now - last > 160 && video.readyState >= 2 && video.videoWidth > 0) {
      last = now;
      try {
        const m = scoreFrame(landmarker.detectForVideo(video, now));
        smooth = !smooth || !m.facePresent ? m : {
          facePresent: true,
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
