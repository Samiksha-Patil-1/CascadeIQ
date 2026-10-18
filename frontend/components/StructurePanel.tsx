"use client";

import React, { useState } from "react";
import { AlertTriangle, RefreshCw, Layers, Award, ShieldAlert, Info } from "lucide-react";
import { NodeModel } from "@/lib/types";

interface StructurePanelProps {
  structure: {
    cycles: string[][];
    layers: string[][];
    single_points_of_failure: string[];
    articulation_points: string[];
    pagerank_reversed: Record<string, number>;
    betweenness: Record<string, number>;
  } | null;
  selectedNode?: NodeModel | null;
  onFocusNode: (nodeId: string) => void;
}

export function StructurePanel({ structure, selectedNode, onFocusNode }: StructurePanelProps) {
  const [activeTab, setActiveTab] = useState<"spof" | "cycles" | "layers" | "centrality" | "node">(
    selectedNode ? "node" : "spof"
  );

  const [prevNodeId, setPrevNodeId] = useState<string | null>(null);
  if (selectedNode && selectedNode.id !== prevNodeId) {
    setPrevNodeId(selectedNode.id);
    setActiveTab("node");
  }

  if (!structure) {
    return (
      <div className="p-4 rounded-xl bg-[#121826] border border-[#1F2937] animate-pulse h-64" />
    );
  }

  const spofCount = structure.single_points_of_failure?.length ?? 0;
  const cycleCount = structure.cycles?.length ?? 0;
  const layerCount = structure.layers?.length ?? 0;

  return (
    <div className="rounded-xl bg-[#121826] border border-[#1F2937] overflow-hidden flex flex-col select-none shadow-xl">
      {/* Tabs */}
      <div className="flex border-b border-[#1F2937] bg-[#0B0F17] text-xs">
        {selectedNode && (
          <button
            onClick={() => setActiveTab("node")}
            className={`flex-1 py-2.5 px-2 font-semibold flex items-center justify-center gap-1 transition-colors ${
              activeTab === "node"
                ? "text-indigo-400 border-b-2 border-indigo-500 bg-[#121826]"
                : "text-[#9CA3AF] hover:text-white"
            }`}
          >
            <Info className="w-3.5 h-3.5" />
            Service
          </button>
        )}

        <button
          onClick={() => setActiveTab("spof")}
          className={`flex-1 py-2.5 px-2 font-semibold flex items-center justify-center gap-1 transition-colors ${
            activeTab === "spof"
              ? "text-rose-400 border-b-2 border-rose-500 bg-[#121826]"
              : "text-[#9CA3AF] hover:text-white"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          SPOFs ({spofCount})
        </button>

        <button
          onClick={() => setActiveTab("cycles")}
          className={`flex-1 py-2.5 px-2 font-semibold flex items-center justify-center gap-1 transition-colors ${
            activeTab === "cycles"
              ? "text-amber-400 border-b-2 border-amber-500 bg-[#121826]"
              : "text-[#9CA3AF] hover:text-white"
          }`}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Cycles ({cycleCount})
        </button>

        <button
          onClick={() => setActiveTab("layers")}
          className={`flex-1 py-2.5 px-2 font-semibold flex items-center justify-center gap-1 transition-colors ${
            activeTab === "layers"
              ? "text-indigo-400 border-b-2 border-indigo-500 bg-[#121826]"
              : "text-[#9CA3AF] hover:text-white"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Layers ({layerCount})
        </button>

        <button
          onClick={() => setActiveTab("centrality")}
          className={`flex-1 py-2.5 px-2 font-semibold flex items-center justify-center gap-1 transition-colors ${
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
        {activeTab === "node" && selectedNode && (
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1F2937] space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">{selectedNode.name}</span>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-[#818CF8]">
                  Tier {selectedNode.tier}
                </span>
              </div>
              <p className="font-mono text-[11px] text-[#9CA3AF]">ID: {selectedNode.id}</p>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#1F2937] text-[11px] font-mono">
                <div>
                  <span className="text-[#9CA3AF]">Type: </span>
                  <span className="text-white capitalize">{selectedNode.type}</span>
                </div>
                <div>
                  <span className="text-[#9CA3AF]">Owner: </span>
                  <span className="text-white">{selectedNode.owner}</span>
                </div>
                <div>
                  <span className="text-[#9CA3AF]">Replicas: </span>
                  <span className="text-white">{selectedNode.replicas}</span>
                </div>
                <div>
                  <span className="text-[#9CA3AF]">Failover Q: </span>
                  <span className="text-white">{(selectedNode.failover_quality * 100).toFixed(0)}%</span>
                </div>
                <div>
                  <span className="text-[#9CA3AF]">MTBF: </span>
                  <span className="text-white">{selectedNode.mtbf_hours}h</span>
                </div>
                <div>
                  <span className="text-[#9CA3AF]">MTTR: </span>
                  <span className="text-white">{selectedNode.mttr_minutes}m</span>
                </div>
                <div>
                  <span className="text-[#9CA3AF]">SLO Floor: </span>
                  <span className="text-white">{(selectedNode.slo_floor * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-[#9CA3AF]">User-Facing: </span>
                  <span className="text-white">{selectedNode.user_facing ? "Yes" : "No"}</span>
                </div>
              </div>
              {selectedNode.revenue_per_min > 0 && (
                <div className="pt-2 border-t border-[#1F2937] text-[11px] font-mono text-emerald-400">
                  Revenue Flow: ${(selectedNode.revenue_per_min * 60).toLocaleString()}/hr
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "spof" && (
          <div className="space-y-3">
            <p className="text-[#9CA3AF] text-[11px]">
              Services without alternative providers that critical capabilities transitively depend on:
            </p>
            {spofCount === 0 ? (
              <div className="p-4 rounded-lg bg-[#0B0F17] border border-[#1F2937] text-center text-[#9CA3AF]">
                No single points of failure detected. System has full redundancy.
              </div>
            ) : (
              structure.single_points_of_failure.map((spof, idx) => (
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
              ))
            )}
          </div>
        )}

        {activeTab === "cycles" && (
          <div className="space-y-3">
            <p className="text-[#9CA3AF] text-[11px]">
              Circular dependency loops detected via Tarjan's SCC algorithm:
            </p>
            {cycleCount === 0 ? (
              <div className="p-4 rounded-lg bg-[#0B0F17] border border-[#1F2937] text-center text-[#9CA3AF]">
                No circular dependency loops detected (Clean DAG compliant).
              </div>
            ) : (
              structure.cycles.map((cyc, idx) => (
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
              ))
            )}
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
