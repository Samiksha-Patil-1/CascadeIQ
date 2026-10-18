"use client";

import React, { useState } from "react";
import { AlertTriangle, RefreshCw, Layers, Award, ShieldAlert } from "lucide-react";

interface StructurePanelProps {
  structure: {
    cycles: string[][];
    layers: string[][];
    single_points_of_failure: string[];
    articulation_points: string[];
    pagerank_reversed: Record<string, number>;
    betweenness: Record<string, number>;
  } | null;
  onFocusNode: (nodeId: string) => void;
}

export function StructurePanel({ structure, onFocusNode }: StructurePanelProps) {
  const [activeTab, setActiveTab] = useState<"spof" | "cycles" | "layers" | "centrality">("spof");

  if (!structure) {
    return (
      <div className="p-4 rounded-xl bg-[#121826] border border-[#1F2937] animate-pulse h-64" />
    );
  }

  return (
    <div className="rounded-xl bg-[#121826] border border-[#1F2937] overflow-hidden flex flex-col select-none shadow-xl">
      {/* Tabs */}
      <div className="flex border-b border-[#1F2937] bg-[#0B0F17] text-xs">
        <button
          onClick={() => setActiveTab("spof")}
          className={`flex-1 py-2.5 px-3 font-semibold flex items-center justify-center gap-1.5 transition-colors ${
            activeTab === "spof"
              ? "text-rose-400 border-b-2 border-rose-500 bg-[#121826]"
              : "text-[#9CA3AF] hover:text-white"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          SPOFs ({structure.single_points_of_failure.length})
        </button>

        <button
          onClick={() => setActiveTab("cycles")}
          className={`flex-1 py-2.5 px-3 font-semibold flex items-center justify-center gap-1.5 transition-colors ${
            activeTab === "cycles"
              ? "text-amber-400 border-b-2 border-amber-500 bg-[#121826]"
              : "text-[#9CA3AF] hover:text-white"
          }`}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Cycles ({structure.cycles.length})
        </button>

        <button
          onClick={() => setActiveTab("layers")}
          className={`flex-1 py-2.5 px-3 font-semibold flex items-center justify-center gap-1.5 transition-colors ${
            activeTab === "layers"
              ? "text-indigo-400 border-b-2 border-indigo-500 bg-[#121826]"
              : "text-[#9CA3AF] hover:text-white"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Layers ({structure.layers.length})
        </button>

        <button
          onClick={() => setActiveTab("centrality")}
          className={`flex-1 py-2.5 px-3 font-semibold flex items-center justify-center gap-1.5 transition-colors ${
            activeTab === "centrality"
              ? "text-cyan-400 border-b-2 border-cyan-500 bg-[#121826]"
              : "text-[#9CA3AF] hover:text-white"
          }`}
        >
          <Award className="w-3.5 h-3.5" />
          Centrality
        </button>
      </div>

      {/* Tab Content */}
      <div className="p-4 flex-1 overflow-y-auto max-h-[360px] text-xs">
        {activeTab === "spof" && (
          <div className="space-y-3">
            <p className="text-[#9CA3AF] text-[11px]">
              Services without alternative providers that critical capabilities transitively depend on:
            </p>
            {structure.single_points_of_failure.map((spof, idx) => (
              <div
                key={idx}
                onClick={() => onFocusNode(spof)}
                className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 hover:border-rose-500/60 transition-colors cursor-pointer flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <span className="font-mono font-bold text-white">{spof}</span>
                </div>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300">
                  Critical Vulnerability
                </span>
              </div>
            ))}
          </div>
        )}

        {activeTab === "cycles" && (
          <div className="space-y-3">
            <p className="text-[#9CA3AF] text-[11px]">
              Circular dependency loops detected via Tarjan's SCC algorithm:
            </p>
            {structure.cycles.map((cyc, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-1.5"
              >
                <div className="flex items-center gap-2 text-amber-400 font-bold">
                  <RefreshCw className="w-3.5 h-3.5" />
                  Cycle #{idx + 1} ({cyc.length} services)
                </div>
                <div className="flex flex-wrap gap-1 font-mono text-[11px]">
                  {cyc.map((n, i) => (
                    <button
                      key={i}
                      onClick={() => onFocusNode(n)}
                      className="px-2 py-0.5 rounded bg-[#0B0F17] text-white hover:text-amber-300 border border-gray-700"
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === "layers" && (
          <div className="space-y-2">
            {structure.layers.map((layer, idx) => (
              <div key={idx} className="p-2 rounded bg-[#0B0F17] border border-[#1F2937]">
                <div className="font-mono text-[10px] text-[#818CF8] mb-1">
                  Layer {idx} ({layer.length} components)
                </div>
                <div className="flex flex-wrap gap-1">
                  {layer.map((n, i) => (
                    <button
                      key={i}
                      onClick={() => onFocusNode(n)}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#121826] text-gray-300 hover:text-white"
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === "centrality" && (
          <div className="space-y-2 font-mono">
            <p className="text-[#9CA3AF] text-[11px] font-sans">
              Top components by reverse PageRank (dependency depth) and Betweenness:
            </p>
            {Object.entries(structure.pagerank_reversed)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 8)
              .map(([nodeId, score], idx) => (
                <div
                  key={idx}
                  onClick={() => onFocusNode(nodeId)}
                  className="p-2 rounded bg-[#0B0F17] border border-[#1F2937] hover:border-cyan-500/50 cursor-pointer flex items-center justify-between"
                >
                  <span className="text-white text-xs">{nodeId}</span>
                  <span className="text-cyan-400 text-xs">{(score * 100).toFixed(2)}%</span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
