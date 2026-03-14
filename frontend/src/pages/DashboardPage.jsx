import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import { useToast } from "../components/Toast";

function DashboardSkeleton() {
  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <div className="w-40 h-8 rounded bg-gray-800 animate-skeleton" />
        <div className="w-36 h-10 rounded-lg bg-gray-800 animate-skeleton" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-dark-card border border-gray-800 rounded-xl p-5">
            <div className="w-32 h-5 rounded bg-gray-800 animate-skeleton mb-3" />
            <div className="w-20 h-4 rounded bg-gray-800 animate-skeleton mb-2" />
            <div className="w-24 h-3 rounded bg-gray-800 animate-skeleton" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

  const fetchPlaylists = useCallback(async () => {
    try {
      const { data } = await client.get("/api/playlists");
      setPlaylists(data);
    } catch {
      toast.error("Failed to load playlists");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchPlaylists();
  }, [fetchPlaylists]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const { data } = await client.post("/api/playlists", {
        name: newName.trim(),
      });
      toast.success(`Created "${data.name}"`);
      navigate(`/playlist/${data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create playlist");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await client.delete(`/api/playlists/${id}`);
      setPlaylists((prev) => prev.filter((p) => p.id !== id));
      toast.success(`Deleted "${name}"`);
    } catch {
      toast.error("Failed to delete playlist");
    }
  };

  const formatDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Your Playlists</h1>
        <button
          onClick={() => setShowNew(true)}
          className="bg-teal text-dark-bg font-semibold px-5 py-2 rounded-lg hover:bg-teal-400 transition"
        >
          + New Playlist
        </button>
      </div>

      {showNew && (
        <form
          onSubmit={handleCreate}
          className="bg-dark-card border border-gray-800 rounded-xl p-5 mb-6 flex gap-3 animate-step-in"
        >
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Playlist name..."
            autoFocus
            className="flex-1 bg-dark-surface border border-gray-700 rounded-lg px-4 py-2 text-gray-100 focus:border-teal focus:ring-1 focus:ring-teal outline-none"
          />
          <button
            type="submit"
            disabled={creating}
            className="bg-teal text-dark-bg font-semibold px-5 py-2 rounded-lg hover:bg-teal-400 transition disabled:opacity-50"
          >
            {creating ? "Creating..." : "Create"}
          </button>
          <button
            type="button"
            onClick={() => {
              setShowNew(false);
              setNewName("");
            }}
            className="text-gray-500 hover:text-gray-300 px-3 transition"
          >
            Cancel
          </button>
        </form>
      )}

      {playlists.length === 0 ? (
        <div className="text-center py-20 animate-step-in">
          <div className="text-6xl mb-4 opacity-20">&#9835;</div>
          <p className="text-gray-300 text-lg font-medium">Create your first playlist</p>
          <p className="text-gray-500 text-sm mt-2 max-w-sm mx-auto">
            Import your track list, enrich with key and BPM data, then let HarmoniQ schedule the perfect harmonic flow.
          </p>
          <button
            onClick={() => setShowNew(true)}
            className="mt-6 bg-teal text-dark-bg font-semibold px-6 py-2.5 rounded-lg hover:bg-teal-400 transition"
          >
            + New Playlist
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {playlists.map((pl) => (
            <div
              key={pl.id}
              className="bg-dark-card border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition cursor-pointer group"
              onClick={() => navigate(`/playlist/${pl.id}`)}
            >
              <div className="flex items-start justify-between">
                <h3 className="font-semibold text-gray-100 truncate pr-2">
                  {pl.name}
                </h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(pl.id, pl.name);
                  }}
                  className="text-gray-600 hover:text-red-400 text-sm opacity-0 group-hover:opacity-100 transition"
                >
                  Delete
                </button>
              </div>

              <div className="mt-3 flex items-center gap-4 text-sm text-gray-400">
                <span className="font-mono">
                  {pl.track_count} track{pl.track_count !== 1 ? "s" : ""}
                </span>
                {pl.mix_score && (
                  <span className="font-mono text-teal">
                    Score: {Number(pl.mix_score).toFixed(0)}
                  </span>
                )}
              </div>

              <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                <span>{formatDate(pl.updated_at)}</span>
                {pl.is_scheduled && (
                  <span className="bg-teal/10 text-teal px-2 py-0.5 rounded-full">
                    Scheduled
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
