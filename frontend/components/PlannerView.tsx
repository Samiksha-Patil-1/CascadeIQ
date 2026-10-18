"use client";

import React, { useState } from "react";
import { Sliders, Sparkles, CheckSquare, Square, Play } from "lucide-react";
import { MitigationItem } from "@/lib/types";

interface PlannerViewProps {
  budget: number;
  onBudgetChange: (b: number) => void;
  onRunOptimize: () => void;
  plan: Array<{
    item: MitigationItem;
    marginal_gain: number;
    cumulative_cost: number;
  }>;
  curve: Array<{ cost: number; expected_loss: number }>;
  kneeIndex: number;
  baselineLoss: number;
  finalLoss: number;
  onApplyPlan: (plan: MitigationItem[]) => void;
  isOptimizing: boolean;
}

export function PlannerView({
  budget,
  onBudgetChange,
  onRunOptimize,
  plan,
  curve,
  kneeIndex,
  baselineLoss,
  finalLoss,
  onApplyPlan,
  isOptimizing,
}: PlannerViewProps) {
  const [selectedItemIds, setSelectedItemIds] = useState<Record<string, boolean>>({});

  const toggleItem = (id: string) => {
    setSelectedItemIds((prev) => ({
      ...prev,
      [id]: prev[id] !== undefined ? !prev[id] : false,
    }));
  };

  const totalCost = plan
    .filter((p) => selectedItemIds[p.item.id] !== false)
    .reduce((sum, p) => sum + p.item.cost, 0);

  const pctSaved = baselineLoss > 0
    ? Math.max(0, ((baselineLoss - finalLoss) / baselineLoss) * 100)
    : 0;

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full select-none">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 rounded-2xl bg-[#121826] border border-[#1F2937]">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-[#818CF8]" />
            Intervention Optimizer (CELF Lazy Greedy)
          </h2>
          <p className="text-xs text-[#9CA3AF]">
            Allocate engineering reliability effort points to minimize expected cascading outage loss.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-1 w-48">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-[#9CA3AF]">Effort Budget:</span>
              <span className="font-bold text-[#818CF8]">{budget} pts</span>
            </div>
            <input
              type="range"
              min={2}
              max={50}
              step={1}
              value={budget}
              onChange={(e) => onBudgetChange(parseInt(e.target.value, 10))}
              className="h-1.5 bg-[#0B0F17] rounded-lg appearance-none cursor-pointer accent-[#818CF8]"
            />
          </div>

          <button
            onClick={onRunOptimize}
            disabled={isOptimizing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 active:scale-95 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            {isOptimizing ? "Optimizing..." : "Compute Best Plan"}
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#121826] border border-[#1F2937]">
          <span className="text-xs text-[#9CA3AF]">Baseline Expected Loss</span>
          <p className="text-xl font-bold font-mono text-rose-400 mt-1">
            ${baselineLoss.toLocaleString()}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[#121826] border border-[#1F2937]">
          <span className="text-xs text-[#9CA3AF]">Optimized Expected Loss</span>
          <p className="text-xl font-bold font-mono text-emerald-400 mt-1">
            ${finalLoss.toLocaleString()}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[#121826] border border-[#1F2937]">
          <span className="text-xs text-[#9CA3AF]">Expected Loss Reduction</span>
          <p className="text-xl font-bold font-mono text-cyan-400 mt-1">
            -{pctSaved.toFixed(1)}%
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[#121826] border border-[#1F2937]">
          <span className="text-xs text-[#9CA3AF]">Allocated Budget</span>
          <p className="text-xl font-bold font-mono text-white mt-1">
            {totalCost} / {budget} pts
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Candidates Checklist */}
        <div className="flex flex-col rounded-xl bg-[#121826] border border-[#1F2937] p-4 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-[#1F2937] mb-3">
            <h3 className="text-sm font-bold text-white">Recommended Interventions (Ranked by Gain/Cost)</h3>
            <span className="text-xs font-mono text-gray-400">{plan.length} items</span>
          </div>

          <div className="space-y-2 flex-1 overflow-y-auto max-h-[350px]">
            {plan.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-[#9CA3AF] text-xs">
                Click "Compute Best Plan" to run optimizer.
              </div>
            ) : (
              plan.map((p, idx) => {
                const isChecked = selectedItemIds[p.item.id] !== false;
                const targetDesc = p.item.target.edge
                  ? `${p.item.target.edge[0]} -> ${p.item.target.edge[1]}`
                  : p.item.target.node;

                return (
                  <div
                    key={idx}
                    onClick={() => toggleItem(p.item.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                      isChecked
                        ? "bg-[#0B0F17] border-indigo-500/40"
                        : "bg-[#0B0F17]/40 border-gray-800 opacity-60"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-[#818CF8]" />
                      ) : (
                        <Square className="w-4 h-4 text-gray-500" />
                      )}
                      <div>
                        <span className="text-xs font-bold text-white capitalize">
                          {p.item.type.replace(/_/g, " ")}
                        </span>
                        <p className="font-mono text-[11px] text-[#9CA3AF]">{targetDesc}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-right">
                      <div>
                        <span className="text-[10px] text-gray-400">Cost</span>
                        <p className="font-mono text-xs font-bold text-white">{p.item.cost} pts</p>
                      </div>
                      <div>
                        <span className="text-[10px] text-gray-400">Marginal Gain</span>
                        <p className="font-mono text-xs font-bold text-emerald-400">
                          -${p.marginal_gain.toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {plan.length > 0 && (
            <button
              onClick={() => onApplyPlan(plan.map((p) => p.item))}
              className="mt-4 w-full py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20 hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Apply Plan & Open Compare View
            </button>
          )}
        </div>

        {/* Cost-Benefit Curve */}
        <div className="flex flex-col rounded-xl bg-[#121826] border border-[#1F2937] p-4 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-[#1F2937] mb-3">
            <h3 className="text-sm font-bold text-white">Cost-Benefit Curve & Knee Point</h3>
            <span className="text-xs text-amber-300 font-mono">
              Knee Point: Step #{kneeIndex}
            </span>
          </div>

          <div className="flex-1 flex flex-col justify-center min-h-[300px]">
            {curve.length <= 1 ? (
              <div className="flex items-center justify-center text-xs text-[#9CA3AF]">
                Optimizer curve will plot here after evaluation.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="h-56 w-full flex items-end gap-2 pt-4 px-2 border-b border-l border-gray-700">
                  {curve.map((pt, idx) => {
                    const maxLoss = Math.max(...curve.map((c) => c.expected_loss), 1);
                    const heightPct = (pt.expected_loss / maxLoss) * 100;
                    const isKnee = idx === kneeIndex;

                    return (
                      <div
                        key={idx}
                        className="flex-1 flex flex-col items-center justify-end h-full group relative"
                      >
                        <div
                          className={`w-full rounded-t transition-all ${
                            isKnee
                              ? "bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.6)]"
                              : "bg-indigo-500/60 hover:bg-indigo-400"
                          }`}
                          style={{ height: `${heightPct}%` }}
                        />
                        <span className="text-[9px] font-mono text-gray-400 mt-1">
                          {pt.cost}p
                        </span>

                        {/* Tooltip */}
                        <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-black text-white text-[10px] font-mono px-2 py-1 rounded border border-gray-700 pointer-events-none whitespace-nowrap z-20">
                          Cost: {pt.cost} pts | Loss: ${pt.expected_loss}
                          {isKnee && " (KNEE)"}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="flex items-center justify-between text-[11px] text-[#9CA3AF] px-2 font-mono">
                  <span>Spend: 0 pts</span>
                  <span className="text-amber-400">★ Optimal Knee: Diminishing Returns</span>
                  <span>Spend: {curve[curve.length - 1]?.cost} pts</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
