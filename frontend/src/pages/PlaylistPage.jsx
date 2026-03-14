import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import Stepper from "../components/Stepper";
import ImportStep from "../components/ImportStep";
import EnrichStep from "../components/EnrichStep";
import CustomizeStep from "../components/CustomizeStep";
import ScheduleStep from "../components/ScheduleStep";
import { useToast } from "../components/Toast";

function PlaylistSkeleton() {
  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-6 h-6 rounded bg-gray-800 animate-skeleton" />
        <div className="w-48 h-6 rounded bg-gray-800 animate-skeleton" />
        <div className="w-20 h-5 rounded bg-gray-800 animate-skeleton" />
      </div>
      <div className="flex gap-2 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="w-24 h-8 rounded-full bg-gray-800 animate-skeleton" />
        ))}
      </div>
      <div className="bg-dark-card border border-gray-800 rounded-xl p-6">
        <div className="w-40 h-6 rounded bg-gray-800 animate-skeleton mb-4" />
        <div className="w-64 h-4 rounded bg-gray-800 animate-skeleton mb-8" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="w-full h-10 rounded bg-gray-800 animate-skeleton" />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function PlaylistPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [playlist, setPlaylist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0);

  const fetchPlaylist = useCallback(async () => {
    try {
      const { data } = await client.get(`/api/playlists/${id}`);
      setPlaylist(data);
      // Auto-advance step based on state
      if (data.is_scheduled) setStep(3);
      else if (data.tracks?.length > 0) setStep((prev) => Math.max(prev, 0));
    } catch {
      toast.error("Playlist not found");
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  }, [id, navigate, toast]);

  useEffect(() => {
    fetchPlaylist();
  }, [fetchPlaylist]);

  if (loading || !playlist) {
    return <PlaylistSkeleton />;
  }

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <ImportStep
            playlistId={id}
            playlist={playlist}
            onPlaylistUpdate={setPlaylist}
            onNext={() => setStep(1)}
          />
        );
      case 1:
        return (
          <EnrichStep
            playlistId={id}
            playlist={playlist}
            onPlaylistUpdate={setPlaylist}
            onNext={() => setStep(2)}
            onBack={() => setStep(0)}
          />
        );
      case 2:
        return (
          <CustomizeStep
            playlistId={id}
            playlist={playlist}
            onPlaylistUpdate={setPlaylist}
            onNext={() => setStep(3)}
            onBack={() => setStep(1)}
          />
        );
      case 3:
        return (
          <ScheduleStep
            playlistId={id}
            playlist={playlist}
            onBack={() => setStep(2)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-8">
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate("/dashboard")}
          className="text-gray-500 hover:text-gray-300 transition"
        >
          &larr;
        </button>
        <h1 className="text-xl font-bold truncate">{playlist.name}</h1>
        <span className="text-sm text-gray-500 font-mono">
          {playlist.tracks?.length || 0} tracks
        </span>
      </div>

      {/* Responsive stepper: full on sm+, dropdown on mobile */}
      <div className="hidden sm:block">
        <Stepper currentStep={step} onStepClick={setStep} />
      </div>
      <div className="sm:hidden mb-6">
        <select
          value={step}
          onChange={(e) => setStep(Number(e.target.value))}
          className="w-full bg-dark-surface border border-gray-700 rounded-lg px-4 py-2.5 text-gray-100 font-medium focus:border-teal outline-none"
        >
          {["Import", "Enrich", "Customize", "Results"].map((label, i) => (
            <option key={i} value={i} disabled={i > step}>
              {i + 1}. {label} {i < step ? "\u2713" : i === step ? "(current)" : ""}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-dark-card border border-gray-800 rounded-xl p-4 sm:p-6 animate-step-in" key={step}>
        {renderStep()}
      </div>
    </div>
  );
}
