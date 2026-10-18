"use client";

import React, { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { ExplainerModal } from "@/components/ExplainerModal";
import { GraphCanvas } from "@/components/GraphCanvas";
import { TimelineScrubber } from "@/components/TimelineScrubber";
import { KpiCards } from "@/components/KpiCards";
import { WhyChainDrawer } from "@/components/WhyChainDrawer";
import { StructurePanel } from "@/components/StructurePanel";
import { RiskBoard } from "@/components/RiskBoard";
import { PlannerView } from "@/components/PlannerView";
import { CompareView } from "@/components/CompareView";
import {
  fetchGraph,
  fetchStructure,
  runSimulation,
  fetchWhyNode,
  fetchRiskRanking,
  runOptimize,
  runCompare,
} from "@/lib/api";
import { GraphModel, MitigationItem, RiskRankingItem, SimulatedNode, SimulationResult } from "@/lib/types";
import { Play, ShieldAlert } from "lucide-react";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<string>("sim");
  const [isExplainerOpen, setIsExplainerOpen] = useState<boolean>(false);

  // Core Data
  const [graph, setGraph] = useState<GraphModel | null>(null);
  const [structure, setStructure] = useState<any>(null);
  const [rankings, setRankings] = useState<RiskRankingItem[]>([]);

  // Simulation State
  const [selectedFailureNode, setSelectedFailureNode] = useState<string>("auth-db");
  const [severity, setSeverity] = useState<number>(1.0);
  const [outageMinutes, setOutageMinutes] = useState<number>(30);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simulatedNodes, setSimulatedNodes] = useState<Record<string, SimulatedNode>>({});
  const [activePath, setActivePath] = useState<Array<{ source: string; target: string }>>([]);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Scrubber / Replay
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(4);

  // Inspector & Why-Chain
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [whyData, setWhyData] = useState<any>(null);

  // Optimizer & Compare
  const [budget, setBudget] = useState<number>(20);
  const [plan, setPlan] = useState<Array<{ item: MitigationItem; marginal_gain: number; cumulative_cost: number }>>([]);
  const [curve, setCurve] = useState<Array<{ cost: number; expected_loss: number }>>([]);
  const [kneeIndex, setKneeIndex] = useState<number>(0);
  const [baselineLoss, setBaselineLoss] = useState<number>(0);
  const [finalLoss, setFinalLoss] = useState<number>(0);
  const [compareData, setCompareData] = useState<any>(null);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [isComparing, setIsComparing] = useState<boolean>(false);

  // Update animated node states and active edges up to time t
  const updateSimStateAtTime = (sim: SimulationResult, t: number) => {
    if (!sim) return;
    const nodeMap: Record<string, SimulatedNode> = {};
    for (const n of sim.nodes) {
      nodeMap[n.id] = { ...n, damage: 0.0, state: "healthy" };
    }

    const activeEdges: Array<{ source: string; target: string }> = [];

    for (const ev of sim.timeline) {
      if (ev.t_s <= t) {
        if (nodeMap[ev.node_id]) {
          nodeMap[ev.node_id].damage = ev.damage;
          nodeMap[ev.node_id].state = ev.to as any;

          const nObj = sim.nodes.find((x) => x.id === ev.node_id);
          if (nObj?.parent_edge) {
            activeEdges.push({
              source: nObj.parent_edge[0],
              target: nObj.parent_edge[1],
            });
          }
        }
      }
    }

    setSimulatedNodes(nodeMap);
    setActivePath(activeEdges);
  };

  // Initial load
  useEffect(() => {
    async function loadData() {
      try {
        const g = await fetchGraph("ecommerce-platform");
        setGraph(g);

        const st = await fetchStructure("ecommerce-platform");
        setStructure(st);

        const rk = await fetchRiskRanking("ecommerce-platform");
        setRankings(rk.rankings || []);

        // Run initial default simulation on auth-db
        const scenario = {
          failures: [{ node_id: "auth-db", severity: 1.0, start_s: 0.0 }],
          outage_minutes: 30,
          seed: 42,
        };
        const sim = await runSimulation("ecommerce-platform", scenario);
        setSimResult(sim);
        updateSimStateAtTime(sim, 30 * 60);
      } catch (err) {
        console.error("Failed to load initial data", err);
      }
    }
    loadData();
  }, []);

  // Replay animation clock
  useEffect(() => {
    if (!isPlaying || !simResult) return;

    const interval = setInterval(() => {
      setCurrentTime((prev) => {
        const nextTime = prev + (0.5 * playbackSpeed);
        const maxTime = outageMinutes * 60;
        if (nextTime >= maxTime) {
          setIsPlaying(false);
          updateSimStateAtTime(simResult, maxTime);
          return maxTime;
        }
        updateSimStateAtTime(simResult, nextTime);
        return nextTime;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying, simResult, playbackSpeed, outageMinutes]);

  // Handle simulation run
  const handleRunSimulation = async (nodeId?: string) => {
    const targetNode = nodeId || selectedFailureNode;
    setIsSimulating(true);
    try {
      const scenario = {
        failures: [{ node_id: targetNode, severity, start_s: 0.0 }],
        outage_minutes: outageMinutes,
        seed: 42,
      };
      const sim = await runSimulation("ecommerce-platform", scenario);
      setSimResult(sim);
      setCurrentTime(0);
      setIsPlaying(true);
      updateSimStateAtTime(sim, 0);
    } catch (e) {
      console.error("Simulation run error", e);
    } finally {
      setIsSimulating(false);
    }
  };

  // Handle node selection for why chain
  const handleSelectNode = async (nodeId: string) => {
    setSelectedNodeId(nodeId);
    try {
      const scenario = {
        failures: [{ node_id: selectedFailureNode, severity, start_s: 0.0 }],
        outage_minutes: outageMinutes,
        seed: 42,
      };
      const whyRes = await fetchWhyNode("ecommerce-platform", nodeId, scenario);
      setWhyData(whyRes);
    } catch (e) {
      console.error("Failed to fetch why data", e);
    }
  };

  // Run Optimizer
  const handleRunOptimize = async () => {
    setIsOptimizing(true);
    try {
      const scenario = {
        failures: [{ node_id: selectedFailureNode, severity, start_s: 0.0 }],
        outage_minutes: outageMinutes,
        seed: 42,
      };
      const optRes = await runOptimize("ecommerce-platform", scenario, budget);
      setPlan(optRes.plan || []);
      setCurve(optRes.curve || []);
      setKneeIndex(optRes.knee_index || 0);
      setBaselineLoss(optRes.baseline_loss || 0);
      setFinalLoss(optRes.final_loss || 0);
    } catch (e) {
      console.error("Optimize error", e);
    } finally {
      setIsOptimizing(false);
    }
  };

  // Run Compare
  const handleRunCompare = async (customPlan?: MitigationItem[]) => {
    setIsComparing(true);
    try {
      const scenario = {
        failures: [{ node_id: selectedFailureNode, severity, start_s: 0.0 }],
        outage_minutes: outageMinutes,
        seed: 42,
      };
      const itemsToApply = customPlan || plan.map((p) => p.item);
      const compRes = await runCompare("ecommerce-platform", scenario, itemsToApply);
      setCompareData(compRes);
      setActiveTab("compare");
    } catch (e) {
      console.error("Compare error", e);
    } finally {
      setIsComparing(false);
    }
  };

  // Quick Demo Trigger
  const handleQuickDemo = () => {
    setSelectedFailureNode("auth-db");
    setSeverity(1.0);
    setActiveTab("sim");
    handleRunSimulation("auth-db");
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0B0F17] text-[#E5E7EB]">
      {/* Navbar with Explainer & Quick Demo buttons */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenExplainer={() => setIsExplainerOpen(true)}
        onQuickDemo={handleQuickDemo}
        isSimulating={isSimulating}
      />

      {/* Explainer Modal */}
      <ExplainerModal
        isOpen={isExplainerOpen}
        onClose={() => setIsExplainerOpen(false)}
        onRunDemo={handleQuickDemo}
      />

      {/* TAB 1: SIMULATION LAB */}
      {activeTab === "sim" && (
        <main className="flex-1 flex flex-col p-6 max-w-7xl w-full mx-auto gap-5">
          {/* Top KPI Cards */}
          <KpiCards summary={simResult?.summary || null} />

          {/* Canvas & Controls Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-5 flex-1 min-h-[520px]">
            {/* Graph Canvas Container */}
            <div className="lg:col-span-3 flex flex-col rounded-2xl border border-[#1F2937] bg-[#0B0F17] overflow-hidden shadow-2xl relative">
              <div className="px-5 py-3 border-b border-[#1F2937] bg-[#121826] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    Failure Cascade Studio
                  </span>
                </div>
                <span className="text-[11px] font-mono text-[#9CA3AF]">
                  34-Node E-Commerce Platform | Seed 42
                </span>
              </div>

              <div className="flex-1 relative min-h-[460px]">
                <GraphCanvas
                  graph={graph}
                  simulatedNodes={simulatedNodes}
                  activePath={activePath}
                  selectedNodeId={selectedNodeId}
                  onSelectNode={handleSelectNode}
                />
              </div>

              {/* Timeline Scrubber */}
              <div className="p-3 bg-[#0B0F17] border-t border-[#1F2937]">
                <TimelineScrubber
                  timeline={simResult?.timeline || []}
                  currentTime={currentTime}
                  maxTime={outageMinutes * 60}
                  onTimeChange={(t) => {
                    setCurrentTime(t);
                    if (simResult) updateSimStateAtTime(simResult, t);
                  }}
                  isPlaying={isPlaying}
                  onTogglePlay={() => setIsPlaying(!isPlaying)}
                  onReset={() => {
                    setIsPlaying(false);
                    setCurrentTime(0);
                    if (simResult) updateSimStateAtTime(simResult, 0);
                  }}
                  speed={playbackSpeed}
                  onSpeedChange={setPlaybackSpeed}
                />
              </div>
            </div>

            {/* Right Side Control & Why-Chain Column */}
            <div className="flex flex-col gap-4">
              {/* Failure Injection Card */}
              <div className="p-5 rounded-2xl bg-[#121826] border border-[#1F2937] shadow-xl space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-[#1F2937]">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                    Inject Fault
                  </h3>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-medium text-[#9CA3AF]">Target Node</label>
                  <select
                    value={selectedFailureNode}
                    onChange={(e) => setSelectedFailureNode(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[#0B0F17] border border-[#1F2937] text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
                  >
                    {graph?.nodes.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.name} ({n.id})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-[11px] font-mono">
                    <span className="text-[#9CA3AF]">Severity:</span>
                    <span className="font-bold text-rose-400">{(severity * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0.1}
                    max={1.0}
                    step={0.05}
                    value={severity}
                    onChange={(e) => setSeverity(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-[#0B0F17] rounded-lg appearance-none cursor-pointer accent-rose-500"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-[11px] font-mono">
                    <span className="text-[#9CA3AF]">Outage Duration:</span>
                    <span className="font-bold text-amber-400">{outageMinutes} min</span>
                  </div>
                  <input
                    type="range"
                    min={5}
                    max={120}
                    step={5}
                    value={outageMinutes}
                    onChange={(e) => setOutageMinutes(parseInt(e.target.value, 10))}
                    className="w-full h-1.5 bg-[#0B0F17] rounded-lg appearance-none cursor-pointer accent-amber-500"
                  />
                </div>

                <button
                  onClick={() => handleRunSimulation()}
                  disabled={isSimulating}
                  className="w-full py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-rose-600 to-red-600 text-white shadow-lg shadow-rose-600/25 hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  {isSimulating ? "Simulating..." : "Trigger Outage & Replay"}
                </button>
              </div>

              {/* Why-Chain Explainer */}
              <WhyChainDrawer
                whyData={whyData}
                onClose={() => setWhyData(null)}
                onFocusNode={handleSelectNode}
              />
            </div>
          </div>
        </main>
      )}

      {/* TAB 2: ARCHITECTURE EXPLORER */}
      {activeTab === "explorer" && (
        <main className="flex-1 flex flex-col p-6 max-w-7xl w-full mx-auto gap-5">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 flex-1 min-h-[550px]">
            <div className="lg:col-span-2 rounded-2xl border border-[#1F2937] bg-[#0B0F17] overflow-hidden shadow-2xl relative">
              <GraphCanvas
                graph={graph}
                selectedNodeId={selectedNodeId}
                onSelectNode={handleSelectNode}
              />
            </div>
            <StructurePanel
              structure={structure}
              selectedNode={graph?.nodes.find((n) => n.id === selectedNodeId) || null}
              onFocusNode={handleSelectNode}
            />
          </div>
        </main>
      )}

      {/* TAB 3: RISK BOARD */}
      {activeTab === "risk" && (
        <RiskBoard
          rankings={rankings}
          onSelectNodeForSimulation={(nodeId) => {
            setSelectedFailureNode(nodeId);
            setActiveTab("sim");
            handleRunSimulation(nodeId);
          }}
          isLoading={rankings.length === 0}
        />
      )}

      {/* TAB 4: MITIGATION PLANNER */}
      {activeTab === "planner" && (
        <PlannerView
          budget={budget}
          onBudgetChange={setBudget}
          onRunOptimize={handleRunOptimize}
          plan={plan}
          curve={curve}
          kneeIndex={kneeIndex}
          baselineLoss={baselineLoss}
          finalLoss={finalLoss}
          onApplyPlan={(appliedPlan) => handleRunCompare(appliedPlan)}
          isOptimizing={isOptimizing}
        />
      )}

      {/* TAB 5: COMPARE VIEW */}
      {activeTab === "compare" && (
        <CompareView
          graph={graph}
          compareData={compareData}
          plan={plan.map((p) => p.item)}
          onRunCompare={() => handleRunCompare()}
          isLoading={isComparing}
        />
      )}
    </div>
  );
}
