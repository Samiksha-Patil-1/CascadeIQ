"use client";

import React from "react";
import { AlertCircle, DollarSign, Users, ShieldAlert, Clock, TrendingDown } from "lucide-react";
import { ImpactSummary } from "@/lib/types";

interface KpiCardsProps {
  summary: ImpactSummary | null;
  delta?: {
    affected?: number;
    failed?: number;
    users_impacted?: number;
    money_per_hour?: number;
    outage_cost?: number;
    slo_breaches?: number;
    pct_loss_reduction?: number;
  };
  isCompareMode?: boolean;
}

export function KpiCards({ summary, delta, isCompareMode = false }: KpiCardsProps) {
  if (!summary) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-[#121826] border border-[#1F2937] animate-pulse h-20" />
        ))}
      </div>
    );
  }

  const items = [
    {
      label: "Affected Nodes",
      value: summary.affected,
      sub: `of system total`,
      icon: AlertCircle,
      delta: delta?.affected,
      invertDelta: true,
      unit: "",
    },
    {
      label: "Hard Failures",
      value: summary.failed,
      sub: "damage >= 0.6",
      icon: ShieldAlert,
      delta: delta?.failed,
      invertDelta: true,
      unit: "",
    },
    {
      label: "Revenue Loss / Hr",
      value: `$${(summary.money_per_hour).toLocaleString()}`,
      sub: "steady-state flow",
      icon: DollarSign,
      delta: delta?.money_per_hour ? `-$${Math.abs(delta.money_per_hour).toLocaleString()}` : undefined,
      invertDelta: true,
    },
    {
      label: "Total Outage Cost",
      value: `$${summary.outage_cost.toLocaleString()}`,
      sub: "integrated over time",
      icon: TrendingDown,
      delta: delta?.pct_loss_reduction ? `-${delta.pct_loss_reduction}%` : undefined,
      invertDelta: true,
      highlight: true,
    },
    {
      label: "Users Impacted",
      value: summary.users_impacted.toLocaleString(),
      sub: "per minute",
      icon: Users,
      delta: delta?.users_impacted,
      invertDelta: true,
      unit: "/min",
    },
    {
      label: "SLO Breaches",
      value: summary.slo_breaches,
      sub: "health < slo_floor",
      icon: Clock,
      delta: delta?.slo_breaches,
      invertDelta: true,
      unit: "services",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 select-none">
      {items.map((item, idx) => {
        const Icon = item.icon;
        return (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border transition-all duration-300 relative overflow-hidden flex flex-col justify-between ${
              item.highlight
                ? "bg-gradient-to-br from-[#121826] to-indigo-950/40 border-indigo-500/40 shadow-[0_0_15px_rgba(99,102,241,0.15)]"
                : "bg-[#121826] border-[#1F2937] hover:border-gray-700"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium text-[#9CA3AF] tracking-wide">
                {item.label}
              </span>
              <Icon className="w-4 h-4 text-[#818CF8] opacity-80" />
            </div>

            <div className="my-1">
              <span className="text-xl md:text-2xl font-bold font-mono tracking-tight text-white">
                {item.value}
              </span>
              {item.unit && <span className="text-xs font-mono text-[#9CA3AF] ml-1">{item.unit}</span>}
            </div>

            <div className="flex items-center justify-between text-[10px]">
              <span className="text-[#9CA3AF] truncate">{item.sub}</span>
              {isCompareMode && item.delta !== undefined && (
                <span className="font-mono font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                  {item.delta}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
