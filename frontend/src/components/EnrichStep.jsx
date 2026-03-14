import { useState, useRef, useEffect, useCallback } from "react";
import client from "../api/client";
import TrackTable from "./TrackTable";
import { analyzeAudioFile } from "../services/essentiaAnalyzer";
import { useToast } from "./Toast";

const AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"];

// --- Auto-Enrich (MusicBrainz → AcousticBrainz → Deezer) ---
function AutoEnrichPanel({ playlistId, onRefresh }) {
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState(null);
  const pollRef = useRef(null);
  const toast = useToast();

  const pollStatus = useCallback(async () => {
    try {
      const { data } = await client.get(
        `/api/playlists/${playlistId}/enrich/status`
      );
      setStatus(data);
      // Done when no pending and at least one identified or all are not_found
      if (data.pending <= 0) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        setRunning(false);
        onRefresh?.();
        toast.success(
          `Enrichment complete: ${data.analyzed} with key, ${data.has_bpm} with BPM`
        );
      }
    } catch {
      // ignore
    }
  }, [playlistId, onRefresh, toast]);

  const startEnrich = async () => {
    setRunning(true);
    try {
      await client.post(`/api/playlists/${playlistId}/enrich/auto`);
      // Start polling
      pollRef.current = setInterval(async () => {
        await pollStatus();
        onRefresh?.();
      }, 2000);
    } catch (err) {
      setRunning(false);
      toast.error(err.response?.data?.detail || "Enrichment failed");
    }
  };

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const pct =
    status && status.total > 0
      ? Math.round(((status.total - status.pending) / status.total) * 100)
      : 0;

  return (
    <div className="bg-dark-surface border border-gray-800 rounded-xl p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-gray-100 mb-1">
            Auto-Enrich All Sources
          </h3>
          <p className="text-gray-400 text-sm">
            Chains MusicBrainz (identify) → SoundNet (key + BPM + energy) →
            GetSongBPM (key + BPM) → AcousticBrainz (key + BPM) → Deezer (BPM fallback).
          </p>
        </div>
        <button
          onClick={startEnrich}
          disabled={running}
          className="shrink-0 bg-teal text-dark-bg font-semibold px-5 py-2.5 rounded-lg hover:bg-teal-400 transition disabled:opacity-50 flex items-center gap-2"
        >
          {running && (
            <span className="w-4 h-4 border-2 border-dark-bg border-t-transparent rounded-full animate-spin" />
          )}
          {running ? "Enriching..." : "Auto-Enrich"}
        </button>
      </div>

      {running && status && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm text-gray-400 mb-1">
            <span>
              {status.identified} identified, {status.analyzed} with key,{" "}
              {status.has_bpm} with BPM
            </span>
            <span>{pct}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-2">
            <div
              className="bg-teal h-2 rounded-full transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {!running && status && (
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Identified", value: status.identified, color: "text-blue-400" },
            { label: "Key found", value: status.analyzed, color: "text-teal" },
            { label: "BPM found", value: status.has_bpm, color: "text-green-400" },
            { label: "Not found", value: status.not_found, color: "text-gray-500" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className={`text-xl font-mono font-bold ${s.color}`}>
                {s.value}
              </div>
              <div className="text-xs text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Individual source buttons ---
function IndividualSources({ playlistId, onRefresh }) {
  const [runningSource, setRunningSource] = useState(null);
  const toast = useToast();

  const runSource = async (source, label) => {
    setRunningSource(source);
    try {
      await client.post(`/api/playlists/${playlistId}/enrich/${source}`);
      toast.success(`${label} started — refreshing...`);
      // Poll briefly then refresh
      await new Promise((r) => setTimeout(r, 3000));
      onRefresh?.();
      // Keep polling until done
      for (let i = 0; i < 30; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        const { data } = await client.get(
          `/api/playlists/${playlistId}/enrich/status`
        );
        onRefresh?.();
        if (data.pending <= 0) break;
      }
      onRefresh?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || `${label} failed`);
    } finally {
      setRunningSource(null);
    }
  };

  const sources = [
    {
      id: "musicbrainz",
      label: "MusicBrainz",
      desc: "Identify tracks, get genre tags",
      color: "border-blue-500/30 hover:border-blue-500",
    },
    {
      id: "soundnet",
      label: "SoundNet",
      desc: "Key + BPM + energy (best coverage)",
      color: "border-teal/30 hover:border-teal",
    },
    {
      id: "getsongbpm",
      label: "GetSongBPM",
      desc: "Key + BPM (fallback)",
      color: "border-orange-500/30 hover:border-orange-500",
    },
    {
      id: "acousticbrainz",
      label: "AcousticBrainz",
      desc: "Key + BPM via MusicBrainz ID",
      color: "border-purple-500/30 hover:border-purple-500",
    },
    {
      id: "deezer",
      label: "Deezer",
      desc: "BPM fallback (no auth needed)",
      color: "border-green-500/30 hover:border-green-500",
    },
  ];

  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">
        Or run individually
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {sources.map((s) => (
          <button
            key={s.id}
            onClick={() => runSource(s.id, s.label)}
            disabled={runningSource !== null}
            className={`text-left border rounded-lg p-3 transition disabled:opacity-50 ${s.color} border-gray-800`}
          >
            <div className="text-sm font-medium text-gray-200 flex items-center gap-2">
              {runningSource === s.id && (
                <span className="w-3 h-3 border-2 border-gray-200 border-t-transparent rounded-full animate-spin" />
              )}
              {s.label}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">{s.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

// --- Audio upload tabs ---
function AudioPanel({ playlistId, tracks, onRefresh }) {
  const [tab, setTab] = useState("server");

  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">
        Audio file analysis
      </p>
      <div className="flex gap-1 mb-4">
        <button
          onClick={() => setTab("server")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
            tab === "server"
              ? "bg-purple-500/15 text-purple-400 border border-purple-500/30"
              : "text-gray-400 hover:text-gray-200 border border-transparent"
          }`}
        >
          Upload to Server
        </button>
        <button
          onClick={() => setTab("browser")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
            tab === "browser"
              ? "bg-green-500/15 text-green-400 border border-green-500/30"
              : "text-gray-400 hover:text-gray-200 border border-transparent"
          }`}
        >
          Analyze in Browser
        </button>
      </div>
      {tab === "server" ? (
        <ServerUploadTab
          playlistId={playlistId}
          tracks={tracks}
          onRefresh={onRefresh}
        />
      ) : (
        <BrowserAnalysisTab tracks={tracks} onRefresh={onRefresh} />
      )}
    </div>
  );
}

// --- Server Upload ---
function ServerUploadTab({ playlistId, tracks, onRefresh }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const toast = useToast();

  const handleFiles = (fileList) => {
    const valid = Array.from(fileList).filter((f) => {
      const ext = "." + f.name.split(".").pop().toLowerCase();
      return AUDIO_EXTENSIONS.includes(ext);
    });
    setFiles(valid);
    setError("");
    setResults([]);
  };

  const upload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setError("");
    setResults([]);

    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      const { data } = await client.post(
        `/api/playlists/${playlistId}/analyze-batch`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResults(data.results || []);
      const analyzed = (data.results || []).filter(
        (r) => r.status === "analyzed"
      ).length;
      toast.success(
        `Analyzed ${analyzed} of ${data.results?.length || 0} files`
      );
      onRefresh?.();
    } catch (err) {
      const msg = err.response?.data?.detail || "Upload failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          dragging
            ? "border-purple-400 bg-purple-400/5 scale-[1.01]"
            : "border-gray-700 hover:border-gray-600"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={AUDIO_EXTENSIONS.join(",")}
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <p className="text-gray-300 text-sm font-medium">
          {files.length > 0
            ? `${files.length} file${files.length !== 1 ? "s" : ""} selected`
            : "Drop audio files here — full analysis (key + BPM + energy)"}
        </p>
        <p className="text-gray-500 text-xs mt-1">
          MP3, WAV, FLAC, OGG, M4A, AAC
        </p>
      </div>

      {files.length > 0 && (
        <button
          onClick={upload}
          disabled={uploading}
          className="mt-3 bg-purple-600 text-white font-semibold px-5 py-2 rounded-lg hover:bg-purple-500 transition disabled:opacity-50 flex items-center gap-2 text-sm"
        >
          {uploading && (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {uploading
            ? "Analyzing..."
            : `Upload & Analyze ${files.length} file${files.length !== 1 ? "s" : ""}`}
        </button>
      )}

      {error && <p className="text-red-400 text-sm mt-2">{error}</p>}

      {results.length > 0 && (
        <div className="mt-3 space-y-1">
          {results.map((r, i) => (
            <div
              key={i}
              className={`text-xs px-3 py-1.5 rounded ${
                r.status === "analyzed"
                  ? "bg-teal/10 text-teal"
                  : r.status === "skipped"
                    ? "bg-amber-500/10 text-amber-400"
                    : "bg-red-500/10 text-red-400"
              }`}
            >
              <span className="font-mono">{r.filename}</span>
              {r.status === "analyzed" ? (
                <span className="ml-2">
                  — {r.track} | {r.key_camelot} | {r.bpm?.toFixed(0)} BPM
                </span>
              ) : (
                <span className="ml-2">— {r.reason}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Browser Analysis ---
function BrowserAnalysisTab({ tracks, onRefresh }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0, current: "" });
  const inputRef = useRef(null);
  const toast = useToast();

  const handleFiles = async (fileList) => {
    const audioFiles = Array.from(fileList).filter((f) => {
      const ext = "." + f.name.split(".").pop().toLowerCase();
      return AUDIO_EXTENSIONS.includes(ext);
    });
    if (audioFiles.length === 0) return;

    setAnalyzing(true);
    setProgress({ done: 0, total: audioFiles.length, current: "" });

    const trackLookup = {};
    for (const pt of tracks) {
      const t = pt.track;
      trackLookup[t.title.toLowerCase()] = t;
      trackLookup[t.artist.toLowerCase()] = t;
      trackLookup[`${t.artist} - ${t.title}`.toLowerCase()] = t;
    }

    let matched = 0;
    for (let i = 0; i < audioFiles.length; i++) {
      const file = audioFiles[i];
      const basename = file.name.replace(/\.[^.]+$/, "").toLowerCase().trim();
      setProgress({ done: i, total: audioFiles.length, current: file.name });

      let track =
        trackLookup[basename] ||
        trackLookup[basename.replace(/_/g, " ")] ||
        trackLookup[basename.replace(/-/g, " ")];
      if (!track) {
        for (const pt of tracks) {
          const t = pt.track;
          if (
            basename.includes(t.title.toLowerCase()) ||
            basename.includes(t.artist.toLowerCase())
          ) {
            track = t;
            break;
          }
        }
      }

      if (!track) continue;

      try {
        const result = await analyzeAudioFile(file);
        await client.put(`/api/tracks/${track.id}/update-analysis`, {
          bpm: result.bpm,
          energy: result.energy,
        });
        matched++;
      } catch {
        // continue
      }
    }

    setProgress((p) => ({ ...p, done: audioFiles.length, current: "" }));
    setAnalyzing(false);
    toast.success(
      `Analyzed ${matched} file${matched !== 1 ? "s" : ""} in browser`
    );
    onRefresh?.();
  };

  const pct =
    progress.total > 0
      ? Math.round((progress.done / progress.total) * 100)
      : 0;

  return (
    <div>
      <div
        onClick={() => !analyzing && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all border-gray-700 hover:border-gray-600 ${
          analyzing ? "opacity-50 pointer-events-none" : ""
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={AUDIO_EXTENSIONS.join(",")}
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <p className="text-gray-300 text-sm font-medium">
          Select audio files — BPM + energy (runs locally)
        </p>
        <p className="text-gray-500 text-xs mt-1">
          Files never leave your machine
        </p>
      </div>

      {analyzing && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span className="truncate max-w-[250px]">{progress.current}</span>
            <span>
              {progress.done}/{progress.total} ({pct}%)
            </span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-1.5">
            <div
              className="bg-green-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {!analyzing &&
        progress.total > 0 &&
        progress.done === progress.total && (
          <p className="mt-2 text-xs text-green-400">
            Done — {progress.done} files processed.
          </p>
        )}
    </div>
  );
}

// --- Main EnrichStep ---
export default function EnrichStep({
  playlistId,
  playlist,
  onPlaylistUpdate,
  onNext,
  onBack,
}) {
  const refresh = useCallback(async () => {
    try {
      const { data } = await client.get(`/api/playlists/${playlistId}`);
      onPlaylistUpdate(data);
    } catch {
      // ignore
    }
  }, [playlistId, onPlaylistUpdate]);

  const tracks = playlist?.tracks || [];
  const hasKeyData = tracks.some(
    (pt) => pt.key_override || pt.track?.key_camelot
  );

  return (
    <div>
      <h2 className="text-xl font-semibold mb-1">Enrich Tracks</h2>
      <p className="text-gray-400 text-sm mb-6">
        Add key, BPM, and energy data to your tracks
      </p>

      {/* Primary: Auto-enrich */}
      <AutoEnrichPanel playlistId={playlistId} onRefresh={refresh} />

      {/* Individual sources */}
      <div className="mt-6">
        <IndividualSources playlistId={playlistId} onRefresh={refresh} />
      </div>

      {/* Audio file analysis */}
      <div className="mt-6">
        <AudioPanel
          playlistId={playlistId}
          tracks={tracks}
          onRefresh={refresh}
        />
      </div>

      {/* Track Table */}
      <div className="mt-8">
        {tracks.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No tracks imported yet. Go back to import tracks first.
          </p>
        ) : (
          <TrackTable
            playlistId={playlistId}
            tracks={tracks}
            onUpdate={refresh}
          />
        )}
      </div>

      {/* Empty key data hint */}
      {tracks.length > 0 && !hasKeyData && (
        <div className="mt-4 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-sm text-amber-400">
          No key data yet. Click "Auto-Enrich" above, upload audio files, or
          click a key cell to enter manually.
        </div>
      )}

      {/* Navigation */}
      <div className="mt-6 flex justify-between">
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-gray-200 transition"
        >
          &larr; Back
        </button>
        <button
          onClick={onNext}
          className="bg-teal text-dark-bg font-semibold px-6 py-2.5 rounded-lg hover:bg-teal-400 transition"
        >
          Continue to Customize &rarr;
        </button>
      </div>
    </div>
  );
}
