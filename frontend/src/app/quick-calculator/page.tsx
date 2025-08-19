"use client";
import React, { useState, useRef, useEffect } from "react";

function formatCurrency(val: string | number) {
  if (val === null || val === undefined || val === "") return "";
  const num = typeof val === "string" ? parseFloat(val.replace(/,/g, "")) : val;
  if (isNaN(num)) return "";
  return num.toLocaleString();
}

function parseCurrency(val: string) {
  return parseFloat(val.replace(/,/g, "")) || 0;
}

interface QuickCalculatorForm {
  // Essential demographics
  age: string;
  marital_status: string;
  dependents: string;
  // Key financial info
  monthly_income: string;
  mortgage_balance: string; // Now represents total debts
  other_debts: string; // Now represents total assets
  // Education (if applicable)
  provide_education: boolean;
  // Existing coverage
  individual_life: string;
  group_life: string;
  // Preferences
  cash_value_importance: string;
  permanent_coverage: string;
  income_replacement_years: string;
}

const initialForm: QuickCalculatorForm = {
  age: "",
  marital_status: "",
  dependents: "",
  monthly_income: "",
  mortgage_balance: "",
  other_debts: "",
  provide_education: false,
  individual_life: "",
  group_life: "",
  cash_value_importance: "unsure",
  permanent_coverage: "unsure",
  income_replacement_years: "10",
};

export default function QuickCalculatorPage() {
  const [form, setForm] = useState<QuickCalculatorForm>(initialForm);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [editableSavings, setEditableSavings] = useState<number | null>(null);
  const [cashValueProjection, setCashValueProjection] = useState<any[]>([]);

  // Currency input handler with formatting
  const handleCurrencyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const cleaned = value.replace(/[^\d,]/g, "");
    const formatted = formatCurrency(cleaned);
    setForm((prev) => ({ ...prev, [name]: formatted }));
  };

  // Generic input handler
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    let checked = false;
    if (type === "checkbox" && e.target instanceof HTMLInputElement) {
      checked = e.target.checked;
    }
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  // Validation
  const validateForm = () => {
    return (
      form.age !== "" &&
      form.marital_status !== "" &&
      form.dependents !== "" &&
      form.monthly_income !== ""
    );
  };

  // Calculate needs
  const handleCalculate = async () => {
    if (!validateForm()) {
      setError("Please fill in all required fields.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        age: parseInt(form.age),
        marital_status: form.marital_status,
        dependents: parseInt(form.dependents),
        monthly_income: parseCurrency(form.monthly_income),
        mortgage_balance: parseCurrency(form.mortgage_balance), // Now represents total debts
        other_debts: parseCurrency(form.other_debts), // Now represents total assets
        provide_education: form.provide_education,
        num_children: form.provide_education ? parseInt(form.dependents) : 0, // Use dependents count
        education_type: "public_4_in", // Assume public education
        education_cost_per_child: form.provide_education ? 23250 : 0, // Public 4-year in-state cost
        individual_life: parseCurrency(form.individual_life),
        group_life: parseCurrency(form.group_life),
        cash_value_importance: form.cash_value_importance,
        permanent_coverage: form.permanent_coverage,
        income_replacement_years: parseInt(form.income_replacement_years),
        // Set defaults for missing fields
        health_status: "good",
        tobacco_use: "no",
        coverage_goals: ["living_expenses", "mortgage"],
        other_coverage_goal: "",
        monthly_expenses: "",
        adjust_inflation: false,
        additional_obligations: 0,
        funeral_expenses: 8000,
        legacy_amount: 0,
        special_needs: "",
        savings: 0,
        investments: 0,
        other_assets: 0,
        advisor_notes: "",
      };

      const response = await fetch("/api/calculate-needs-detailed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Failed to calculate needs");
      }

      const data = await response.json();
      setResult(data);
      setEditableSavings(data.recommended_monthly_savings || 400);
      setCashValueProjection(data.cash_value_projection || []);
    } catch (err) {
      setError("Failed to calculate needs. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Recalculate projection when savings amount changes
  const recalcProjection = (monthly: number) => {
    if (!result || !result.projection_parameters) return;

    const params = result.projection_parameters;
    const duration = result.duration_years || 20;
    const projection = [];
    let cashValue = 0;

    for (let year = 1; year <= duration; year++) {
      if (year === 1) {
        cashValue += monthly * 12 * params.year1_allocation;
      } else {
        cashValue = cashValue * (1 + params.illustrated_rate) + monthly * 12 * params.year2plus_allocation;
      }
      projection.push({ year, value: Math.round(cashValue / 100) * 100 });
    }

    setCashValueProjection(projection);
  };

  // Coverage breakdown chart (matching assessment style)
  function CoverageBreakdownChart({ breakdown }: { breakdown: any }) {
    const total = Object.values(breakdown).reduce((sum: number, v) => sum + (typeof v === "number" ? v : 0), 0);
    // Only include non-zero categories
    const entries = Object.entries(breakdown).filter(([_, v]) => (typeof v === "number" ? v : Number(v)) > 0);
    // Pie chart dimensions
    const size = 220;
    const radius = size / 2 - 20;
    let startAngle = 0;
    const colors = {
      living_expenses: "#1B365D",
      debts: "#3B82F6",
      education: "#F59E42",
      funeral: "#6366F1",
      legacy: "#10B981",
      other: "#F43F5E",
    };
    return (
      <div>
        {entries.length > 0 && (
          <div className="flex justify-start mb-4">
            <svg width={size} height={size}>
              {entries.map(([k, v], i) => {
                const value = typeof v === "number" ? v : Number(v);
                const percent = total ? value / total : 0;
                const endAngle = startAngle + percent * 2 * Math.PI;
                const x1 = size / 2 + radius * Math.cos(startAngle);
                const y1 = size / 2 + radius * Math.sin(startAngle);
                const x2 = size / 2 + radius * Math.cos(endAngle);
                const y2 = size / 2 + radius * Math.sin(endAngle);
                const largeArc = percent > 0.5 ? 1 : 0;
                const path = `M${size / 2},${size / 2} L${x1},${y1} A${radius},${radius} 0 ${largeArc} 1 ${x2},${y2} Z`;
                startAngle = endAngle;
                return (
                  <g key={k}>
                    <path d={path} fill={colors[k as keyof typeof colors] || "#ccc"} opacity={0.85} />
                  </g>
                );
              })}
            </svg>
          </div>
        )}
        <div className="flex gap-2">
          {Object.entries(breakdown).map(([k, v]) => {
            const value = typeof v === 'number' ? v : Number(v);
            const percent = total && typeof value === 'number' ? ((value / total) * 100).toFixed(0) : '0';
            return (
              <div key={k} className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full" style={{ background: colors[k as keyof typeof colors] || '#ccc', opacity: 0.8 }}></div>
                <div className="text-xs mt-1">{k.replace('_', ' ')}</div>
                <div className="text-xs font-bold">{percent}%</div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Cash value chart (matching assessment style)
  function CashValueChart({ data }: { data: any[] }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    // Only show key years for clarity
    const keyYears = [5, 10, 20, 30, 40];
    // Filter data to only include key years (or closest available)
    const filteredData = keyYears
      .map(y => data.find(d => d.year === y))
      .filter(Boolean);
    useEffect(() => {
      if (!filteredData || !filteredData.length) return;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      // Chart dimensions
      const width = canvas.width;
      const height = canvas.height;
      const padding = 40;
      const maxVal = Math.max(...filteredData.map(d => d.value));
      const minVal = Math.min(...filteredData.map(d => d.value));
      const n = filteredData.length;
      // Draw axes
      ctx.strokeStyle = "#888";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding, padding);
      ctx.lineTo(padding, height - padding);
      ctx.lineTo(width - padding, height - padding);
      ctx.stroke();
      // Draw line
      ctx.strokeStyle = "#10B981";
      ctx.lineWidth = 3;
      ctx.beginPath();
      filteredData.forEach((d, i) => {
        const x = padding + ((width - 2 * padding) * i) / (n - 1);
        const y = height - padding - ((d.value - minVal) / (maxVal - minVal || 1)) * (height - 2 * padding);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      // Draw points and value labels
      ctx.fillStyle = "#10B981";
      ctx.font = "bold 14px sans-serif";
      filteredData.forEach((d, i) => {
        const x = padding + ((width - 2 * padding) * i) / (n - 1);
        const y = height - padding - ((d.value - minVal) / (maxVal - minVal || 1)) * (height - 2 * padding);
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = "#222";
        ctx.fillText(`$${d.value.toLocaleString()}`, x - 30, y - 12);
        ctx.fillStyle = "#10B981";
      });
      // Draw year labels
      ctx.fillStyle = "#222";
      ctx.font = "14px sans-serif";
      filteredData.forEach((d, i) => {
        const x = padding + ((width - 2 * padding) * i) / (n - 1);
        ctx.fillText(`Yr ${d.year}`, x - 18, height - padding + 22);
      });
    }, [filteredData]);
    return (
      <div className="my-8">
        <div className="font-semibold mb-2">Projected Cash Value (IUL Track)</div>
        <div className="w-full flex justify-center">
          <canvas ref={canvasRef} width={700} height={320} style={{ background: "#f3f4f6", borderRadius: 12, maxWidth: "100%" }} />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col items-center min-h-[70vh] text-black">
      {/* Header */}
      <div className="w-full px-12 pt-8 text-center">
        <h1 className="text-3xl font-bold text-[#1B365D] mb-2">Quick Insurance Calculator</h1>
        <p className="text-gray-600">Get a fast estimate of your life insurance needs in just a few minutes</p>
      </div>

      {!result ? (
        /* Calculator Form */
        <div className="w-full px-12 pb-12">
          <div className="bg-white text-black rounded-2xl shadow p-8 min-h-[320px] w-full max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-[#1B365D] mb-6">Quick Assessment</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Personal Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>
                
                <div>
                  <label className="block font-semibold mb-1">
                    Age <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="age"
                    value={form.age}
                    onChange={handleChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                    placeholder="Enter your age"
                  />
                </div>

                <div>
                  <label className="block font-semibold mb-1">
                    Marital Status <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="marital_status"
                    value={form.marital_status}
                    onChange={handleChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                  >
                    <option value="">Select status</option>
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                    <option value="divorced">Divorced</option>
                    <option value="widowed">Widowed</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold mb-1">
                    Number of Dependents <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="dependents"
                    value={form.dependents}
                    onChange={handleChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                    placeholder="0"
                  />
                </div>
              </div>

              {/* Financial Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Financial Information</h3>
                
                <div>
                  <label className="block font-semibold mb-1">
                    Monthly Income <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="monthly_income"
                    value={form.monthly_income}
                    onChange={handleCurrencyChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                    placeholder="e.g. 8,000"
                  />
                </div>

                <div>
                  <label className="block font-semibold mb-1">
                    Total Debts
                  </label>
                  <input
                    type="text"
                    name="mortgage_balance"
                    value={form.mortgage_balance}
                    onChange={handleCurrencyChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                    placeholder="e.g. 300,000"
                  />
                </div>

                <div>
                  <label className="block font-semibold mb-1">
                    Estimated Total Assets
                  </label>
                  <input
                    type="text"
                    name="other_debts"
                    value={form.other_debts}
                    onChange={handleCurrencyChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                    placeholder="e.g. 150,000"
                  />
                </div>
              </div>
            </div>

            {/* Education Section */}
            <div className="mt-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Education Funding</h3>
              
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  name="provide_education"
                  checked={form.provide_education}
                  onChange={handleChange}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label className="text-sm font-medium text-gray-700">
                  I want to provide for my children's education (assumes public 4-year in-state costs)
                </label>
              </div>
            </div>

            {/* Existing Coverage */}
            <div className="mt-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Existing Life Insurance</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold mb-1">
                    Individual Life Insurance
                  </label>
                  <input
                    type="text"
                    name="individual_life"
                    value={form.individual_life}
                    onChange={handleCurrencyChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                    placeholder="e.g. 100,000"
                  />
                </div>
                <div>
                  <label className="block font-semibold mb-1">
                    Group Life Insurance
                  </label>
                  <input
                    type="text"
                    name="group_life"
                    value={form.group_life}
                    onChange={handleCurrencyChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                    placeholder="e.g. 50,000"
                  />
                </div>
              </div>
            </div>

            {/* Preferences */}
            <div className="mt-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Preferences</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block font-semibold mb-1">
                    Is accumulating savings in your life insurance policy important to you?
                  </label>
                  <select
                    name="cash_value_importance"
                    value={form.cash_value_importance}
                    onChange={handleChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                  >
                    <option value="unsure">Unsure</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold mb-1">
                    Do you want permanent lifelong coverage?
                  </label>
                  <select
                    name="permanent_coverage"
                    value={form.permanent_coverage}
                    onChange={handleChange}
                    className="w-full border rounded-lg px-3 py-2 text-black"
                  >
                    <option value="unsure">Unsure</option>
                    <option value="yes">Yes (permanent)</option>
                    <option value="no">No (temporary)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Calculate Button */}
            <div className="mt-8 text-center">
              <button
                onClick={handleCalculate}
                disabled={loading || !validateForm()}
                className="bg-[#1B365D] text-white rounded-lg px-8 py-3 font-semibold shadow hover:bg-blue-900 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Calculating..." : "Calculate My Needs"}
              </button>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600">{error}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Results Display */
        <div className="w-full px-12 pb-12">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg p-6 shadow-sm border text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Recommended Coverage</h3>
                <p className="text-3xl font-bold text-blue-600">${result.recommended_coverage.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-sm border text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Coverage Gap</h3>
                <p className="text-3xl font-bold text-black">${result.gap.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-sm border text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Duration</h3>
                <p className="text-3xl font-bold text-black">
                  {result.product_recommendation?.includes("IUL") 
                    ? "permanent" 
                    : `${result.duration_years} years`}
                </p>
              </div>
            </div>

            {/* Product Recommendation */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Product Recommendation</h3>
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="text-2xl font-bold text-blue-900 mb-3">{result.product_recommendation}</h4>
                {result.product_recommendation?.includes("IUL") ? (
                  <p className="text-blue-800 mb-2">JPM TermVest+ offers two tracks: Term and IUL. The IUL Track provides immediate access to cash value accumulation with tax-deferred growth potential, flexible premiums, and permanent coverage. Your cash value can grow based on market performance while providing a guaranteed death benefit for life.</p>
                ) : (
                  <p className="text-blue-800 mb-2">JPM TermVest+ offers two tracks: Term and IUL. The Term Track provides essential protection at an affordable premium for a specified period. You can convert to the IUL Track later to begin building cash value savings with permanent coverage when your financial situation allows.</p>
                )}
                <p className="text-blue-800"><b>Why?</b> {result.rationale}</p>
              </div>
            </div>

            {/* Coverage Breakdown */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Coverage Breakdown</h3>
              <ul className="list-disc ml-6 mb-4">
                <li>Living Expenses: ${result.needs_breakdown.living_expenses.toLocaleString()}</li>
                <li>Debts: ${result.needs_breakdown.debts.toLocaleString()}</li>
                <li>Education: ${result.needs_breakdown.education.toLocaleString()}</li>
                <li>Funeral: ${result.needs_breakdown.funeral.toLocaleString()}</li>
                <li>Legacy: ${result.needs_breakdown.legacy.toLocaleString()}</li>
                <li>Other: ${result.needs_breakdown.other.toLocaleString()}</li>
              </ul>
              <CoverageBreakdownChart breakdown={result.needs_breakdown} />
            </div>

            {/* Cash Value Projection (if IUL) */}
            {result.product_recommendation?.includes("IUL") && (
              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Cash Value Savings</h3>
                <p className="text-gray-600 mb-4">
                  Based on your input data, this is our calculated field for suggested monthly cash value savings. 
                  You can change this value during times of financial change (saving more or less).
                </p>
                <div className="flex items-center gap-4 mb-4">
                  <label className="text-sm font-medium text-gray-700">Monthly Amount:</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      value={editableSavings || result.recommended_monthly_savings || 400}
                      onChange={(e) => {
                        let value = parseInt(e.target.value) || 400;
                        const maxLimit = result.max_monthly_contribution || 2000;
                        
                        // Auto-correct if value exceeds max limit
                        if (value > maxLimit) {
                          value = maxLimit;
                        }
                        
                        setEditableSavings(value);
                        recalcProjection(value);
                      }}
                      className="pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      min="100"
                      max={result.max_monthly_contribution || 2000}
                      placeholder="400"
                    />
                  </div>
                </div>
                
                {/* Savings Level Indicator */}
                {result.max_monthly_contribution && (
                  <div className="mb-4">
                    <div className="text-sm text-gray-600 mb-2">
                      Maximum allowed: ${result.max_monthly_contribution.toLocaleString()}/month (MEC limit)
                    </div>
                    {(() => {
                      const currentAmount = editableSavings || result.recommended_monthly_savings || 400;
                      const percentage = (currentAmount / result.max_monthly_contribution) * 100;
                      
                      let level = "";
                      let color = "";
                      
                      if (percentage <= 25) {
                        level = "Low Savings";
                        color = "text-orange-600";
                      } else if (percentage <= 50) {
                        level = "Medium Savings";
                        color = "text-blue-600";
                      } else if (percentage <= 75) {
                        level = "High Savings";
                        color = "text-green-600";
                      } else {
                        level = "Maximum Savings";
                        color = "text-purple-600";
                      }
                      
                      return (
                        <div className={`text-sm font-semibold ${color}`}>
                          {level} ({percentage.toFixed(0)}% of maximum)
                        </div>
                      );
                    })()}
                  </div>
                )}
                <CashValueChart data={cashValueProjection} />
                <div className="text-xs italic text-gray-500 mt-2">
                  Projection assumes illustrated rate of 5.5%, allocations of 20% in year 1 and 60% in subsequent years. Actual results may vary and are not guaranteed.
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700">
                Ask Robo-Advisor
              </button>
              <button className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700">
                Start Application
              </button>
            </div>

            {/* Back Button */}
            <div className="text-center">
              <button
                onClick={() => {
                  setResult(null);
                  setForm(initialForm);
                  setError(null);
                }}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                ← Start Over
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 