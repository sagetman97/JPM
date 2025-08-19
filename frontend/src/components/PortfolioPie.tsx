"use client";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

export default function PortfolioPie({ insurance, total = 2000000 }: { insurance: number; total?: number }) {
  // Mock portfolio: 60% stocks, 30% bonds, 10% cash, add insurance as a new slice
  const base = [
    { label: "Stocks", value: total * 0.6, color: "#4A90A4" },
    { label: "Bonds", value: total * 0.3, color: "#1B365D" },
    { label: "Cash", value: total * 0.1, color: "#DEE2E6" },
  ];
  const insuranceValue = Math.max(insurance, 0);
  const data = {
    labels: [...base.map((b) => b.label), "Life Insurance"],
    datasets: [
      {
        data: [...base.map((b) => b.value), insuranceValue],
        backgroundColor: [...base.map((b) => b.color), "#00A651"],
        borderWidth: 1,
      },
    ],
  };
  const options = {
    plugins: {
      legend: { position: "bottom" as const },
      tooltip: { callbacks: { label: (ctx: any) => `${ctx.label}: $${ctx.parsed.toLocaleString()}` } },
    },
  };
  return (
    <div className="w-full flex flex-col items-center">
      <Pie data={data} options={options} />
      <div className="text-xs text-gray-500 mt-2">Sample portfolio allocation including recommended insurance</div>
    </div>
  );
} 