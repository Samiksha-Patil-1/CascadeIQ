"use client";

import React, { useState } from "react";
import { DollarSign, Play, ArrowUpDown } from "lucide-react";
import { RiskRankingItem } from "@/lib/types";

interface RiskBoardProps {
  rankings: RiskRankingItem[];
  onSelectNodeForSimulation: (nodeId: string) => void;
  isLoading: boolean;
}

export function RiskBoard({
  rankings,
  onSelectNodeForSimulation,
  isLoading,
}: RiskBoardProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<"ael" | "criticality" | "affected_count">("ael");
  const [sortAsc, setSortAsc] = useState(false);

  const filtered = rankings
    .filter(
      (r) =>
        r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.node_id.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      const mult = sortAsc ? 1 : -1;
      return (a[sortField] - b[sortField]) * mult;
    });

  const handleSort = (field: "ael" | "criticality" | "affected_count") => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full select-none">
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            Enterprise Risk Ranking & Prioritization
          </h2>
          <p className="text-xs text-[#9CA3AF]">
            Evaluated via single-failure sweep (severity 1.0) sorted by Annualized Expected Loss (AEL).
          </p>
        </div>

        <input
          type="text"
          placeholder="Filter services..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-[#121826] border border-[#1F2937] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 w-64"
        />
      </div>

      {/* Heatmap / Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {rankings.slice(0, 3).map((item, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl bg-gradient-to-br from-[#121826] to-rose-950/20 border border-rose-500/30 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold">
                RANK #{item.rank}
              </span>
              <span className="text-xs font-mono text-gray-400">Tier {item.tier}</span>
            </div>

            <div className="my-2">
              <h4 className="text-base font-bold text-white">{item.name}</h4>
              <p className="font-mono text-xs text-[#9CA3AF]">{item.node_id}</p>
            </div>

            <div className="pt-2 border-t border-gray-800/60 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-gray-400">Annualized Loss</span>
                <p className="text-base font-bold font-mono text-emerald-400">
                  ${item.ael.toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => onSelectNodeForSimulation(item.node_id)}
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 text-xs font-semibold transition-colors"
              >
                <Play className="w-3 h-3 fill-current" />
                Simulate
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-[#1F2937] bg-[#121826] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0F17] text-[#9CA3AF] border-b border-[#1F2937] font-mono">
              <tr>
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">Service</th>
                <th
                  onClick={() => handleSort("ael")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    Annual Loss (AEL) <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-4">Hourly Impact</th>
                <th className="py-3 px-4">Incident Freq</th>
                <th className="py-3 px-4">MTTR</th>
                <th
                  onClick={() => handleSort("affected_count")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    Blast Radius <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort("criticality")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    Criticality Index <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2937]/50">
              {filtered.map((r) => (
                <tr
                  key={r.node_id}
                  className="hover:bg-white/5 transition-colors group"
                >
                  <td className="py-3 px-4 font-mono font-bold text-gray-400">
                    #{r.rank}
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{r.name}</div>
                    <div className="font-mono text-[10px] text-gray-400">{r.node_id}</div>
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                    ${r.ael.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 font-mono text-gray-300">
                    ${r.impact_per_hour.toLocaleString()}/hr
                  </td>
                  <td className="py-3 px-4 font-mono text-gray-300">
                    {r.incidents_per_year} /yr
                  </td>
                  <td className="py-3 px-4 font-mono text-gray-300">
                    {r.mttr_minutes}m
                  </td>
                  <td className="py-3 px-4 font-mono text-rose-400 font-bold">
                    {r.affected_count} nodes
                  </td>
                  <td className="py-3 px-4 font-mono text-[#818CF8]">
                    {r.criticality.toFixed(3)}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectNodeForSimulation(r.node_id)}
                      className="px-2.5 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 font-semibold transition-colors"
                    >
                      Simulate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
