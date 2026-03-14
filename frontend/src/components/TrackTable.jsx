import { useState } from "react";
import client from "../api/client";
import { useToast } from "./Toast";

const SOURCE_LABELS = {
  cache: "Cache",
  musicbrainz: "MB",
  essentia_server: "Server",
  essentia_browser: "Browser",
  manual: "Manual",
  deezer: "Deezer",
  acousticbrainz: "AB",
  getsongbpm: "GSBPM",
};

const SOURCE_COLORS = {
  cache: "text-gray-400",
  musicbrainz: "text-blue-400",
  essentia_server: "text-purple-400",
  essentia_browser: "text-green-400",
  manual: "text-amber",
  deezer: "text-green-300",
  acousticbrainz: "text-purple-300",
  getsongbpm: "text-teal",
};

export default function TrackTable({ playlistId, tracks, onUpdate }) {
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState("");
  const toast = useToast();

  const startEdit = (ptId, field, currentValue) => {
    setEditingCell({ ptId, field });
    setEditValue(currentValue ?? "");
  };

  const commitEdit = async (pt) => {
    if (!editingCell) return;
    const { field } = editingCell;
    const trackId = pt.track_id;

    let payload = {};
    if (field === "key") {
      payload.key_override = editValue.trim() || null;
    } else if (field === "bpm") {
      const v = parseFloat(editValue);
      payload.bpm_override = isNaN(v) ? null : v;
    } else if (field === "energy") {
      const v = parseInt(editValue, 10);
      payload.energy_override = isNaN(v) ? null : v;
    }

    setEditingCell(null);

    try {
      await client.put(
        `/api/playlists/${playlistId}/tracks/${trackId}`,
        payload
      );
      onUpdate?.();
    } catch {
      toast.error("Failed to save override");
    }
  };

  const handleKeyDown = (e, pt) => {
    if (e.key === "Enter") {
      commitEdit(pt);
    } else if (e.key === "Escape") {
      setEditingCell(null);
    }
  };

  if (!tracks || tracks.length === 0) {
    return (
      <p className="text-gray-500 text-sm mt-4">No tracks imported yet.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm min-w-[600px]">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-800">
            <th className="py-2 px-2 font-medium w-8">#</th>
            <th className="py-2 px-2 font-medium">Title</th>
            <th className="py-2 px-2 font-medium">Artist</th>
            <th className="py-2 px-2 font-medium w-20">Key</th>
            <th className="py-2 px-2 font-medium w-20">BPM</th>
            <th className="py-2 px-2 font-medium w-20">Energy</th>
            <th className="py-2 px-2 font-medium w-20">Source</th>
            <th className="py-2 px-2 font-medium w-24">Status</th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((pt, i) => {
            const t = pt.track;
            const effKey = pt.key_override || t.key_camelot;
            const effBpm = pt.bpm_override ?? t.bpm;
            const effEnergy = pt.energy_override ?? t.energy;
            const isEditing = (field) =>
              editingCell?.ptId === pt.id && editingCell?.field === field;

            return (
              <tr
                key={pt.id}
                className="border-b border-gray-800/50 hover:bg-dark-surface/50"
              >
                <td className="py-2 px-2 font-mono text-gray-500">{i + 1}</td>
                <td className="py-2 px-2 text-gray-100 truncate max-w-[200px]">
                  {t.title}
                </td>
                <td className="py-2 px-2 text-gray-300 truncate max-w-[160px]">
                  {t.artist}
                </td>

                {/* Key - editable */}
                <td
                  className="py-2 px-2 font-mono cursor-pointer"
                  onClick={() => startEdit(pt.id, "key", effKey)}
                >
                  {isEditing("key") ? (
                    <input
                      autoFocus
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={() => commitEdit(pt)}
                      onKeyDown={(e) => handleKeyDown(e, pt)}
                      className="w-16 bg-dark-surface border border-teal rounded px-1 py-0.5 text-xs font-mono text-gray-100 outline-none"
                    />
                  ) : (
                    <span
                      className={
                        effKey ? "text-teal" : "text-amber bg-amber/10 px-1 rounded"
                      }
                    >
                      {effKey || "--"}
                    </span>
                  )}
                </td>

                {/* BPM - editable */}
                <td
                  className="py-2 px-2 font-mono cursor-pointer"
                  onClick={() =>
                    startEdit(pt.id, "bpm", effBpm ? Number(effBpm).toFixed(0) : "")
                  }
                >
                  {isEditing("bpm") ? (
                    <input
                      autoFocus
                      type="number"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={() => commitEdit(pt)}
                      onKeyDown={(e) => handleKeyDown(e, pt)}
                      className="w-16 bg-dark-surface border border-teal rounded px-1 py-0.5 text-xs font-mono text-gray-100 outline-none"
                    />
                  ) : (
                    <span
                      className={
                        effBpm
                          ? "text-gray-200"
                          : "text-amber bg-amber/10 px-1 rounded"
                      }
                    >
                      {effBpm ? Number(effBpm).toFixed(0) : "--"}
                    </span>
                  )}
                </td>

                {/* Energy - editable */}
                <td
                  className="py-2 px-2 font-mono cursor-pointer"
                  onClick={() =>
                    startEdit(
                      pt.id,
                      "energy",
                      effEnergy != null ? String(Math.round(Number(effEnergy))) : ""
                    )
                  }
                >
                  {isEditing("energy") ? (
                    <input
                      autoFocus
                      type="number"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={() => commitEdit(pt)}
                      onKeyDown={(e) => handleKeyDown(e, pt)}
                      className="w-16 bg-dark-surface border border-teal rounded px-1 py-0.5 text-xs font-mono text-gray-100 outline-none"
                    />
                  ) : (
                    <span
                      className={
                        effEnergy != null
                          ? "text-gray-200"
                          : "text-amber bg-amber/10 px-1 rounded"
                      }
                    >
                      {effEnergy != null ? Math.round(Number(effEnergy)) : "--"}
                    </span>
                  )}
                </td>

                {/* Source */}
                <td className="py-2 px-2">
                  <span
                    className={`text-xs font-medium ${SOURCE_COLORS[t.analysis_source] || "text-gray-500"}`}
                  >
                    {SOURCE_LABELS[t.analysis_source] || "-"}
                  </span>
                </td>

                {/* Status */}
                <td className="py-2 px-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      t.enrichment_status === "analyzed"
                        ? "bg-teal/10 text-teal"
                        : t.enrichment_status === "identified"
                          ? "bg-blue-500/10 text-blue-400"
                          : t.enrichment_status === "not_found"
                            ? "bg-red-500/10 text-red-400"
                            : "bg-gray-700/50 text-gray-400"
                    }`}
                  >
                    {t.enrichment_status}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
