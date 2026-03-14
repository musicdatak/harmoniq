import { useMemo } from "react";
import ExportButtons from "./ExportButtons";

// Camelot key data for the wheel and badges
const CAMELOT_DATA = [
  { code: "1A", musical: "Ab minor", color: "#FF6B6B" },
  { code: "1B", musical: "B major", color: "#FF6B6B" },
  { code: "2A", musical: "Eb minor", color: "#FF8E53" },
  { code: "2B", musical: "F# major", color: "#FF8E53" },
  { code: "3A", musical: "Bb minor", color: "#FFB347" },
  { code: "3B", musical: "Db major", color: "#FFB347" },
  { code: "4A", musical: "F minor", color: "#FFD93D" },
  { code: "4B", musical: "Ab major", color: "#FFD93D" },
  { code: "5A", musical: "C minor", color: "#6BCB77" },
  { code: "5B", musical: "Eb major", color: "#6BCB77" },
  { code: "6A", musical: "G minor", color: "#4D96FF" },
  { code: "6B", musical: "Bb major", color: "#4D96FF" },
  { code: "7A", musical: "D minor", color: "#6B5CE7" },
  { code: "7B", musical: "F major", color: "#6B5CE7" },
  { code: "8A", musical: "A minor", color: "#9B59B6" },
  { code: "8B", musical: "C major", color: "#9B59B6" },
  { code: "9A", musical: "E minor", color: "#E056A0" },
  { code: "9B", musical: "G major", color: "#E056A0" },
  { code: "10A", musical: "B minor", color: "#FF4757" },
  { code: "10B", musical: "D major", color: "#FF4757" },
  { code: "11A", musical: "F# minor", color: "#1ABC9C" },
  { code: "11B", musical: "A major", color: "#1ABC9C" },
  { code: "12A", musical: "Db minor", color: "#3498DB" },
  { code: "12B", musical: "E major", color: "#3498DB" },
];

const CODE_TO_COLOR = Object.fromEntries(
  CAMELOT_DATA.map((d) => [d.code, d.color])
);

// --- MixScoreGauge ---
function MixScoreGauge({ score }) {
  const pct = Math.max(0, Math.min(100, Number(score) || 0));
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  const color =
    pct >= 80 ? "#00e5c7" : pct >= 60 ? "#6BCB77" : pct >= 40 ? "#FFD93D" : "#FF4757";

  return (
    <div className="flex flex-col items-center">
      <svg width="150" height="150" viewBox="0 0 150 150">
        {/* Background circle */}
        <circle
          cx="75"
          cy="75"
          r={radius}
          fill="none"
          stroke="#1f2937"
          strokeWidth="10"
        />
        {/* Animated fill */}
        <circle
          cx="75"
          cy="75"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 75 75)"
          style={{
            transition: "stroke-dashoffset 1.5s ease-out, stroke 0.5s ease",
          }}
        />
        {/* Score text */}
        <text
          x="75"
          y="70"
          textAnchor="middle"
          fill={color}
          fontFamily="'JetBrains Mono', monospace"
          fontSize="28"
          fontWeight="bold"
        >
          {pct.toFixed(0)}
        </text>
        <text
          x="75"
          y="92"
          textAnchor="middle"
          fill="#9ca3af"
          fontFamily="'JetBrains Mono', monospace"
          fontSize="11"
        >
          MIX SCORE
        </text>
      </svg>
    </div>
  );
}

// --- CamelotBadge ---
function CamelotBadge({ code }) {
  if (!code) return <span className="text-gray-500 font-mono text-xs">--</span>;
  const color = CODE_TO_COLOR[code] || "#9ca3af";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="w-3 h-3 rounded-full inline-block flex-shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="font-mono text-sm" style={{ color }}>
        {code}
      </span>
    </span>
  );
}

// --- TransitionBadge ---
const TRANSITION_CONFIG = {
  Perfect: { emoji: "\uD83D\uDFE2", color: "#00e5c7", bg: "bg-teal/10" },
  Harmonic: { emoji: "\uD83D\uDD35", color: "#4D96FF", bg: "bg-blue-500/10" },
  Near: { emoji: "\uD83D\uDFE1", color: "#FFD93D", bg: "bg-yellow-500/10" },
  Clash: { emoji: "\uD83D\uDD34", color: "#FF4757", bg: "bg-red-500/10" },
};

function TransitionBadge({ label, score }) {
  if (!label) return null;
  const cfg = TRANSITION_CONFIG[label] || TRANSITION_CONFIG.Clash;
  return (
    <tr>
      <td colSpan="7" className="py-0 px-0">
        <div className="flex items-center justify-center gap-2 py-1">
          <div className="flex-1 h-px bg-gray-800" />
          <span
            className={`text-xs px-2.5 py-0.5 rounded-full ${cfg.bg} flex items-center gap-1`}
            style={{ color: cfg.color }}
          >
            <span>{cfg.emoji}</span>
            {label}
            {score != null && (
              <span className="font-mono ml-1 opacity-70">
                {Number(score).toFixed(0)}
              </span>
            )}
          </span>
          <div className="flex-1 h-px bg-gray-800" />
        </div>
      </td>
    </tr>
  );
}

// --- CamelotWheel ---
function CamelotWheel({ usedKeys, keySequence }) {
  const cx = 150;
  const cy = 150;
  const outerR = 130;
  const innerR = 85;
  const midR = (outerR + innerR) / 2;

  // 12 number groups, each with A (inner) and B (outer)
  const segments = [];
  for (let num = 1; num <= 12; num++) {
    const angle = ((num - 1) * 30 - 90) * (Math.PI / 180);
    const nextAngle = (num * 30 - 90) * (Math.PI / 180);

    for (const letter of ["B", "A"]) {
      const code = `${num}${letter}`;
      const color = CODE_TO_COLOR[code] || "#666";
      const isUsed = usedKeys.has(code);
      const r1 = letter === "B" ? midR : innerR;
      const r2 = letter === "B" ? outerR : midR;

      const x1 = cx + r1 * Math.cos(angle);
      const y1 = cy + r1 * Math.sin(angle);
      const x2 = cx + r2 * Math.cos(angle);
      const y2 = cy + r2 * Math.sin(angle);
      const x3 = cx + r2 * Math.cos(nextAngle);
      const y3 = cy + r2 * Math.sin(nextAngle);
      const x4 = cx + r1 * Math.cos(nextAngle);
      const y4 = cy + r1 * Math.sin(nextAngle);

      const d = `M ${x1} ${y1} L ${x2} ${y2} A ${r2} ${r2} 0 0 1 ${x3} ${y3} L ${x4} ${y4} A ${r1} ${r1} 0 0 0 ${x1} ${y1} Z`;

      // Label position
      const midAngle = (angle + nextAngle) / 2;
      const labelR = (r1 + r2) / 2;
      const lx = cx + labelR * Math.cos(midAngle);
      const ly = cy + labelR * Math.sin(midAngle);

      segments.push({ code, color, isUsed, d, lx, ly });
    }
  }

  // Build journey path from keySequence
  const journeyPoints = useMemo(() => {
    return keySequence
      .filter((code) => code)
      .map((code) => {
        const num = parseInt(code);
        const letter = code.slice(-1);
        const angle = ((num - 1) * 30 + 15 - 90) * (Math.PI / 180);
        const r = letter === "B" ? (midR + outerR) / 2 : (innerR + midR) / 2;
        return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
      });
  }, [keySequence]);

  const journeyPath =
    journeyPoints.length > 1
      ? journeyPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ")
      : "";

  const totalLength = useMemo(() => {
    let len = 0;
    for (let i = 1; i < journeyPoints.length; i++) {
      const dx = journeyPoints[i].x - journeyPoints[i - 1].x;
      const dy = journeyPoints[i].y - journeyPoints[i - 1].y;
      len += Math.sqrt(dx * dx + dy * dy);
    }
    return len;
  }, [journeyPoints]);

  return (
    <svg width="300" height="300" viewBox="0 0 300 300">
      {/* Segments */}
      {segments.map((seg) => (
        <g key={seg.code}>
          <path
            d={seg.d}
            fill={seg.isUsed ? seg.color : "#1a1a2e"}
            stroke="#0a0a0f"
            strokeWidth="1.5"
            opacity={seg.isUsed ? 0.85 : 0.3}
          />
          <text
            x={seg.lx}
            y={seg.ly}
            textAnchor="middle"
            dominantBaseline="central"
            fill={seg.isUsed ? "#0a0a0f" : "#4b5563"}
            fontSize="8"
            fontFamily="'JetBrains Mono', monospace"
            fontWeight={seg.isUsed ? "bold" : "normal"}
          >
            {seg.code}
          </text>
        </g>
      ))}

      {/* Journey path */}
      {journeyPath && (
        <path
          d={journeyPath}
          fill="none"
          stroke="#00e5c7"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.8"
          strokeDasharray={totalLength}
          strokeDashoffset={totalLength}
          style={{
            animation: "drawPath 2s ease-out forwards",
          }}
        />
      )}

      {/* Start/end markers */}
      {journeyPoints.length > 0 && (
        <>
          <circle
            cx={journeyPoints[0].x}
            cy={journeyPoints[0].y}
            r="4"
            fill="#00e5c7"
          />
          <circle
            cx={journeyPoints[journeyPoints.length - 1].x}
            cy={journeyPoints[journeyPoints.length - 1].y}
            r="4"
            fill="#FF4757"
          />
        </>
      )}

      <style>{`
        @keyframes drawPath {
          to { stroke-dashoffset: 0; }
        }
      `}</style>
    </svg>
  );
}

// --- ResultsTable ---
function ResultsTable({ tracks }) {
  if (!tracks || tracks.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-800">
            <th className="py-2 px-2 font-medium w-8">#</th>
            <th className="py-2 px-2 font-medium">Title</th>
            <th className="py-2 px-2 font-medium">Artist</th>
            <th className="py-2 px-2 font-medium w-20">Key</th>
            <th className="py-2 px-2 font-medium w-20">BPM</th>
            <th className="py-2 px-2 font-medium w-20">Energy</th>
            <th className="py-2 px-2 font-medium w-20">Source</th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((pt, i) => {
            const t = pt.track;
            const effKey = pt.key_override || t.key_camelot;
            const effBpm = pt.bpm_override ?? t.bpm;
            const effEnergy = pt.energy_override ?? t.energy;

            return [
              // Transition badge between rows
              i > 0 && (
                <TransitionBadge
                  key={`trans-${pt.id}`}
                  label={pt.transition_label}
                  score={pt.transition_score}
                />
              ),
              <tr
                key={pt.id}
                className="border-b border-gray-800/50 hover:bg-dark-surface/50"
                style={{
                  animation: `fadeSlideIn 0.3s ease-out ${i * 50}ms both`,
                }}
              >
                <td className="py-2 px-2 font-mono text-gray-500">
                  {pt.position_scheduled || i + 1}
                </td>
                <td className="py-2 px-2 text-gray-100 truncate max-w-[200px]">
                  {t.title}
                </td>
                <td className="py-2 px-2 text-gray-300 truncate max-w-[160px]">
                  {t.artist}
                </td>
                <td className="py-2 px-2">
                  <CamelotBadge code={effKey} />
                </td>
                <td className="py-2 px-2 font-mono text-gray-200">
                  {effBpm ? Number(effBpm).toFixed(0) : "--"}
                </td>
                <td className="py-2 px-2 font-mono text-gray-200">
                  {effEnergy != null ? Math.round(Number(effEnergy)) : "--"}
                </td>
                <td className="py-2 px-2 text-xs text-gray-500">
                  {t.analysis_source || "-"}
                </td>
              </tr>,
            ];
          })}
        </tbody>
      </table>

      <style>{`
        @keyframes fadeSlideIn {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

// --- Main ScheduleStep ---
export default function ScheduleStep({ playlistId, playlist, onBack, onNext }) {
  const tracks = useMemo(() => {
    const pts = playlist?.tracks || [];
    return [...pts].sort(
      (a, b) =>
        (a.position_scheduled || a.position_original || 0) -
        (b.position_scheduled || b.position_original || 0)
    );
  }, [playlist]);

  const usedKeys = useMemo(() => {
    const keys = new Set();
    tracks.forEach((pt) => {
      const k = pt.key_override || pt.track?.key_camelot;
      if (k) keys.add(k);
    });
    return keys;
  }, [tracks]);

  const keySequence = useMemo(() => {
    return tracks.map((pt) => pt.key_override || pt.track?.key_camelot).filter(Boolean);
  }, [tracks]);

  const mixScore = playlist?.mix_score ? Number(playlist.mix_score) : 0;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-1">Results</h2>
      <p className="text-gray-400 text-sm mb-8">
        Your optimized track order
      </p>

      {/* Score + Wheel side by side */}
      <div className="flex flex-col md:flex-row items-center justify-center gap-8 mb-8">
        <MixScoreGauge score={mixScore} />
        <CamelotWheel usedKeys={usedKeys} keySequence={keySequence} />
      </div>

      {/* Results table */}
      <ResultsTable tracks={tracks} />

      {/* Export + navigation */}
      <div className="mt-8">
        <ExportButtons playlistId={playlistId} playlistName={playlist?.name} />
      </div>

      <div className="mt-6 flex justify-between">
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-gray-200 transition"
        >
          &larr; Back to Customize
        </button>
      </div>
    </div>
  );
}
