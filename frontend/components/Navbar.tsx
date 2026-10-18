"use client";

import React from "react";
import { Activity, Sparkles, Play, Cpu, BarChart3, Sliders, GitCompare } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenExplainer: () => void;
  onQuickDemo: () => void;
  isSimulating: boolean;
}

export function Navbar({
  activeTab,
  setActiveTab,
  onOpenExplainer,
  onQuickDemo,
  isSimulating,
}: NavbarProps) {
  const tabs = [
    { id: "sim", label: "Simulation Lab", icon: Play },
    { id: "explorer", label: "Architecture Explorer", icon: Cpu },
    { id: "risk", label: "Risk Board", icon: BarChart3 },
    { id: "planner", label: "Mitigation Planner", icon: Sliders },
    { id: "compare", label: "Compare View", icon: GitCompare },
  ];

  return (
    <header className="flex flex-col md:flex-row items-center justify-between px-6 py-3 border-b border-[#1F2937] bg-[#121826] gap-3 select-none">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/25 text-[#818CF8] shadow-[0_0_15px_rgba(129,140,248,0.2)]">
          <Activity className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white">CascadeIQ</h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-[#818CF8] border border-indigo-500/30">
              v1.0 Pro
            </span>
          </div>
          <p className="text-xs text-[#9CA3AF]">
            Predict the Blast Radius of Failure & Optimize Mitigations
          </p>
        </div>
      </div>

      {/* Navigation tabs */}
      <nav className="flex items-center gap-1.5 p-1 rounded-xl bg-[#0B0F17] border border-[#1F2937]">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                isActive
                  ? "bg-[#1F2937] text-white shadow-sm font-semibold border border-gray-700"
                  : "text-[#9CA3AF] hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#818CF8]" : ""}`} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Action buttons */}
      <div className="flex items-center gap-3">
        {/* Quick Demo Trigger */}
        <button
          onClick={onQuickDemo}
          disabled={isSimulating}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25 transition-all shadow-sm active:scale-95 disabled:opacity-50"
          title="Inject Auth-DB at severity 1.0 and view cascade"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          Run Demo Cascade
        </button>

        {/* Explainer Button */}
        <button
          onClick={onOpenExplainer}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-[0_0_20px_rgba(99,102,241,0.35)] hover:shadow-[0_0_25px_rgba(99,102,241,0.5)] hover:brightness-110 active:scale-95 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-spin" style={{ animationDuration: "6s" }} />
          How This Project Works
        </button>
      </div>
    </header>
  );
}
