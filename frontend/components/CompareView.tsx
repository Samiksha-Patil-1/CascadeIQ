"use client";

import React from "react";
import { GitCompare } from "lucide-react";
import { GraphCanvas } from "./GraphCanvas";
import { KpiCards } from "./KpiCards";
import { GraphModel, MitigationItem } from "@/lib/types";

interface CompareViewProps {
  graph: GraphModel | null;
  compareData: {
    baseline: any;
    mitigated: any;
    mitigated_graph?: GraphModel;
    delta: any;
    plan_cost: number;
  } | null;
  plan: MitigationItem[];
  onRunCompare: () => void;
  isLoading: boolean;
}

export function CompareView({
  graph,
  compareData,
  plan,
  onRunCompare,
  isLoading,
}: CompareViewProps) {

  if (!compareData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] p-8 text-center select-none">
        <GitCompare className="w-12 h-12 text-[#818CF8] mb-3 opacity-60 animate-bounce" />
        <h3 className="text-lg font-bold text-white mb-1">Baseline vs Mitigated Comparison</h3>
        <p className="text-xs text-[#9CA3AF] max-w-md mb-6">
          Compare the exact same failure scenario on the unmitigated baseline versus your proposed mitigation plan with identical random seeds.
        </p>
        <button
          onClick={onRunCompare}
          disabled={isLoading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/25 active:scale-95 transition-all"
        >
          {isLoading ? "Running Dual Simulation..." : "Run Side-by-Side Comparison"}
        </button>
      </div>
    );
  }

  // Construct map of node states at currentTime
  const getNodesAtTime = (sim: any, t: number) => {
    const nodeMap: Record<string, any> = {};
    if (!sim) return nodeMap;

    for (const n of sim.nodes) {
      nodeMap[n.id] = { ...n, damage: 0.0, state: "healthy" };
    }

    // Apply timeline events up to t
    for (const ev of sim.timeline) {
      if (ev.t_s <= t) {
        if (nodeMap[ev.node_id]) {
          nodeMap[ev.node_id].damage = ev.damage;
          nodeMap[ev.node_id].state = ev.to;
        }
      }
    }
    return nodeMap;
  };

  const baseNodes = getNodesAtTime(compareData.baseline, 1800);
  const mitNodes = getNodesAtTime(compareData.mitigated, 1800);

  return (
    <div className="flex flex-col gap-5 p-6 max-w-7xl mx-auto w-full select-none">
      {/* Top Delta Cards */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-emerald-500/20 text-emerald-400 font-mono text-xs font-bold">
              PROVEN QUANTITATIVE GAINS
            </span>
            <span className="text-xs text-[#9CA3AF]">
              Plan: {plan.length} items (Cost: {compareData.plan_cost} pts)
            </span>
          </div>

          <button
            onClick={onRunCompare}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
          >
            Re-run Compare
          </button>
        </div>

        <KpiCards
          summary={compareData.mitigated.summary}
          delta={compareData.delta}
          isCompareMode={true}
        />
      </div>

      {/* Split Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[420px]">
        {/* Baseline (Before) */}
        <div className="flex flex-col rounded-xl border border-rose-500/30 bg-[#0B0F17] overflow-hidden shadow-xl">
          <div className="px-4 py-2 border-b border-[#1F2937] bg-[#121826] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
              <span className="text-xs font-bold text-white">BEFORE (Baseline System)</span>
            </div>
            <span className="text-[11px] font-mono text-rose-400 font-bold">
              {compareData.baseline.summary.affected} affected ({compareData.baseline.summary.failed} failed)
            </span>
          </div>
          <div className="flex-1 relative">
            <GraphCanvas graph={graph} simulatedNodes={baseNodes} />
          </div>
        </div>

        {/* Mitigated (After) */}
        <div className="flex flex-col rounded-xl border border-emerald-500/30 bg-[#0B0F17] overflow-hidden shadow-xl">
          <div className="px-4 py-2 border-b border-[#1F2937] bg-[#121826] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-bold text-white">AFTER (Mitigated System)</span>
            </div>
            <span className="text-[11px] font-mono text-emerald-400 font-bold">
              {compareData.mitigated.summary.affected} affected (-{compareData.delta.pct_loss_reduction}% loss)
            </span>
          </div>
          <div className="flex-1 relative">
            <GraphCanvas graph={compareData.mitigated_graph || graph} simulatedNodes={mitNodes} />
          </div>
        </div>
      </div>
    </div>
  );
}
