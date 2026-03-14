import { useState } from "react";
import client from "../api/client";
import { useToast } from "./Toast";

function RangeSlider({ label, value, onChange, max = 100 }) {
  return (
    <div className="mb-5">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gray-300">{label}</label>
        <span className="text-sm font-mono text-teal">{value}</span>
      </div>
      <input
        type="range"
        min={0}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 rounded-full appearance-none cursor-pointer bg-gray-800
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-teal [&::-webkit-slider-thumb]:shadow-lg
          [&::-webkit-slider-thumb]:cursor-pointer
          [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:rounded-full
          [&::-moz-range-thumb]:bg-teal [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer"
        style={{
          background: `linear-gradient(to right, #00e5c7 0%, #00e5c7 ${value}%, #1f2937 ${value}%, #1f2937 100%)`,
        }}
      />
    </div>
  );
}

export default function CustomizeStep({
  playlistId,
  playlist,
  onPlaylistUpdate,
  onNext,
  onBack,
}) {
  const [harmony, setHarmony] = useState(playlist?.harmony_weight ?? 80);
  const [energy, setEnergy] = useState(playlist?.energy_weight ?? 50);
  const [bpm, setBpm] = useState(playlist?.bpm_weight ?? 30);
  const [energyArc, setEnergyArc] = useState(playlist?.energy_arc_mode ?? false);
  const [scheduling, setScheduling] = useState(false);
  const toast = useToast();

  const handleSchedule = async () => {
    setScheduling(true);
    try {
      await client.put(`/api/playlists/${playlistId}`, {
        harmony_weight: harmony,
        energy_weight: energy,
        bpm_weight: bpm,
        energy_arc_mode: energyArc,
      });
      const { data } = await client.post(
        `/api/playlists/${playlistId}/schedule`
      );
      onPlaylistUpdate(data);
      const score = data.mix_score ? Number(data.mix_score).toFixed(0) : "N/A";
      toast.success(`Scheduled! Mix score: ${score}`);
      onNext();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Scheduling failed");
    } finally {
      setScheduling(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-1">Customize Scheduling</h2>
      <p className="text-gray-400 text-sm mb-8">
        Adjust weights to control how tracks are ordered
      </p>

      <div className="max-w-md">
        <RangeSlider
          label="Harmony Weight"
          value={harmony}
          onChange={setHarmony}
        />
        <RangeSlider
          label="Energy Weight"
          value={energy}
          onChange={setEnergy}
        />
        <RangeSlider label="BPM Weight" value={bpm} onChange={setBpm} />

        {/* Energy Arc toggle */}
        <div className="mt-6 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-300">Energy Arc Mode</p>
            <p className="text-xs text-gray-500 mt-0.5">
              Build energy up then bring it down naturally
            </p>
          </div>
          <button
            onClick={() => setEnergyArc(!energyArc)}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              energyArc ? "bg-teal" : "bg-gray-700"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                energyArc ? "translate-x-6" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Schedule button */}
      <div className="mt-10 text-center">
        <button
          onClick={handleSchedule}
          disabled={scheduling}
          className="bg-teal text-dark-bg font-bold text-lg px-10 py-4 rounded-xl hover:bg-teal-400 transition disabled:opacity-50 shadow-lg shadow-teal/20"
        >
          {scheduling ? (
            <span className="flex items-center gap-3">
              <span className="w-5 h-5 border-2 border-dark-bg border-t-transparent rounded-full animate-spin" />
              Scheduling...
            </span>
          ) : (
            "Schedule Playlist"
          )}
        </button>
      </div>

      {/* Navigation */}
      <div className="mt-8 flex justify-between">
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-gray-200 transition"
        >
          &larr; Back
        </button>
      </div>
    </div>
  );
}
