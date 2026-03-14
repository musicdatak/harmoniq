/**
 * Client-side audio analysis using Essentia.js (WASM).
 * Extracts BPM and energy. Key detection requires server analysis.
 */

let essentiaInstance = null;
let essentia = null;

async function getEssentia() {
  if (essentia) return essentia;

  const { Essentia, EssentiaWASM } = await import("essentia.js");
  const wasmModule = await EssentiaWASM();
  essentia = new Essentia(wasmModule);
  return essentia;
}

/**
 * Decode an audio File into a mono Float32Array at the given sample rate.
 */
function decodeAudioFile(file, sampleRate = 44100) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate,
        });
        const buffer = await audioCtx.decodeAudioData(reader.result);
        // Mix to mono
        const mono = buffer.getChannelData(0);
        audioCtx.close();
        resolve(mono);
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Analyze an audio file in the browser.
 * Returns { bpm, energy } or throws on failure.
 */
export async function analyzeAudioFile(file) {
  const es = await getEssentia();
  const audioData = await decodeAudioFile(file);

  // Convert to essentia vector
  const vector = es.arrayToVector(audioData);

  // BPM estimation using PercivalBpmEstimator
  let bpm = null;
  try {
    const bpmResult = es.PercivalBpmEstimator(vector);
    bpm = Math.round(bpmResult.bpm * 100) / 100;
    if (bpm <= 0) bpm = null;
  } catch {
    // fallback: try RhythmExtractor
    try {
      const rhythm = es.RhythmExtractor(vector);
      bpm = Math.round(rhythm.bpm * 100) / 100;
      if (bpm <= 0) bpm = null;
    } catch {
      bpm = null;
    }
  }

  // Energy
  let energy = null;
  try {
    const energyResult = es.Energy(vector);
    // Normalize to 0-10 scale (log scale, same as server)
    const raw = energyResult.energy;
    energy = Math.min(10, Math.log10(raw + 1) * 2);
    energy = Math.round(energy * 100) / 100;
  } catch {
    energy = null;
  }

  return { bpm, energy };
}

/**
 * Check if Essentia.js WASM can be loaded.
 */
export async function isAvailable() {
  try {
    await getEssentia();
    return true;
  } catch {
    return false;
  }
}
