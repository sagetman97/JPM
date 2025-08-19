"use client";
import React, { useState } from "react";
import { useRef, useEffect } from "react";

const COVERAGE_GOALS = [
  { value: "living_expenses", label: "Family’s living expenses" },
  { value: "mortgage", label: "Mortgage or other debts" },
  { value: "education", label: "Children’s education" },
  { value: "funeral", label: "Funeral/final expenses" },
  { value: "special_needs", label: "Special needs or legacy" },
  { value: "other", label: "Other (please specify)" },
];

const EDUCATION_TYPES = [
  { value: "public_2", label: "Public, 2-year in-district ($13,470/year)" },
  { value: "public_4_in", label: "Public, 4-year in-state ($23,250/year)" },
  { value: "public_4_out", label: "Public, 4-year out-of-state ($40,550/year)" },
  { value: "private_4", label: "Private nonprofit, 4-year ($53,430/year)" },
  { value: "custom", label: "Custom estimate" },
];

function formatCurrency(val: string | number) {
  if (val === null || val === undefined || val === "") return "";
  const num = typeof val === "string" ? parseFloat(val.replace(/,/g, "")) : val;
  if (isNaN(num)) return "";
  return num.toLocaleString();
}

function parseCurrency(val: string) {
  return parseFloat(val.replace(/,/g, "")) || 0;
}

// Fix: Explicitly type the form state
interface AssessmentForm {
  // Demographics
  age: string;
  marital_status: string;
  dependents: string;
  health_status: string;
  tobacco_use: string; // 'yes' | 'no' | ''
  // Preferences
  cash_value_importance: string;
  permanent_coverage: string; // 'yes' | 'no' | 'unsure'
  support_years: string; // keep for backend compatibility, but not shown
  coverage_goals: string[];
  other_coverage_goal: string;
  monthly_income: string;
  monthly_expenses: string;
  adjust_inflation: boolean;
  mortgage_balance: string;
  other_debts: string;
  additional_obligations: string;
  provide_education: boolean;
  num_children: string;
  education_type: string;
  education_cost_per_child: string;
  funeral_expenses: string;
  legacy_amount: string;
  special_needs: string;
  savings: string;
  investments: string;
  individual_life: string;
  group_life: string;
  other_assets: string;
  advisor_notes: string;
  income_replacement_years: string; // new field for user input (0-20, default 10)
}

const initialForm: AssessmentForm = {
  age: "",
  marital_status: "",
  dependents: "",
  health_status: "",
  tobacco_use: "",
  cash_value_importance: "unsure",
  permanent_coverage: "unsure",
  support_years: "10",
  coverage_goals: [],
  other_coverage_goal: "",
  monthly_income: "",
  monthly_expenses: "",
  adjust_inflation: false,
  mortgage_balance: "",
  other_debts: "",
  additional_obligations: "",
  provide_education: false,
  num_children: "",
  education_type: "public_4_in",
  education_cost_per_child: "",
  funeral_expenses: "",
  legacy_amount: "",
  special_needs: "",
  savings: "",
  investments: "",
  individual_life: "",
  group_life: "",
  other_assets: "",
  advisor_notes: "",
  income_replacement_years: "10",
};

export default function AssessmentPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<AssessmentForm>(initialForm);
  const [touched, setTouched] = useState<{ [k: string]: boolean }>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [editableSavings, setEditableSavings] = useState<number | null>(null);
  const [projectionParams, setProjectionParams] = useState<any>(null);
  const [cashValueProjection, setCashValueProjection] = useState<any[]>([]);

  // Step definitions
  const steps = [
    "Personal Details",
    "Goals & Preferences",
    "Coverage Goals",
    "Income & Expenses",
    "Debts & Obligations",
    "Education Needs",
    "Final Expenses & Legacy",
    "Assets & Coverage",
    "Review",
    "Advisor Notes & Results",
  ];

  // Multi-select handler
  const handleGoalChange = (goal: string) => {
    setForm((prev) => {
      const goals = prev.coverage_goals.includes(goal)
        ? prev.coverage_goals.filter((g) => g !== goal)
        : [...prev.coverage_goals, goal];
      return { ...prev, coverage_goals: goals };
    });
  };

  // Currency input handler with formatting
  const handleCurrencyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // Remove non-numeric except comma
    const cleaned = value.replace(/[^\d,]/g, "");
    // Format with commas
    const formatted = formatCurrency(cleaned);
    setForm((prev) => ({ ...prev, [name]: formatted }));
    setTouched((prev) => ({ ...prev, [name]: true }));
  };

  // Generic input handler
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    let checked = false;
    if (type === "checkbox" && e.target instanceof HTMLInputElement) {
      checked = e.target.checked;
    }
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
    setTouched((prev) => ({ ...prev, [name]: true }));
  };

  // Validation for required fields in each step
  const validateStep = () => {
    if (step === 0) {
      return form.age !== "" && form.marital_status !== "" && form.dependents !== "" && form.health_status !== "";
    }
    if (step === 1) {
      return form.cash_value_importance !== "unsure" && form.permanent_coverage !== "unsure";
    }
    if (step === 2) {
      return form.coverage_goals.length > 0;
    }
    if (step === 3) {
      return true; // All optional
    }
    if (step === 4) {
      return true;
    }
    if (step === 5) {
      if (form.coverage_goals.includes("education") || form.provide_education) {
        return form.num_children !== "";
      }
      return true;
    }
    if (step === 6) {
      return true;
    }
    if (step === 7) {
      return true;
    }
    if (step === 8) {
      return true;
    }
    return true;
  };

  // Backend integration for summary step
  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {
        ...form,
        age: parseInt(form.age) || undefined,
        dependents: parseInt(form.dependents) || undefined,
        permanent_coverage: form.permanent_coverage,
        income_replacement_years: parseInt(form.support_years) || 10,
        years_of_coverage: undefined, // not used
        monthly_income: parseCurrency(form.monthly_income),
        monthly_expenses: parseCurrency(form.monthly_expenses),
        support_years: parseInt(form.support_years) || 10,
        mortgage_balance: parseCurrency(form.mortgage_balance),
        other_debts: parseCurrency(form.other_debts),
        additional_obligations: parseCurrency(form.additional_obligations),
        num_children: parseInt(form.num_children) || 0,
        education_cost_per_child:
          form.education_type === "custom"
            ? parseCurrency(form.education_cost_per_child)
            : form.education_type === "public_2"
            ? 13470 * 2
            : form.education_type === "public_4_in"
            ? 23250 * 4
            : form.education_type === "public_4_out"
            ? 40550 * 4
            : form.education_type === "private_4"
            ? 53430 * 4
            : 0,
        funeral_expenses: parseCurrency(form.funeral_expenses),
        legacy_amount: parseCurrency(form.legacy_amount),
        special_needs: form.special_needs,
        savings: parseCurrency(form.savings),
        investments: parseCurrency(form.investments),
        individual_life: parseCurrency(form.individual_life),
        group_life: parseCurrency(form.group_life),
        other_assets: parseCurrency(form.other_assets),
      };
      const res = await fetch("/api/calculate-needs-detailed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to calculate needs");
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  // When result changes, update editableSavings and projectionParams
  React.useEffect(() => {
    if (result && result.recommended_monthly_savings) {
      setEditableSavings(result.recommended_monthly_savings);
      setProjectionParams(result.projection_parameters);
      setCashValueProjection(result.cash_value_projection || []);
    }
  }, [result]);

  // Recalculate cash value projection in real time
  const recalcProjection = (monthly: number) => {
    if (!projectionParams || !result?.duration_years) return [];
    const { illustrated_rate, year1_allocation, year2plus_allocation } = projectionParams;
    let cashValue = 0;
    const arr = [];
    for (let year = 1; year <= result.duration_years; year++) {
      if (year === 1) {
        cashValue += monthly * 12 * year1_allocation;
      } else {
        cashValue = cashValue * (1 + illustrated_rate) + monthly * 12 * year2plus_allocation;
      }
      arr.push({ year, value: Math.round(cashValue / 100) * 100 });
    }
    return arr;
  };

  // Step content renderers
  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-semibold mb-1">Age *</label>
              <input name="age" type="number" min="18" value={form.age} onChange={handleChange} className="w-full border rounded-lg px-3 py-2" required />
            </div>
            <div>
              <label className="block font-semibold mb-1">Marital Status *</label>
              <select name="marital_status" value={form.marital_status} onChange={handleChange} className="w-full border rounded-lg px-3 py-2" required>
                <option value="">Select</option>
                <option value="single">Single</option>
                <option value="married">Married</option>
                <option value="divorced">Divorced</option>
                <option value="widowed">Widowed</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold mb-1">Number of Dependents *</label>
              <input name="dependents" type="number" min="0" value={form.dependents} onChange={handleChange} className="w-full border rounded-lg px-3 py-2" required />
            </div>
            <div>
              <label className="block font-semibold mb-1">Are you in generally good health?</label>
              <select name="health_status" value={form.health_status} onChange={handleChange} className="w-full border rounded-lg px-3 py-2">
                <option value="">Select</option>
                <option value="good">Yes</option>
                <option value="average">Average</option>
                <option value="poor">No</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold mb-1">Do you use tobacco?</label>
              <select name="tobacco_use" value={form.tobacco_use} onChange={handleChange} className="w-full border rounded-lg px-3 py-2">
                <option value="">Select</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>
          </div>
        );
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-semibold mb-1">Is accumulating savings in your life insurance policy important to you?</label>
              <select name="cash_value_importance" value={form.cash_value_importance} onChange={handleChange} className="w-full border rounded-lg px-3 py-2">
                <option value="unsure">Unsure</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold mb-1">Do you want permanent lifelong coverage?</label>
              <select name="permanent_coverage" value={form.permanent_coverage} onChange={handleChange} className="w-full border rounded-lg px-3 py-2">
                <option value="unsure">Unsure</option>
                <option value="yes">Yes (permanent)</option>
                <option value="no">No (temporary)</option>
              </select>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="flex flex-col gap-6">
            <div>
              <div className="font-semibold mb-2">What would you like your life insurance to help cover?</div>
              <div className="flex flex-col gap-2">
                {COVERAGE_GOALS.map((goal) => (
                  <label key={goal.value} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={form.coverage_goals.includes(goal.value)}
                      onChange={() => handleGoalChange(goal.value)}
                    />
                    {goal.label}
                  </label>
                ))}
              </div>
              {form.coverage_goals.includes("other") && (
                <input
                  name="other_coverage_goal"
                  value={form.other_coverage_goal}
                  onChange={handleChange}
                  className="w-full border rounded-lg px-3 py-2 mt-2"
                  placeholder="Please specify other coverage goal"
                />
              )}
            </div>
          </div>
        );
      case 3:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-semibold mb-1">Monthly Take-home Income</label>
              <input
                name="monthly_income"
                value={form.monthly_income}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 8,000"
              />
              <span className="text-xs text-gray-500">(We use your income to estimate how much your family would need to maintain their lifestyle if you were gone.)</span>
            </div>
            <div>
              <label className="block font-semibold mb-1">How many years would your family need support?</label>
              <select name="support_years" value={form.support_years} onChange={handleChange} className="w-full border rounded-lg px-3 py-2">
                {Array.from({ length: 21 }, (_, i) => (
                  <option key={i} value={i}>{i} {i === 1 ? 'year' : 'years'}</option>
                ))}
              </select>
              <span className="text-xs text-gray-500">(0-20 years, default 10)</span>
            </div>
            <div className="flex items-center gap-2 mt-6">
              <input
                type="checkbox"
                name="adjust_inflation"
                checked={form.adjust_inflation}
                onChange={handleChange}
              />
              <label className="font-semibold">Adjust for inflation?</label>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-semibold mb-1">Mortgage Balance</label>
              <input
                name="mortgage_balance"
                value={form.mortgage_balance}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 250,000"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Other Debts (auto, student, credit cards)</label>
              <input
                name="other_debts"
                value={form.other_debts}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 15,000"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Additional Obligations</label>
              <input
                name="additional_obligations"
                value={form.additional_obligations}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 5,000"
              />
            </div>
          </div>
        );
      case 5:
        if (!form.coverage_goals.includes("education") && !form.provide_education) {
          return <div className="text-gray-500">No education needs selected.</div>;
        }
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-semibold mb-1">Number of Children</label>
              <input
                name="num_children"
                type="number"
                min="0"
                value={form.num_children}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 2"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Type of Education</label>
              <select
                name="education_type"
                value={form.education_type}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2"
              >
                {EDUCATION_TYPES.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            {form.education_type === "custom" && (
              <div>
                <label className="block font-semibold mb-1">Custom Cost per Child</label>
                <input
                  name="education_cost_per_child"
                  value={form.education_cost_per_child}
                  onChange={handleCurrencyChange}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="e.g. 80,000"
                />
              </div>
            )}
          </div>
        );
      case 6:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-semibold mb-1">Funeral/Final Expenses</label>
              <input
                name="funeral_expenses"
                value={form.funeral_expenses}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 8,000"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Legacy or Special Bequest</label>
              <input
                name="legacy_amount"
                value={form.legacy_amount}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 50,000"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block font-semibold mb-1">Special Needs or Other Goals</label>
              <textarea
                name="special_needs"
                value={form.special_needs}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="Describe any special needs, disabilities, or other goals."
              />
            </div>
          </div>
        );
      case 7:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-semibold mb-1">Savings</label>
              <input
                name="savings"
                value={form.savings}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 20,000"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Investments</label>
              <input
                name="investments"
                value={form.investments}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 50,000"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Individual Life Insurance</label>
              <input
                name="individual_life"
                value={form.individual_life}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 100,000"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Group Life Insurance (through work)</label>
              <input
                name="group_life"
                value={form.group_life}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 50,000"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Other Assets</label>
              <input
                name="other_assets"
                value={form.other_assets}
                onChange={handleCurrencyChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="e.g. 10,000"
              />
            </div>
          </div>
        );
      case 8:
        // Review step
        return (
          <div className="flex flex-col gap-4">
            <div className="font-semibold">Review your answers before calculating:</div>
            <pre className="bg-gray-100 rounded p-4 text-xs overflow-x-auto">{JSON.stringify(form, null, 2)}</pre>
          </div>
        );
      case 9:
        return (
          <div className="flex flex-col gap-6">
            <div>
              <label className="block font-semibold mb-1">Advisor Notes (optional)</label>
              <textarea
                name="advisor_notes"
                value={form.advisor_notes}
                onChange={handleChange}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="Add any notes or context for this assessment."
              />
            </div>
            <button
              className="bg-[#1B365D] text-white rounded-lg px-6 py-2 font-semibold shadow hover:bg-blue-900 disabled:opacity-50 w-fit"
              onClick={handleSubmit}
              disabled={loading}
            >{loading ? "Calculating..." : "Calculate & Show Results"}</button>
            {error && <div className="text-red-500">{error}</div>}
            {result && (
              <div className="bg-gray-50 rounded-xl p-6 mt-4 w-full">
                <div className="mb-4">
                  <div className="font-bold text-lg">Recommended Coverage: <span className="text-[#1B365D]">${result.recommended_coverage.toLocaleString()}</span></div>
                  <div className="text-gray-700">Gap: <span className="font-semibold">${result.gap.toLocaleString()}</span></div>
                  <div className="text-gray-700">Duration: <span className="font-semibold">{
                    result.product_recommendation && result.product_recommendation.includes("IUL")
                      ? "permanent"
                      : (result.duration_years || "-") + " years"
                  }</span></div>
                </div>
                {result.product_recommendation && (
                  <div className="mb-4">
                    <div className="font-bold text-lg text-[#1B365D]">Product Recommendation: {result.product_recommendation}</div>
                    <div className="text-gray-700 mb-2">{result.product_description || "JPM TermVest+ is a flexible life insurance solution that allows you to start with affordable term coverage and, when ready, convert to a permanent Indexed Universal Life (IUL) policy that builds cash value. The IUL track offers the potential for tax-advantaged growth, flexible premiums, and a lifetime death benefit."}</div>
                    <div className="text-gray-700 mb-2"><b>Why?</b> {result.rationale}</div>
                  </div>
                )}
                {result.product_recommendation && result.product_recommendation.includes("IUL") && (
                  <div className="mb-4">
                    <label className="block font-semibold mb-1">Monthly Cash Value Savings:</label>
                    <div className="text-sm text-gray-600 mb-2">
                      Based on your input data, this is our calculated suggested monthly cash value savings. You can adjust this value at any time to reflect changes in your financial situation (e.g., saving more or less).
                    </div>
                    <input
                      type="number"
                      min={50}
                      step={10}
                      value={editableSavings ?? result.recommended_monthly_savings}
                      onChange={e => {
                        const val = Number(e.target.value);
                        setEditableSavings(val);
                        setCashValueProjection(recalcProjection(val));
                      }}
                      className="w-40 border rounded-lg px-3 py-2"
                    />
                  </div>
                )}
                {result.product_recommendation && result.product_recommendation.includes("IUL") && (
                  <div className="mt-6">
                    <CashValueChart data={cashValueProjection} />
                    <div className="text-xs italic text-gray-500 mt-2">
                      Projection assumes illustrated rate of {projectionParams?.illustrated_rate ? (projectionParams.illustrated_rate * 100).toFixed(1) : '5.5'}%, allocations of {projectionParams?.year1_allocation ? (projectionParams.year1_allocation * 100).toFixed(0) : '20'}% in year 1 and {projectionParams?.year2plus_allocation ? (projectionParams.year2plus_allocation * 100).toFixed(0) : '60'}% in subsequent years. Actual results may vary and are not guaranteed.
                    </div>
                    <div className="my-8" />
                  </div>
                )}
                <div className="mb-4">
                  <div className="font-semibold text-lg mb-2">Coverage Breakdown</div>
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
                {result.advisor_notes && (
                  <div className="mt-4 p-4 bg-blue-50 rounded">
                    <div className="font-semibold">Advisor Notes:</div>
                    <div>{result.advisor_notes}</div>
                  </div>
                )}
                {/* Add two centered buttons at the bottom */}
                <div className="flex justify-center gap-8 mt-8">
                  <button className="bg-[#1B365D] text-white rounded-lg px-8 py-3 font-semibold shadow hover:bg-blue-900 disabled:opacity-50 text-lg">Ask Robo-Advisor</button>
                  <button className="bg-[#10B981] text-white rounded-lg px-8 py-3 font-semibold shadow hover:bg-green-700 disabled:opacity-50 text-lg">Start Application</button>
                </div>
              </div>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  // Chart components (simple, can be replaced with a chart library)
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

  return (
    <div className="w-full flex flex-col items-start min-h-[70vh] text-black">
      {/* Progress Bar */}
      <div className="w-full px-12 pt-8">
        <div className="flex items-center mb-8">
          {steps.map((label, i) => (
            <div key={i} className="flex items-center">
              <div className={`rounded-full w-8 h-8 flex items-center justify-center font-bold text-white ${i <= step ? 'bg-[#1B365D]' : 'bg-gray-300'}`}>{i + 1}</div>
              {i < steps.length - 1 && <div className={`h-1 w-12 ${i < step ? 'bg-[#1B365D]' : 'bg-gray-300'}`}></div>}
            </div>
          ))}
          <span className="ml-4 text-lg font-semibold text-[#1B365D]">{steps[step]}</span>
        </div>
      </div>
      {/* Step Content */}
      <div className="w-full px-12 pb-12">
        <div className="bg-white text-black rounded-2xl shadow p-8 min-h-[320px] w-full">
          <h2 className="text-2xl font-bold text-[#1B365D] mb-6">{steps[step]}</h2>
          {renderStep()}
          <div className="flex gap-4 mt-8">
            <button
              className="bg-gray-200 text-gray-700 rounded-lg px-6 py-2 font-semibold shadow disabled:opacity-50"
              onClick={() => setStep(s => Math.max(0, s - 1))}
              disabled={step === 0}
            >Back</button>
            {step < steps.length - 1 && (
              <button
                className="bg-[#1B365D] text-white rounded-lg px-6 py-2 font-semibold shadow hover:bg-blue-900 disabled:opacity-50"
                onClick={() => setStep(s => Math.min(steps.length - 1, s + 1))}
                disabled={!validateStep()}
              >Next</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

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

function ConversionTimelineChart({ data }: { data: any[] }) {
  if (!data || !data.length) return null;
  const maxVal = Math.max(...data.map(d => d.iul_cash_value || 0));
  return (
    <div className="w-full h-32 bg-gray-200 rounded-lg flex items-end gap-2 p-2">
      {data.map((d, i) => (
        <div key={i} className="flex flex-col items-center justify-end" style={{ height: '100%' }}>
          <div style={{ height: `${((d.iul_cash_value || 0) / (maxVal || 1)) * 100}%`, background: d.can_convert ? '#6366F1' : '#E5E7EB' }} className="w-6 rounded-t-lg"></div>
          <div className="text-xs mt-1">Yr {d.year}</div>
        </div>
      ))}
    </div>
  );
} 