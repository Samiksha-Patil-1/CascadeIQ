"use client";

import React, { useState } from "react";
import {
  X,
  Sparkles,
  ArrowRight,
  TrendingDown,
  Layers,
  DollarSign,
  AlertTriangle,
  Play,
} from "lucide-react";

interface ExplainerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunDemo: () => void;
}

export function ExplainerModal({ isOpen, onClose, onRunDemo }: ExplainerModalProps) {
  const [activeStep, setActiveStep] = useState(0);

  if (!isOpen) return null;

  const steps = [
    {
      title: "1. The Enterprise Problem",
      subtitle: "Why outages cascade invisibly in microservices",
      icon: AlertTriangle,
      content: (
        <div className="space-y-4 text-sm text-[#E5E7EB] leading-relaxed">
          <p>
            Modern enterprise architectures have dozens to thousands of services with tangled, often undocumented dependencies.
            When a downstream database or internal service slows down or crashes, the true blast radius is only discovered during an incident, at the worst possible moment.
          </p>
          <div className="p-4 rounded-xl bg-[#0B0F17] border border-[#1F2937] space-y-2">
            <h4 className="font-semibold text-amber-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" /> Traditional Limitations
            </h4>
            <ul className="list-disc pl-5 space-y-1 text-xs text-[#9CA3AF]">
              <li><strong className="text-gray-200">Chaos Engineering:</strong> Injects real faults in live environments (risky, slow, disruptive).</li>
              <li><strong className="text-gray-200">Observability Tools:</strong> Tell you what already broke after the outage occurred.</li>
              <li><strong className="text-gray-200">Architecture Reviews:</strong> Purely qualitative opinions without quantitative loss models.</li>
            </ul>
          </div>
          <p className="text-xs text-[#9CA3AF]">
            <strong className="text-white">CascadeIQ Solution:</strong> Chaos engineering without the chaos. Simulate outages mathematically before they happen, predict the exact monetary blast radius, and optimize mitigations under budget.
          </p>
        </div>
      ),
    },
    {
      title: "2. The Mathematical Propagation Model",
      subtitle: "Pure event-driven simulation with time delays",
      icon: Layers,
      content: (
        <div className="space-y-4 text-sm text-[#E5E7EB] leading-relaxed">
          <p>
            CascadeIQ enforces a fundamental domain rule: <span className="font-semibold text-[#818CF8]">Dependency edges point from Dependent to Provider</span> (source depends on target), but <span className="font-semibold text-rose-400">Failure cascades in reverse</span> (provider to dependent).
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1F2937]">
              <div className="font-mono text-emerald-400 font-semibold mb-1">Step 1: Transmission Factor (τ)</div>
              <p className="font-mono text-[11px] text-gray-300">
                τ_e = w_e × κ(kind) × (1 - m_e)
              </p>
              <p className="text-[#9CA3AF] mt-1 text-[11px]">
                Coupling strength w attenuated by edge call type κ (sync=1.0, data=0.8, config=0.9, async=0.35) and multi-mitigation diminishing returns.
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1F2937]">
              <div className="font-mono text-indigo-400 font-semibold mb-1">Step 2: Group & Noisy-OR Loss</div>
              <p className="font-mono text-[11px] text-gray-300">
                L_v = 1 - ∏_g (1 - G_g)
              </p>
              <p className="text-[#9CA3AF] mt-1 text-[11px]">
                Alternative redundant providers in a group protect the node unless all alternatives fail. Loss is aggregated across independent providers.
              </p>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-[#0B0F17] border border-[#1F2937] text-xs">
            <span className="font-semibold text-amber-300">Time-Aware Min-Heap:</span> Failures take real seconds to propagate (<code className="text-gray-200">t + delay_e</code>), accurately modeling network timeouts, queue drain times, and health check intervals.
          </div>
        </div>
      ),
    },
    {
      title: "3. Translating Architecture into Dollars",
      subtitle: "Annualized Expected Loss (AEL) & Risk Ranking",
      icon: DollarSign,
      content: (
        <div className="space-y-4 text-sm text-[#E5E7EB] leading-relaxed">
          <p>
            Engineers care about service health; CTOs care about money and customer SLA breaches.
            CascadeIQ attaches revenue ($/min) and active traffic only to user-facing business capability nodes to prevent double counting.
          </p>
          <div className="p-4 rounded-xl bg-[#0B0F17] border border-[#1F2937] space-y-2">
            <div className="font-mono text-xs text-emerald-400">AEL Equation:</div>
            <div className="p-2 rounded bg-black/40 font-mono text-xs text-white">
              AEL(v) = (8760 / MTBF) × (MTTR / 60) × (Hourly Loss)
            </div>
            <p className="text-xs text-[#9CA3AF]">
              Runs a single-failure sweep across every node in the graph, multiplying annual incident frequency by outage duration and total cascading downstream financial loss.
            </p>
          </div>
          <p className="text-xs text-[#9CA3AF]">
            In the bundled 34-node e-commerce platform, <strong className="text-rose-400">auth-db</strong> has zero revenue attached to it directly, but CascadeIQ ranks it as the top single point of failure because checkout, catalog, and mobile traffic all depend on it transitively!
          </p>
        </div>
      ),
    },
    {
      title: "4. Automated Intervention Optimization",
      subtitle: "Submodular lazy greedy search with best-single guard",
      icon: TrendingDown,
      content: (
        <div className="space-y-4 text-sm text-[#E5E7EB] leading-relaxed">
          <p>
            Given a limited reliability budget (effort points or dollars), what is the optimal combination of circuit breakers, fallback caches, read replicas, and bulkheads to deploy?
          </p>
          <div className="space-y-2 text-xs">
            <div className="flex items-start gap-2 p-2 rounded bg-[#0B0F17] border border-[#1F2937]">
              <span className="font-bold text-[#818CF8]">CELF Lazy Greedy:</span>
              <span className="text-[#9CA3AF]">Uses marginal gain per cost heap to evaluate candidate interventions 10x faster than brute force.</span>
            </div>
            <div className="flex items-start gap-2 p-2 rounded bg-[#0B0F17] border border-[#1F2937]">
              <span className="font-bold text-emerald-400">Knee Point Detection:</span>
              <span className="text-[#9CA3AF]">Identifies the point on the cost-benefit curve where extra engineering spend reaches diminishing returns.</span>
            </div>
            <div className="flex items-start gap-2 p-2 rounded bg-[#0B0F17] border border-[#1F2937]">
              <span className="font-bold text-cyan-400">Side-by-Side Compare:</span>
              <span className="text-[#9CA3AF]">Re-runs the exact same failure on the mitigated graph using identical random seeds to prove the delta mathematically.</span>
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-2xl bg-[#121826] border border-[#1F2937] shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1F2937] bg-[#0B0F17]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-[#818CF8]">
              <Sparkles className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">How CascadeIQ Works</h3>
              <p className="text-xs text-[#9CA3AF]">Architecture risk modeling and failure mitigation guide</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Indicator Tabs */}
        <div className="flex border-b border-[#1F2937] bg-[#0B0F17]/50 px-6 py-2 overflow-x-auto gap-2">
          {steps.map((st, idx) => (
            <button
              key={idx}
              onClick={() => setActiveStep(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                activeStep === idx
                  ? "bg-[#1F2937] text-white border border-gray-600 font-semibold shadow"
                  : "text-[#9CA3AF] hover:text-white hover:bg-white/5"
              }`}
            >
              Step {idx + 1}
            </button>
          ))}
        </div>

        {/* Step Body */}
        <div className="p-6 flex-1 min-h-[300px]">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-base font-bold text-white">{steps[activeStep].title}</h4>
          </div>
          <p className="text-xs text-[#818CF8] font-medium mb-4">{steps[activeStep].subtitle}</p>
          {steps[activeStep].content}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[#1F2937] bg-[#0B0F17]">
          <button
            onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
            disabled={activeStep === 0}
            className="px-4 py-2 rounded-lg text-xs font-medium text-[#9CA3AF] hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            Previous
          </button>

          <div className="flex items-center gap-3">
            {activeStep < steps.length - 1 ? (
              <button
                onClick={() => setActiveStep((prev) => Math.min(steps.length - 1, prev + 1))}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-[#1F2937] text-white hover:bg-[#2e3b52] transition-colors"
              >
                Next <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={() => {
                  onClose();
                  onRunDemo();
                }}
                className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/20 hover:brightness-110 active:scale-95 transition-all"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                Launch Winning Demo Now
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
