"use client";

import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import { COLORS } from "@/lib/colors";
import { Activity, ShieldAlert, Cpu } from "lucide-react";

export default function HomePage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize Cytoscape with a 3-node demonstration graph
    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        // Nodes
        {
          data: {
            id: "node-c",
            label: "auth-db (C)\nFAILED (1.0)",
            color: COLORS.stateFailed,
            shape: "barrel",
          },
        },
        {
          data: {
            id: "node-b",
            label: "auth-service (B)\nDEGRADED (0.6)",
            color: COLORS.stateDegraded,
            shape: "round-rectangle",
          },
        },
        {
          data: {
            id: "node-a",
            label: "api-gateway (A)\nHEALTHY (0.15)",
            color: COLORS.stateHealthy,
            shape: "rectangle",
          },
        },
        // Edges: source depends on target
        {
          data: {
            id: "edge-ab",
            source: "node-a",
            target: "node-b",
            label: "sync (0.8)",
          },
        },
        {
          data: {
            id: "edge-bc",
            source: "node-b",
            target: "node-c",
            label: "sync (1.0)",
          },
        },
      ],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-valign": "center",
            "text-halign": "center",
            "text-wrap": "wrap",
            "text-max-width": "120px",
            color: COLORS.textPrimary,
            "font-family": "monospace",
            "font-size": "11px",
            "background-color": "data(color)",
            width: "120px",
            height: "60px",
            shape: "data(shape)" as unknown as cytoscape.Css.NodeShape,
            "border-width": 2,
            "border-color": COLORS.border,
          },
        },
        {
          selector: "edge",
          style: {
            label: "data(label)",
            color: COLORS.textMuted,
            "font-family": "monospace",
            "font-size": "10px",
            width: 2,
            "line-color": COLORS.border,
            "target-arrow-color": COLORS.accent,
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "text-margin-y": -10,
          },
        },
      ],
      layout: {
        name: "grid",
        rows: 1,
        padding: 50,
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-[#0B0F17] text-[#E5E7EB]">
      {/* Top Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-[#1F2937] bg-[#121826]">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20 text-[#818CF8]">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-wide">CascadeIQ</h1>
            <p className="text-xs text-[#9CA3AF]">
              Enterprise Blast Radius & Failure Mitigation Platform
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Backend: Online
          </span>
          <span className="px-2 py-1 rounded bg-[#1F2937] text-gray-300">Phase 0 Skeleton</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col p-6 max-w-7xl w-full mx-auto gap-6">
        {/* KPI / Status Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-[#1F2937] bg-[#121826] flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-[#9CA3AF]">Graph Mode</p>
              <p className="text-xl font-bold mt-1">Cytoscape 3-Node</p>
            </div>
            <Cpu className="w-8 h-8 text-[#818CF8] opacity-80" />
          </div>

          <div className="p-4 rounded-xl border border-[#1F2937] bg-[#121826] flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-[#9CA3AF]">Direction Convention</p>
              <p className="text-sm font-semibold mt-1">
                Source <span className="text-[#818CF8]">&rarr;</span> Target (Dependent &rarr; Provider)
              </p>
            </div>
            <ShieldAlert className="w-8 h-8 text-[#FBBF24] opacity-80" />
          </div>

          <div className="p-4 rounded-xl border border-[#1F2937] bg-[#121826] flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-[#9CA3AF]">API Health</p>
              <p className="text-xl font-bold mt-1 text-emerald-400">GET /health: OK</p>
            </div>
            <div className="w-3 h-3 rounded-full bg-emerald-400" />
          </div>
        </div>

        {/* Graph Canvas Container */}
        <div className="flex-1 min-h-[500px] border border-[#1F2937] rounded-xl bg-[#0B0F17] relative overflow-hidden flex flex-col shadow-inner">
          <div className="px-4 py-2 border-b border-[#1F2937] bg-[#121826]/70 flex items-center justify-between">
            <span className="text-xs font-mono text-[#9CA3AF]">
              Canvas Preview (Pan / Zoom enabled)
            </span>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-[#34D399]" /> Healthy
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-[#FBBF24]" /> Degraded
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-[#F87171]" /> Failed
              </span>
            </div>
          </div>
          <div ref={containerRef} className="w-full flex-1" />
        </div>
      </main>
    </div>
  );
}
