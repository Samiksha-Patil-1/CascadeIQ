"use client";

import React from "react";
import { X, AlertCircle, ArrowDown } from "lucide-react";

interface WhyChainProps {
  whyData: {
    node_id: string;
    damage: number;
    state: string;
    chain: Array<{
      source: string;
      target: string;
      kind: string;
      strength: number;
      tau: number;
      delay_s: number;
    }>;
    top_contributors: Array<{
      provider: string;
      contribution: number;
      tau: number;
      provider_damage: number;
    }>;
    narrative: string;
  } | null;
  onClose: () => void;
  onFocusNode?: (nodeId: string) => void;
}

export function WhyChainDrawer({ whyData, onClose, onFocusNode }: WhyChainProps) {
  if (!whyData) return null;

  return (
    <div className="p-4 rounded-xl bg-[#121826] border border-[#1F2937] shadow-xl space-y-4 select-none">
      <div className="flex items-center justify-between pb-3 border-b border-[#1F2937]">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          <h3 className="text-sm font-bold text-white">Why Did {whyData.node_id} Fail?</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Narrative Card */}
      <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1F2937] text-xs text-[#E5E7EB] leading-relaxed">
        {whyData.narrative}
      </div>

      {/* Hop by Hop Chain */}
      {whyData.chain && whyData.chain.length > 0 && (
        <div className="space-y-2">
          <span className="text-[11px] font-semibold text-[#9CA3AF] uppercase tracking-wider">
            Cascade Transmission Path
          </span>
          <div className="space-y-1.5">
            {whyData.chain.map((hop, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-[#0B0F17] border border-[#1F2937] flex flex-col gap-1 hover:border-indigo-500/50 transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <button
                    onClick={() => onFocusNode && onFocusNode(hop.source)}
                    className="font-mono font-semibold text-white hover:text-indigo-400"
                  >
                    {hop.source}
                  </button>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/15 text-[#818CF8]">
                    {hop.kind}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-[#9CA3AF]">
                  <ArrowDown className="w-3 h-3 text-rose-400" />
                  <span>
                    Coupling w: <strong className="text-gray-200">{hop.strength}</strong>
                  </span>
                  <span>
                    Trans τ: <strong className="text-rose-400">{hop.tau}</strong>
                  </span>
                  <span>
                    Delay: <strong className="text-gray-200">{hop.delay_s}s</strong>
                  </span>
                </div>
                <button
                  onClick={() => onFocusNode && onFocusNode(hop.target)}
                  className="font-mono text-xs text-rose-300 self-start hover:underline mt-0.5"
                >
                  &rarr; relies on {hop.target}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Contributing Providers */}
      {whyData.top_contributors && whyData.top_contributors.length > 0 && (
        <div className="space-y-2">
          <span className="text-[11px] font-semibold text-[#9CA3AF] uppercase tracking-wider">
            Top Loss Contributors
          </span>
          <div className="space-y-1">
            {whyData.top_contributors.map((contrib, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-[#0B0F17] border border-[#1F2937] flex items-center justify-between text-xs font-mono"
              >
                <span className="text-gray-300">{contrib.provider}</span>
                <span className="text-rose-400 font-bold">
                  {(contrib.contribution * 100).toFixed(1)}% share
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
