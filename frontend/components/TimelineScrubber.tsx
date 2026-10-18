"use client";

import React from "react";
import { Play, Pause, RotateCcw } from "lucide-react";
import { TimelineEvent } from "@/lib/types";

interface TimelineScrubberProps {
  timeline: TimelineEvent[];
  currentTime: number;
  maxTime: number;
  onTimeChange: (time: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onReset: () => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
}

export function TimelineScrubber({
  timeline,
  currentTime,
  maxTime,
  onTimeChange,
  isPlaying,
  onTogglePlay,
  onReset,
  speed,
  onSpeedChange,
}: TimelineScrubberProps) {
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const speeds = [1, 4, 16];

  return (
    <div className="flex flex-col md:flex-row items-center gap-4 px-5 py-3 rounded-xl bg-[#121826] border border-[#1F2937] shadow-lg select-none">
      {/* Play/Pause & Reset Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={onTogglePlay}
          className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors active:scale-95 shadow"
          title={isPlaying ? "Pause" : "Play Replay"}
        >
          {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
        </button>
        <button
          onClick={onReset}
          className="p-2 rounded-lg bg-[#1F2937] hover:bg-gray-700 text-gray-300 transition-colors active:scale-95"
          title="Reset to 00:00"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Scrubber Track */}
      <div className="flex-1 w-full flex items-center gap-3">
        <span className="font-mono text-xs text-gray-300 w-12 text-right">
          {formatTime(currentTime)}
        </span>

        <div className="relative flex-1 flex items-center">
          <input
            type="range"
            min={0}
            max={Math.max(maxTime, 1)}
            step={0.5}
            value={currentTime}
            onChange={(e) => onTimeChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#1F2937] rounded-lg appearance-none cursor-pointer accent-[#818CF8]"
          />

          {/* Event Tick Markers */}
          {timeline.map((ev, idx) => {
            if (maxTime <= 0) return null;
            const pct = (ev.t_s / maxTime) * 100;
            return (
              <div
                key={idx}
                className="absolute w-1.5 h-1.5 rounded-full bg-rose-500/80 pointer-events-none -translate-x-1/2"
                style={{ left: `${pct}%` }}
                title={`${ev.node_id} -> ${ev.to} at ${ev.t_s.toFixed(1)}s`}
              />
            );
          })}
        </div>

        <span className="font-mono text-xs text-[#9CA3AF] w-12">
          {formatTime(maxTime)}
        </span>
      </div>

      {/* Speed Selector */}
      <div className="flex items-center gap-1 bg-[#0B0F17] p-1 rounded-lg border border-[#1F2937]">
        {speeds.map((s) => (
          <button
            key={s}
            onClick={() => onSpeedChange(s)}
            className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold transition-all ${
              speed === s
                ? "bg-[#1F2937] text-[#818CF8] border border-indigo-500/30"
                : "text-[#9CA3AF] hover:text-white"
            }`}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  );
}
