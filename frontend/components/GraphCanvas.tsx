"use client";

import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import { COLORS } from "@/lib/colors";
import { GraphModel, SimulatedNode } from "@/lib/types";

interface GraphCanvasProps {
  graph: GraphModel | null;
  simulatedNodes?: Record<string, SimulatedNode>;
  activePath?: Array<{ source: string; target: string }>;
  selectedNodeId?: string | null;
  onSelectNode?: (nodeId: string) => void;
  layoutType?: "dagre" | "breadthfirst" | "concentric";
}

export function GraphCanvas({
  graph,
  simulatedNodes = {},
  activePath = [],
  selectedNodeId = null,
  onSelectNode,
  layoutType = "breadthfirst",
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !graph) return;

    // Convert domain nodes to Cytoscape elements
    const elements: cytoscape.ElementDefinition[] = [];

    // Nodes
    for (const node of graph.nodes) {
      const sim = simulatedNodes[node.id];
      const damage = sim ? sim.damage : 0.0;
      let stateColor: string = COLORS.stateHealthy;
      if (damage >= node.fail_threshold) {
        stateColor = COLORS.stateFailed;
      } else if (damage >= node.degrade_threshold) {
        stateColor = COLORS.stateDegraded;
      }

      let shape: cytoscape.Css.NodeShape = "round-rectangle";
      if (node.type === "database") shape = "barrel";
      else if (node.type === "cache") shape = "diamond";
      else if (node.type === "queue") shape = "hexagon";
      else if (node.type === "gateway") shape = "rectangle";
      else if (node.type === "external") shape = "rectangle";

      const isSelected = selectedNodeId === node.id;

      elements.push({
        data: {
          id: node.id,
          label: `${node.name}\n[${node.id}]${damage > 0 ? `\nDamage: ${(damage * 100).toFixed(0)}%` : ""}`,
          type: node.type,
          tier: node.tier,
          color: stateColor,
          shape: shape,
          isSelected: isSelected,
          damage: damage,
        },
      });
    }

    // Edges (source depends on target)
    for (const edge of graph.edges) {
      const edgeId = `${edge.source}->${edge.target}`;
      const isActive = activePath.some(
        (p) => p.source === edge.source && p.target === edge.target
      );

      elements.push({
        data: {
          id: edgeId,
          source: edge.source,
          target: edge.target,
          kind: edge.kind,
          strength: edge.strength,
          isActive: isActive,
          hasMitigation: edge.mitigations && edge.mitigations.length > 0,
        },
      });
    }

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-valign": "center",
            "text-halign": "center",
            "text-wrap": "wrap",
            "text-max-width": "110px",
            color: COLORS.textPrimary,
            "font-family": "monospace",
            "font-size": "9px",
            "background-color": "data(color)",
            width: "120px",
            height: "55px",
            shape: "data(shape)" as any,
            "border-width": 2,
            "border-color": "#1F2937",
            "transition-property": "background-color, border-color, border-width",
            "transition-duration": 0.3,
          },
        },
        {
          selector: "node[damage >= 0.6]",
          style: {
            "border-color": "#EF4444",
            "border-width": 3,
            "shadow-blur": 15,
            "shadow-color": "rgba(248,113,113,0.5)",
            "shadow-opacity": 0.8,
          },
        },
        {
          selector: "node[?isSelected]",
          style: {
            "border-color": "#818CF8",
            "border-width": 4,
            "shadow-blur": 20,
            "shadow-color": "#818CF8",
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#374151",
            "target-arrow-color": "#4B5563",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "arrow-scale": 0.8,
          },
        },
        {
          selector: "edge[kind = 'async']",
          style: {
            "line-style": "dashed",
          },
        },
        {
          selector: "edge[kind = 'config']",
          style: {
            "line-style": "dotted",
          },
        },
        {
          selector: "edge[?isActive]",
          style: {
            width: 3.5,
            "line-color": "#F87171",
            "target-arrow-color": "#F87171",
            "line-style": "solid",
            "shadow-blur": 10,
            "shadow-color": "#F87171",
          },
        },
        {
          selector: "edge[?hasMitigation]",
          style: {
            "line-color": "#38BDF8",
            "target-arrow-color": "#38BDF8",
          },
        },
      ] as any,
      layout: {
        name: layoutType,
        padding: 40,
        animate: false,
      } as any,
      userZoomingEnabled: true,
      userPanningEnabled: true,
    });

    cy.on("tap", "node", (evt) => {
      const nodeId = evt.target.id();
      if (onSelectNode) {
        onSelectNode(nodeId);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graph, layoutType]);

  // Update node colors and edge states dynamically without re-laying out
  useEffect(() => {
    if (!cyRef.current || !graph) return;
    const cy = cyRef.current;

    cy.batch(() => {
      for (const node of graph.nodes) {
        const el = cy.getElementById(node.id);
        if (!el || el.empty()) continue;

        const sim = simulatedNodes[node.id];
        const damage = sim ? sim.damage : 0.0;
        let color: string = COLORS.stateHealthy;
        if (damage >= node.fail_threshold) color = COLORS.stateFailed;
        else if (damage >= node.degrade_threshold) color = COLORS.stateDegraded;

        el.data("color", color);
        el.data("damage", damage);
        el.data("isSelected", selectedNodeId === node.id);
        el.data(
          "label",
          `${node.name}\n[${node.id}]${damage > 0 ? `\nDamage: ${(damage * 100).toFixed(0)}%` : ""}`
        );
      }

      for (const edge of graph.edges) {
        const edgeId = `${edge.source}->${edge.target}`;
        const el = cy.getElementById(edgeId);
        if (!el || el.empty()) continue;

        const isActive = activePath.some(
          (p) => p.source === edge.source && p.target === edge.target
        );
        el.data("isActive", isActive);
      }
    });
  }, [simulatedNodes, activePath, selectedNodeId, graph]);

  return (
    <div className="relative w-full h-full flex flex-col bg-[#0B0F17] overflow-hidden select-none">
      <div ref={containerRef} className="w-full flex-1" />

      {/* Canvas Controls Overlay */}
      <div className="absolute bottom-4 left-4 z-10 flex items-center gap-2 p-1.5 rounded-xl bg-[#121826]/90 border border-[#1F2937] backdrop-blur-md shadow-lg text-xs">
        <button
          onClick={() => cyRef.current?.fit(undefined, 30)}
          className="px-2.5 py-1 rounded bg-[#1F2937] hover:bg-gray-700 text-gray-200 transition-colors"
        >
          Fit Canvas
        </button>
        <button
          onClick={() => cyRef.current?.zoom((cyRef.current.zoom() || 1) * 1.25)}
          className="px-2 py-1 rounded bg-[#1F2937] hover:bg-gray-700 text-gray-200"
        >
          +
        </button>
        <button
          onClick={() => cyRef.current?.zoom((cyRef.current.zoom() || 1) * 0.8)}
          className="px-2 py-1 rounded bg-[#1F2937] hover:bg-gray-700 text-gray-200"
        >
          -
        </button>
      </div>

      {/* State Legend */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-3 px-3 py-1.5 rounded-xl bg-[#121826]/90 border border-[#1F2937] backdrop-blur-md text-[11px] text-gray-300">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#34D399]" /> Healthy
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#FBBF24]" /> Degraded
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#F87171] animate-pulse" /> Failed
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#38BDF8]" /> Mitigation
        </span>
      </div>
    </div>
  );
}
