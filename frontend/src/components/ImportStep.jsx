import { useState, useRef } from "react";
import client from "../api/client";
import { useToast } from "./Toast";

function FileDropZone({ playlistId, onImported }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  const toast = useToast();

  const handleFiles = async (files) => {
    const file = files[0];
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["xlsx", "xls", "csv"].includes(ext)) {
      setError("Please upload an .xlsx or .csv file");
      return;
    }
    setError("");
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await client.post(
        `/api/playlists/${playlistId}/import/excel`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      toast.success(`Imported ${data.tracks?.length || 0} tracks`);
      onImported(data);
    } catch (err) {
      const msg = err.response?.data?.detail || "Upload failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
          dragging
            ? "border-teal bg-teal/5 scale-[1.01]"
            : "border-gray-700 hover:border-gray-600 animate-drop-pulse"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="text-3xl mb-3 opacity-40">
          {uploading ? (
            <div className="w-8 h-8 border-2 border-teal border-t-transparent rounded-full animate-spin mx-auto" />
          ) : (
            "\u2B06"
          )}
        </div>
        <p className="text-gray-300 font-medium">
          {uploading ? "Uploading..." : "Drop Excel/CSV file here"}
        </p>
        <p className="text-gray-500 text-sm mt-1">or click to browse</p>
      </div>
      {error && (
        <p className="text-red-400 text-sm mt-2">{error}</p>
      )}
    </div>
  );
}

function TextPasteInput({ playlistId, onImported }) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const toast = useToast();

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setError("");
    setSubmitting(true);
    try {
      const { data } = await client.post(
        `/api/playlists/${playlistId}/import/text`,
        { text }
      );
      toast.success(`Imported ${data.tracks?.length || 0} tracks`);
      onImported(data);
    } catch (err) {
      const msg = err.response?.data?.detail || "Import failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={10}
        placeholder={`Paste tracks, one per line:\n\nDaft Punk - Get Lucky\nM83 - Midnight City\nMGMT - Electric Feel\nTame Impala - The Less I Know the Better`}
        className="w-full bg-dark-surface border border-gray-700 rounded-xl px-4 py-3 text-gray-100 font-mono text-sm focus:border-teal focus:ring-1 focus:ring-teal outline-none resize-y transition"
      />
      {error && (
        <p className="text-red-400 text-sm mt-2">{error}</p>
      )}
      <button
        onClick={handleSubmit}
        disabled={submitting || !text.trim()}
        className="mt-3 bg-dark-card border border-gray-700 text-gray-200 font-medium px-5 py-2 rounded-lg hover:border-teal hover:text-teal transition disabled:opacity-40"
      >
        {submitting ? "Importing..." : "Import tracks"}
      </button>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="mt-6 space-y-2">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-3">
          <div className="w-8 h-8 rounded bg-gray-800 animate-skeleton" />
          <div className="flex-1 h-8 rounded bg-gray-800 animate-skeleton" />
          <div className="w-24 h-8 rounded bg-gray-800 animate-skeleton" />
          <div className="w-16 h-8 rounded bg-gray-800 animate-skeleton" />
        </div>
      ))}
    </div>
  );
}

function PreviewTable({ tracks }) {
  if (!tracks || tracks.length === 0) return null;

  return (
    <div className="mt-6 overflow-x-auto">
      <table className="w-full text-sm min-w-[500px]">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-800">
            <th className="py-2 px-3 font-medium">#</th>
            <th className="py-2 px-3 font-medium">Title</th>
            <th className="py-2 px-3 font-medium">Artist</th>
            <th className="py-2 px-3 font-medium">Key</th>
            <th className="py-2 px-3 font-medium">BPM</th>
            <th className="py-2 px-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((pt, i) => (
            <tr
              key={pt.id}
              className="border-b border-gray-800/50 hover:bg-dark-surface/50"
            >
              <td className="py-2 px-3 font-mono text-gray-500">{i + 1}</td>
              <td className="py-2 px-3 text-gray-100">{pt.track.title}</td>
              <td className="py-2 px-3 text-gray-300">{pt.track.artist}</td>
              <td className="py-2 px-3 font-mono text-teal">
                {pt.track.key_camelot || (
                  <span className="text-amber">--</span>
                )}
              </td>
              <td className="py-2 px-3 font-mono text-gray-300">
                {pt.track.bpm
                  ? Number(pt.track.bpm).toFixed(0)
                  : <span className="text-amber">--</span>}
              </td>
              <td className="py-2 px-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    pt.track.enrichment_status === "analyzed"
                      ? "bg-teal/10 text-teal"
                      : pt.track.enrichment_status === "identified"
                        ? "bg-blue-500/10 text-blue-400"
                        : "bg-gray-700/50 text-gray-400"
                  }`}
                >
                  {pt.track.enrichment_status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ImportStep({ playlistId, playlist, onPlaylistUpdate, onNext }) {
  const [tab, setTab] = useState("file");

  const handleImported = (data) => {
    onPlaylistUpdate(data);
  };

  const tracks = playlist?.tracks || [];

  return (
    <div>
      <h2 className="text-xl font-semibold mb-1">Import Tracks</h2>
      <p className="text-gray-400 text-sm mb-6">
        Upload an Excel file or paste a track list
      </p>

      <div className="flex gap-1 mb-6">
        {[
          { id: "file", label: "Upload File" },
          { id: "text", label: "Paste Text" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t.id
                ? "bg-teal/15 text-teal border border-teal/30"
                : "text-gray-400 hover:text-gray-200 border border-transparent"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "file" ? (
        <FileDropZone playlistId={playlistId} onImported={handleImported} />
      ) : (
        <TextPasteInput playlistId={playlistId} onImported={handleImported} />
      )}

      <PreviewTable tracks={tracks} />

      {tracks.length > 0 && (
        <div className="mt-6 flex justify-end">
          <button
            onClick={onNext}
            className="bg-teal text-dark-bg font-semibold px-6 py-2.5 rounded-lg hover:bg-teal-400 transition"
          >
            Continue to Enrich &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
