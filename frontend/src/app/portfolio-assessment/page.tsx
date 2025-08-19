"use client";
import React, { useState, useRef, useEffect } from "react";
import Papa from "papaparse";
import * as XLSX from "xlsx";

// Utility functions
function formatCurrency(val: string) {
  if (!val) return "";
  const cleaned = val.replace(/[^\d]/g, "");
  if (cleaned === "") return "";
  const num = parseInt(cleaned);
  return num.toLocaleString();
}

function parseCurrency(val: string) {
  if (!val) return 0;
  return parseInt(val.replace(/[^\d]/g, "")) || 0;
}

// Portfolio data interfaces
interface PortfolioData {
  // Client Information
  client_name: string;
  age: string;
  marital_status: string;
  dependents: string;
  
  // Portfolio Summary
  total_assets: number;
  total_net_worth: number;
  liquid_assets: number;
  
  // Asset Allocation
  asset_allocation: {
    equity: number;
    fixed_income: number;
    real_estate: number;
    cash: number;
    alternative_investments: number;
  };
  
  // Account Breakdown
  accounts: {
    retirement: number;
    taxable: number;
    education: number;
    real_estate: number;
  };
  
  // Risk Profile
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  investment_horizon: number;
  
  // Existing Insurance
  current_life_insurance: number;
  policy_types: string[];
  
  // Financial Goals
  retirement_target: number;
  legacy_goals: number;
  income_replacement_needs: number;
}

interface PortfolioForm {
  // File upload
  uploaded_files: File[];
  
  // Step 1: Client Demographics
  client_name: string;
  age: string;
  marital_status: string;
  dependents: string;
  health_status: string;
  tobacco_use: string;
  
  // Step 2: Portfolio Overview
  total_assets: string;
  investable_portfolio: string;
  total_net_worth: string;
  liquid_assets: string;
  
  // Step 3: Asset Allocation
  equity_allocation: string;
  fixed_income_allocation: string;
  real_estate_allocation: string;
  cash_allocation: string;
  alternative_allocation: string;
  
  // Step 4: Account Details
  retirement_accounts: string;
  taxable_accounts: string;
  education_accounts: string;
  liabilities_total: string;
  
  // Step 5: Risk Profile & Goals
  risk_tolerance: string;
  investment_horizon: string;
  retirement_target: string;
  legacy_goals: string;
  
  // Step 6: Insurance & Protection
  current_life_insurance: string;
  individual_life: string;
  group_life: string;
  income_replacement_years: string;
  
  // Step 7: Financial Goals
  cash_value_importance: string;
  permanent_coverage: string;
  coverage_goals: string[];
  other_coverage_goal: string;
  
  // Step 8: Additional Information
  monthly_income: string;
  monthly_expenses: string;
  funeral_expenses: string;
  special_needs: string;
  
  // Calculated Results
  recommended_coverage: number;
  gap: number;
  product_recommendation: string;
  rationale: string;
  cash_value_projection: any[];
  recommended_monthly_savings: number;
  max_monthly_contribution: number;
}

const initialForm: PortfolioForm = {
  uploaded_files: [],
  client_name: "",
  age: "",
  marital_status: "",
  dependents: "",
  health_status: "",
  tobacco_use: "",
  total_assets: "",
  investable_portfolio: "",
  total_net_worth: "",
  liquid_assets: "",
  equity_allocation: "",
  fixed_income_allocation: "",
  real_estate_allocation: "",
  cash_allocation: "",
  alternative_allocation: "",
  retirement_accounts: "",
  taxable_accounts: "",
  education_accounts: "",
  liabilities_total: "",
  risk_tolerance: "moderate",
  investment_horizon: "20",
  retirement_target: "",
  legacy_goals: "",
  current_life_insurance: "",
  individual_life: "",
  group_life: "",
  funeral_expenses: "8000",
  special_needs: "",
  income_replacement_years: "10",
  cash_value_importance: "unsure",
  permanent_coverage: "unsure",
  coverage_goals: [],
  other_coverage_goal: "",
  monthly_income: "",
  monthly_expenses: "",
  recommended_coverage: 0,
  gap: 0,
  product_recommendation: "",
  rationale: "",
  cash_value_projection: [],
  recommended_monthly_savings: 0,
  max_monthly_contribution: 0,
};

export default function PortfolioAssessmentPage() {
  const [form, setForm] = useState<PortfolioForm>(initialForm);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState("");
  const [fileUploadStatus, setFileUploadStatus] = useState("");
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [editableSavings, setEditableSavings] = useState<number | null>(null);
  const [cashValueProjection, setCashValueProjection] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Step definitions
  const steps = [
    "File Upload",
    "Client Demographics", 
    "Portfolio Overview",
    "Asset Allocation",
    "Account Details",
    "Risk Profile & Goals",
    "Insurance & Protection",
    "Financial Goals",
    "Additional Information",
    "Review Data",
    "Results"
  ];

  // Streamlined file upload handler using new specialized backend
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    setFileUploadStatus("Processing your file...");
    setLoading(true);
    
    try {
      // Process each file individually for better performance
      const portfolioData = await processFilesEfficiently(Array.from(files));
      
      // Store portfolio data for dashboard display
      setPortfolioData(portfolioData);
      
      // Auto-fill form with comprehensive parsed data
      setForm(prev => ({
        ...prev,
        uploaded_files: [...prev.uploaded_files, ...Array.from(files)],
        
        // Client Demographics (from household profile)
        client_name: portfolioData.additional_fields?.client_name || portfolioData.household_profile?.client_name || prev.client_name,
        age: portfolioData.household_profile?.client_age?.toString() || prev.age,
        marital_status: portfolioData.household_profile?.marital_status?.toLowerCase() || prev.marital_status,
        dependents: portfolioData.household_profile?.dependents_count?.toString() || prev.dependents,
        health_status: portfolioData.additional_fields?.health_status?.toLowerCase() || prev.health_status,
        tobacco_use: portfolioData.additional_fields?.tobacco_use?.toLowerCase() || prev.tobacco_use,
        risk_tolerance: portfolioData.household_profile?.risk_tolerance?.toLowerCase() || prev.risk_tolerance,
        investment_horizon: portfolioData.household_profile?.time_horizon_years?.toString() || prev.investment_horizon,
        
        // Portfolio Overview (from financial summary)
        total_assets: portfolioData.financial_summary?.total_assets?.toString() || prev.total_assets,
        investable_portfolio: portfolioData.financial_summary?.investable_portfolio?.toString() || portfolioData.portfolio_overview?.investable_portfolio?.toString() || prev.investable_portfolio,
        total_net_worth: portfolioData.financial_summary?.total_net_worth?.toString() || prev.total_net_worth,
        liquid_assets: portfolioData.financial_summary?.liquid_assets?.toString() || prev.liquid_assets,
        monthly_income: portfolioData.financial_summary?.monthly_income_total?.toString() || prev.monthly_income,
        monthly_expenses: portfolioData.financial_summary?.monthly_expenses_total?.toString() || prev.monthly_expenses,
        
        // Asset Allocation
        equity_allocation: portfolioData.asset_allocation?.equity?.toString() || prev.equity_allocation,
        fixed_income_allocation: portfolioData.asset_allocation?.fixed_income?.toString() || prev.fixed_income_allocation,
        real_estate_allocation: portfolioData.asset_allocation?.real_estate?.toString() || prev.real_estate_allocation,
        cash_allocation: portfolioData.asset_allocation?.cash?.toString() || prev.cash_allocation,
        alternative_allocation: portfolioData.asset_allocation?.alternative_investments?.toString() || prev.alternative_allocation,
        
        // Account Details
        retirement_accounts: portfolioData.account_breakdown?.retirement_accounts?.toString() || prev.retirement_accounts,
        taxable_accounts: portfolioData.account_breakdown?.taxable_accounts?.toString() || prev.taxable_accounts,
        education_accounts: portfolioData.account_breakdown?.education_accounts?.toString() || prev.education_accounts,
        liabilities_total: portfolioData.financial_summary?.total_liabilities?.toString() || prev.liabilities_total,
        
        // Current Insurance
        current_life_insurance: portfolioData.current_insurance?.total_life_coverage?.toString() || prev.current_life_insurance,
        individual_life: portfolioData.current_insurance?.individual_life?.toString() || prev.individual_life,
        group_life: portfolioData.current_insurance?.group_life?.toString() || prev.group_life,
        
        // Financial Goals
        retirement_target: portfolioData.financial_goals?.retirement_target?.toString() || prev.retirement_target,
        legacy_goals: portfolioData.financial_goals?.legacy_goals?.toString() || prev.legacy_goals,
        
        // Additional Information
        funeral_expenses: portfolioData.additional_fields?.funeral_expenses?.toString() || "8000",
        special_needs: portfolioData.additional_fields?.special_needs || (portfolioData.household_profile?.dependents_count > 0 ? "Dependent care needs" : ""),
        
      }));
      
      setFileUploadStatus(`Successfully processed ${files.length} file(s). Form has been populated with extracted data.`);
      
      // Log extracted fields information for debugging
      if (portfolioData.extracted_fields) {
        console.log('Extracted fields:', portfolioData.extracted_fields);
        console.log('Data quality score:', portfolioData.extracted_fields.data_quality_score);
        console.log('Record types found:', portfolioData.extracted_fields.record_types_found);
      }
      
    } catch (err: any) {
      setFileUploadStatus(`Error: ${err.message}`);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced file processing with comprehensive error handling
  const processFilesEfficiently = async (files: File[]): Promise<any> => {
    let combinedData: any = {
      household_profile: {
        client_age: 0,
        marital_status: "",
        dependents_count: 0,
        dependents_ages: "",
        risk_tolerance: "",
        time_horizon_years: 0,
        income_w2_annual: 0,
        income_1099_annual: 0,
        spouse_income_annual: 0,
        other_income_annual: 0,
        monthly_expenses_fixed: 0,
        monthly_expenses_variable: 0,
        savings_rate_pct: 0,
        emergency_fund_target_months: 0
      },
      financial_summary: {
        total_assets: 0,
        total_portfolio_value: 0,
        investable_portfolio: 0,
        total_net_worth: 0,
        liquid_assets: 0,
        total_liabilities: 0,
        monthly_income_total: 0,
        monthly_expenses_total: 0
      },
      portfolio_overview: {
        total_assets: 0,
        investable_portfolio: 0,
        total_net_worth: 0,
        liquid_assets: 0
      },
      asset_allocation: {
        equity: 0,
        fixed_income: 0,
        real_estate: 0,
        cash: 0,
        alternative_investments: 0
      },
      account_breakdown: {
        retirement_accounts: 0,
        taxable_accounts: 0,
        education_accounts: 0,
        real_estate_value: 0,
        insurance_cash_value: 0
      },
      current_insurance: {
        individual_life: 0,
        group_life: 0,
        total_life_coverage: 0
      },
      liabilities_detail: {
        mortgage_balance: 0,
        student_loans: 0,
        credit_cards: 0,
        other_debts: 0
      },
      financial_goals: {
        retirement_target: 0,
        education_funding_needs: 0,
        legacy_goals: 0
      },
      additional_fields: {
        health_status: "Good",
        tobacco_use: "No",
        client_name: "",
        funeral_expenses: 8000,
        special_needs: ""
      },
      extracted_fields: {
        record_types_found: [],
        total_positions: 0,
        total_accounts: 0,
        data_quality_score: "Low"
      },
      processing_time: 0
    };

    const startTime = Date.now();
    let successfulFiles = 0;
    let failedFiles = 0;
    let totalStages = 0;
    let completedStages = 0;

    // Process files sequentially for better error handling
    for (let fileIndex = 0; fileIndex < files.length; fileIndex++) {
      const file = files[fileIndex];
      try {
        console.log(`Processing file ${fileIndex + 1}/${files.length}: ${file.name}`);
        setFileUploadStatus(`Processing file ${fileIndex + 1}/${files.length}: ${file.name}...`);
        
        // Convert file to base64 for efficient transmission
        const base64Content = await fileToBase64(file);
        
        // Call new comprehensive backend endpoint
        const response = await fetch('/api/analyze-portfolio-file', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            file_content: base64Content,
            file_name: file.name,
            file_type: getFileExtension(file.name)
          }),
          // Increase timeout for LLM processing
          signal: AbortSignal.timeout(120000) // 2 minutes timeout
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('File analysis failed:', response.status, errorText);
          throw new Error(`File analysis failed: ${response.status} - ${response.statusText}. Please try again.`);
        }

        const result = await response.json();
        
        if (result.success && result.data) {
          // Track processing progress
          if (result.debug_info) {
            totalStages = Math.max(totalStages, result.debug_info.stages_completed || 0);
            completedStages += result.debug_info.stages_completed || 0;
          }
          
          // Merge data intelligently (avoid double-counting)
          combinedData = mergeComprehensivePortfolioData(combinedData, result.data);
          successfulFiles++;
          
          console.log(`Successfully processed ${file.name}:`, result.data);
          setFileUploadStatus(`✅ ${file.name} processed successfully! (${successfulFiles}/${files.length} files done)`);
          
          // Show progress for multi-file uploads
          if (files.length > 1) {
            const progress = ((fileIndex + 1) / files.length) * 100;
            console.log(`File processing progress: ${progress.toFixed(1)}%`);
          }
          
        } else {
          failedFiles++;
          console.warn(`File ${file.name} analysis failed:`, result.error);
          setFileUploadStatus(`⚠️ ${file.name} failed: ${result.error} (${failedFiles} failures)`);
        }
        
      } catch (error: any) {
        failedFiles++;
        console.error(`Error processing file ${file.name}:`, error);
        setFileUploadStatus(`❌ ${file.name} error: ${error.message} (${failedFiles} failures)`);
        
        // Continue with other files instead of failing completely
        if (fileIndex === files.length - 1) {
          // Last file failed, show final status
          if (successfulFiles > 0) {
            setFileUploadStatus(`⚠️ ${successfulFiles} files processed, ${failedFiles} failed. Some data may be incomplete.`);
          } else {
            setFileUploadStatus(`❌ All files failed to process. Please check file format and try again.`);
          }
        }
      }
    }

    combinedData.processing_time = (Date.now() - startTime) / 1000;
    
    // Final processing summary
    const summary = {
      totalFiles: files.length,
      successfulFiles,
      failedFiles,
      totalStages,
      completedStages,
      averageStagesPerFile: successfulFiles > 0 ? completedStages / successfulFiles : 0
    };
    
    console.log('File processing summary:', summary);
    console.log('Combined comprehensive portfolio data:', combinedData);
    
    // Add processing summary to debug info
    combinedData.processing_summary = summary;
    
    return combinedData;
  };

  // Utility function to convert file to base64
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          // Extract base64 content (remove data:application/...;base64, prefix)
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to read file'));
        }
      };
      reader.onerror = error => reject(error);
    });
  };

  // Get file extension
  const getFileExtension = (filename: string): string => {
    return filename.split('.').pop()?.toLowerCase() || 'unknown';
  };

  // Intelligent data merging to avoid double-counting for comprehensive data
  const mergeComprehensivePortfolioData = (existing: any, newData: any): any => {
    const merged = { ...existing };
    
    // For household profile, take the most complete data
    if (newData.household_profile) {
      merged.household_profile = {
        ...merged.household_profile,
        ...newData.household_profile
      };
    }
    
    // For financial summary, take the maximum values (most comprehensive)
    if (newData.financial_summary) {
      merged.financial_summary = {
        total_assets: Math.max(existing.financial_summary.total_assets, newData.financial_summary.total_assets),
        total_portfolio_value: Math.max(existing.financial_summary.total_portfolio_value, newData.financial_summary.total_portfolio_value),
        investable_portfolio: Math.max(existing.financial_summary.investable_portfolio, newData.financial_summary.investable_portfolio),
        total_net_worth: Math.max(existing.financial_summary.total_net_worth, newData.financial_summary.total_net_worth),
        liquid_assets: Math.max(existing.financial_summary.liquid_assets, newData.financial_summary.liquid_assets),
        total_liabilities: Math.max(existing.financial_summary.total_liabilities, newData.financial_summary.total_liabilities),
        monthly_income_total: Math.max(existing.financial_summary.monthly_income_total, newData.financial_summary.monthly_income_total),
        monthly_expenses_total: Math.max(existing.financial_summary.monthly_expenses_total, newData.financial_summary.monthly_expenses_total)
      };
    }
    
    // For portfolio overview, take the maximum values
    if (newData.portfolio_overview) {
      merged.portfolio_overview = {
        total_assets: Math.max(existing.portfolio_overview?.total_assets || 0, newData.portfolio_overview.total_assets),
        investable_portfolio: Math.max(existing.portfolio_overview?.investable_portfolio || 0, newData.portfolio_overview.investable_portfolio),
        total_net_worth: Math.max(existing.portfolio_overview?.total_net_worth || 0, newData.portfolio_overview.total_net_worth),
        liquid_assets: Math.max(existing.portfolio_overview?.liquid_assets || 0, newData.portfolio_overview.liquid_assets)
      };
    }
    
    // For asset allocation, replace values (same file being processed, not different files)
    if (newData.asset_allocation) {
      merged.asset_allocation = {
        equity: newData.asset_allocation.equity, // Replace, don't add
        fixed_income: newData.asset_allocation.fixed_income, // Replace, don't add
        real_estate: newData.asset_allocation.real_estate, // Replace, don't add
        cash: newData.asset_allocation.cash, // Replace, don't add
        alternative_investments: newData.asset_allocation.alternative_investments // Replace, don't add
      };
    }
    
    // For account breakdown, sum values (different files might have different account types)
    if (newData.account_breakdown) {
      merged.account_breakdown = {
        retirement_accounts: existing.account_breakdown.retirement_accounts + newData.account_breakdown.retirement_accounts,
        taxable_accounts: existing.account_breakdown.taxable_accounts + newData.account_breakdown.taxable_accounts,
        education_accounts: existing.account_breakdown.education_accounts + newData.account_breakdown.education_accounts,

        insurance_cash_value: existing.account_breakdown.insurance_cash_value + newData.account_breakdown.insurance_cash_value
      };
    }
    
    // For current insurance, take the maximum values
    if (newData.current_insurance) {
      merged.current_insurance = {
        individual_life: Math.max(existing.current_insurance.individual_life, newData.current_insurance.individual_life),
        group_life: Math.max(existing.current_insurance.group_life, newData.current_insurance.group_life),
        total_life_coverage: Math.max(existing.current_insurance.total_life_coverage, newData.current_insurance.total_life_coverage)
      };
    }
    
    // For liabilities detail, sum values (different files might have different debt types)
    if (newData.liabilities_detail) {
      merged.liabilities_detail = {
        mortgage_balance: existing.liabilities_detail.mortgage_balance + newData.liabilities_detail.mortgage_balance,
        student_loans: existing.liabilities_detail.student_loans + newData.liabilities_detail.student_loans,
        credit_cards: existing.liabilities_detail.credit_cards + newData.liabilities_detail.credit_cards,
        other_debts: existing.liabilities_detail.other_debts + newData.liabilities_detail.other_debts
      };
    }
    
    // For financial goals, take the maximum values
    if (newData.financial_goals) {
      merged.financial_goals = {
        retirement_target: Math.max(existing.financial_goals.retirement_target, newData.financial_goals.retirement_target),
        education_funding_needs: Math.max(existing.financial_goals.education_funding_needs, newData.financial_goals.education_funding_needs),
        legacy_goals: Math.max(existing.financial_goals.legacy_goals, newData.financial_goals.legacy_goals)
      };
    }
    
    // For extracted fields, combine information
    if (newData.extracted_fields) {
      merged.extracted_fields = {
        record_types_found: [...new Set([...existing.extracted_fields.record_types_found, ...newData.extracted_fields.record_types_found])],
        total_positions: existing.extracted_fields.total_positions + newData.extracted_fields.total_positions,
        total_accounts: existing.extracted_fields.total_accounts + newData.extracted_fields.total_accounts,
        data_quality_score: newData.extracted_fields.data_quality_score === "High" ? newData.extracted_fields.data_quality_score : existing.extracted_fields.data_quality_score
      };
    }
    
    return merged;
  };

  // Legacy parsing functions removed - replaced with streamlined backend processing

  // Form handlers
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    let checked = false;
    if (type === "checkbox" && e.target instanceof HTMLInputElement) {
      checked = e.target.checked;
    }
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const handleCurrencyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const cleaned = value.replace(/[^\d,]/g, "");
    const formatted = formatCurrency(cleaned);
    
    // Validate input
    const numericValue = parseCurrency(value);
    if (numericValue < 0) {
      setError(`${name.replace(/_/g, ' ')} cannot be negative`);
      return;
    }
    
    // Clear error if validation passes
    if (error) setError(null);
    
    setForm((prev) => ({ ...prev, [name]: formatted }));
  };

  // Multi-select handler for coverage goals
  const handleGoalChange = (goal: string) => {
    setForm((prev) => {
      const goals = prev.coverage_goals.includes(goal)
        ? prev.coverage_goals.filter((g) => g !== goal)
        : [...prev.coverage_goals, goal];
      return { ...prev, coverage_goals: goals };
    });
  };

  // Step validation
  const validateStep = () => {
    if (step === 0) {
      return true; // File upload is optional
    }
    if (step === 1) {
      return form.client_name !== "" && form.age !== "" && form.marital_status !== "" && form.dependents !== "";
    }
    if (step === 2) {
      return form.total_assets !== "" || form.total_net_worth !== "";
    }
    if (step === 3) {
      return true; // Asset allocation is auto-filled but optional
    }
    if (step === 4) {
      return true; // Account details are optional
    }
    if (step === 5) {
      return form.risk_tolerance !== "" && form.investment_horizon !== "";
    }
    if (step === 6) {
      return form.income_replacement_years !== "";
    }
    if (step === 7) {
      return form.cash_value_importance !== "unsure" && form.permanent_coverage !== "unsure";
    }
    if (step === 8) {
      return true; // Additional information is optional
    }
    return true;
  };

  // Navigation functions
  const nextStep = async () => {
    console.log("nextStep called", { step, filesCount: form.uploaded_files.length });
    
    if (step < steps.length - 1) {
      // If we're on step 0 (file upload) and files are uploaded, start analysis
      if (step === 0 && form.uploaded_files.length > 0) {
        console.log("Starting analysis with files");
        setIsAnalyzing(true);
        setAnalysisProgress("Analyzing files");
        
        try {
          // Simulate analysis time
          await new Promise(resolve => setTimeout(resolve, 2000));
          setAnalysisProgress("Processing data");
          await new Promise(resolve => setTimeout(resolve, 1500));
          setAnalysisProgress("Populating form");
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          setStep(step + 1);
        } catch (error) {
          console.error("Analysis error:", error);
        } finally {
          setIsAnalyzing(false);
          setAnalysisProgress("");
        }
      } else {
        console.log("No files uploaded, proceeding directly");
        // If no files uploaded, just proceed to next step
        setStep(step + 1);
      }
    }
  };

  const prevStep = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  // Form validation function
  const validateFormData = (formData: PortfolioForm): string[] => {
    const errors: string[] = [];
    
    // Validate required fields
    if (!formData.age || parseInt(formData.age) < 18 || parseInt(formData.age) > 85) {
      errors.push("Age must be between 18 and 85");
    }
    
    if (!formData.total_assets || parseCurrency(formData.total_assets) <= 0) {
      errors.push("Total assets must be greater than 0");
    }
    
    if (!formData.investable_portfolio || parseCurrency(formData.investable_portfolio) < 0) {
      errors.push("Investable portfolio cannot be negative");
    }
    
    if (parseCurrency(formData.investable_portfolio) > parseCurrency(formData.total_assets)) {
      errors.push("Investable portfolio cannot exceed total assets");
    }
    
    if (!formData.liquid_assets || parseCurrency(formData.liquid_assets) < 0) {
      errors.push("Liquid assets cannot be negative");
    }
    
    if (parseCurrency(formData.liquid_assets) > parseCurrency(formData.total_assets)) {
      errors.push("Liquid assets cannot exceed total assets");
    }
    
    // Validate asset allocation percentages
    const equity = parseCurrency(formData.equity_allocation);
    const fixedIncome = parseCurrency(formData.fixed_income_allocation);
    const realEstate = parseCurrency(formData.real_estate_allocation);
    const cash = parseCurrency(formData.cash_allocation);
    const alternative = parseCurrency(formData.alternative_allocation);
    
    if (equity < 0 || fixedIncome < 0 || realEstate < 0 || cash < 0 || alternative < 0) {
      errors.push("Asset allocation values cannot be negative");
    }
    
    // Validate that investable portfolio allocation percentages sum to reasonable range
    const investablePortfolio = parseCurrency(formData.investable_portfolio);
    if (investablePortfolio > 0) {
      // Only count CASH and ALTERNATIVE as liquid allocation (equity and fixed income are investments)
      const liquidAllocation = cash + alternative;
      
      console.log(`Asset allocation validation:`);
      console.log(`  Equity: ${equity} (part of investable portfolio)`);
      console.log(`  Fixed Income: ${fixedIncome} (part of investable portfolio)`);
      console.log(`  Cash: ${cash} (liquid)`);
      console.log(`  Alternative: ${alternative} (liquid)`);
      console.log(`  Liquid Allocation Total: ${liquidAllocation} (cash + alternative only)`);
      console.log(`  Investable Portfolio: ${investablePortfolio}`);
      console.log(`  Real Estate: ${parseCurrency(formData.real_estate_allocation)}`);
      console.log(`  Validation threshold: ${investablePortfolio * 1.1}`);
      console.log(`  Is valid: ${liquidAllocation <= investablePortfolio * 1.1}`);
      
      if (liquidAllocation > investablePortfolio * 1.1) { // Allow 10% tolerance
        errors.push("Asset allocation values seem to exceed investable portfolio");
      }
      
      // Validate that real estate is reasonable (should be separate from investable portfolio)
      const realEstate = parseCurrency(formData.real_estate_allocation);
      if (realEstate > 0 && realEstate > investablePortfolio * 5) { // Real estate can be much larger
        console.log(`Real estate (${realEstate}) is much larger than investable portfolio (${investablePortfolio}) - this is normal`);
      }
    }
    
    return errors;
  };

  // Calculate portfolio assessment
  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    // Validate form data before submission
    const validationErrors = validateFormData(form);
    if (validationErrors.length > 0) {
      setError(`Please fix the following issues:\n${validationErrors.join('\n')}`);
      setLoading(false);
      return;
    }
    
    // Show progress indicator
    setAnalysisProgress("Analyzing portfolio data...");
    
    try {
      const res = await fetch("/api/analyze-portfolio-comprehensive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          portfolio_data: {
            // Client Information
            client_name: form.client_name,
            age: parseInt(form.age) || 35,
            marital_status: form.marital_status,
            dependents: parseInt(form.dependents) || 0,
            health_status: form.health_status,
            tobacco_use: form.tobacco_use,
            
            // Portfolio Overview
            total_assets: parseCurrency(form.total_assets),
            investable_portfolio: parseCurrency(form.investable_portfolio),
            total_net_worth: parseCurrency(form.total_net_worth),
            liquid_assets: parseCurrency(form.liquid_assets),
            monthly_income: parseCurrency(form.monthly_income),
            monthly_expenses: parseCurrency(form.monthly_expenses),
            
            // Asset Allocation - send both new and legacy field names for compatibility
            equity_allocation: parseCurrency(form.equity_allocation),
            fixed_income_allocation: parseCurrency(form.fixed_income_allocation),
            real_estate_allocation: parseCurrency(form.real_estate_allocation),
            cash_allocation: parseCurrency(form.cash_allocation),
            alternative_allocation: parseCurrency(form.alternative_allocation),
            
            // Legacy field names for backend calculations
            equity: parseCurrency(form.equity_allocation),
            fixed_income: parseCurrency(form.fixed_income_allocation),
            real_estate: parseCurrency(form.real_estate_allocation),
            cash: parseCurrency(form.cash_allocation),
            alternative_investments: parseCurrency(form.alternative_allocation),
            
            // Account Details
            retirement_accounts: parseCurrency(form.retirement_accounts),
            taxable_accounts: parseCurrency(form.taxable_accounts),
            education_accounts: parseCurrency(form.education_accounts),
            
            // Liabilities - send both new and legacy field names for compatibility
            liabilities_total: parseCurrency(form.liabilities_total),
            total_liabilities: parseCurrency(form.liabilities_total),
            
            // Insurance & Protection - send both new and legacy field names for compatibility
            current_life_insurance: parseCurrency(form.current_life_insurance),
            individual_life: parseCurrency(form.individual_life),
            group_life: parseCurrency(form.group_life),
            total_life_coverage: parseCurrency(form.individual_life) + parseCurrency(form.group_life),
            funeral_expenses: parseCurrency(form.funeral_expenses),
            special_needs: form.special_needs,
            
            // Financial Goals
            cash_value_importance: form.cash_value_importance,
            permanent_coverage: form.permanent_coverage,
            coverage_goals: form.coverage_goals,
            other_coverage_goal: form.other_coverage_goal
          }
        }),
      });
      
      if (!res.ok) throw new Error("Failed to analyze portfolio");
      
      setAnalysisProgress("Processing analysis results...");
      const data = await res.json();
      
      // Transform the new analysis structure to match frontend expectations
      if (data.success && data.analysis) {
        const analysis = data.analysis;
        const life_insurance = analysis.life_insurance_needs || {};
        const portfolio_metrics = analysis.portfolio_metrics || {};
        
        const transformedResult = {
          recommended_coverage: life_insurance.total_need || 0, // Access directly from object
          gap: life_insurance.coverage_gap || 0,
          duration_years: life_insurance.duration_years || 20,
          product_recommendation: life_insurance.product_recommendation || 'JPM TermVest+',
          rationale: life_insurance.rationale || '',

          portfolio_metrics: portfolio_metrics,
          risk_level: portfolio_metrics.risk_level || 'moderate',
          risk_score: portfolio_metrics.risk_score || 50,

          asset_allocation: portfolio_metrics.asset_allocation_percentages || {},

          key_findings: analysis.key_findings || [],
          risk_analysis: analysis.risk_analysis || [],
          opportunities: analysis.opportunities || [],
          recommendations: analysis.recommendations || [],

          // Cash value projection data
          cash_value_projection: analysis.cash_value_projection || [],
          projection_parameters: analysis.projection_parameters || {},
          recommended_monthly_savings: analysis.recommended_monthly_savings || 0,
          max_monthly_contribution: analysis.max_monthly_contribution || 0,

          // Life insurance needs breakdown (for frontend display)
          life_insurance_needs: {
            income_replacement: life_insurance.income_replacement || 0,
            debt_payoff: life_insurance.debt_payoff || 0,
            education_funding: life_insurance.education_funding || 0,
            funeral_expenses: life_insurance.funeral_expenses || 0,
            legacy_amount: life_insurance.legacy_amount || 0,
            special_needs: life_insurance.special_needs || 0,
            total_need: life_insurance.total_need || 0,
            coverage_gap: life_insurance.coverage_gap || 0
          },

          processing_time: data.processing_time_seconds || 0
        };
        setAnalysisProgress("Analysis complete!");
        setResult(transformedResult);
        
        // Debug logging to see what data we received
        console.log("Frontend received analysis data:", analysis);
        console.log("Frontend transformed result:", transformedResult);
        console.log("Asset allocation data:", transformedResult.asset_allocation);
        
        // Clear progress after a short delay
        setTimeout(() => setAnalysisProgress(""), 2000);
        
        // Set cash value projection for the chart
        if (analysis.cash_value_projection) {
          console.log("Setting cash value projection from analysis:", analysis.cash_value_projection);
          setCashValueProjection(analysis.cash_value_projection);
        } else {
          console.log("No cash value projection in analysis, using fallback");
        }
        
        // Set editable savings for IUL projections
        if (analysis.recommended_monthly_savings) {
          console.log("Setting recommended monthly savings:", analysis.recommended_monthly_savings);
          setEditableSavings(analysis.recommended_monthly_savings);
          // Also set the initial cash value projection if not already set
          if (!analysis.cash_value_projection && analysis.projection_parameters) {
            console.log("Generating fallback cash value projection with parameters:", analysis.projection_parameters);
            const initialProjection = recalcProjection(analysis.recommended_monthly_savings);
            setCashValueProjection(initialProjection);
          }
        } else {
          console.log("No recommended monthly savings found");
        }
      } else {
        setResult(data);
      }
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  // Recalculate cash value projection (copied from assessment page)
  const recalcProjection = (monthly: number) => {
    if (!result?.projection_parameters || !result?.duration_years) return [];
    const { illustrated_rate, year1_allocation, year2plus_allocation } = result.projection_parameters;
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

  // Chart components (copied from assessment page)
  const CoverageBreakdownChart = ({ breakdown }: { breakdown: any }) => {
    const total = Object.values(breakdown).reduce((sum: number, v: any) => sum + v, 0);
    const data = Object.entries(breakdown)
      .filter(([_, value]) => (value as number) > 0)
      .map(([key, value]) => ({
        label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: value as number,
        percentage: ((value as number) / total) * 100
      }));

    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];
    
    let currentAngle = 0;
    const radius = 80;
    const centerX = 100;
    const centerY = 100;

    return (
      <div className="flex justify-center items-start">
        <svg width="200" height="200" className="flex-shrink-0">
          {data.map((slice, index) => {
            const sliceAngle = (slice.percentage / 100) * 2 * Math.PI;
            const x1 = centerX + radius * Math.cos(currentAngle);
            const y1 = centerY + radius * Math.sin(currentAngle);
            const x2 = centerX + radius * Math.cos(currentAngle + sliceAngle);
            const y2 = centerY + radius * Math.sin(currentAngle + sliceAngle);
            
            const largeArcFlag = sliceAngle > Math.PI ? 1 : 0;
            const pathData = [
              `M ${centerX} ${centerY}`,
              `L ${x1} ${y1}`,
              `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
              'Z'
            ].join(' ');

            currentAngle += sliceAngle;

            return (
              <g key={index}>
                <path
                  d={pathData}
                  fill={colors[index % colors.length]}
                  stroke="white"
                  strokeWidth="2"
                />
              </g>
            );
          })}
        </svg>
        <div className="ml-6 space-y-2 min-w-0 flex-1">
          {data.map((slice, index) => (
            <div key={index} className="flex items-center">
              <div 
                className="w-4 h-4 rounded mr-2 flex-shrink-0" 
                style={{ backgroundColor: colors[index % colors.length] }}
              />
              <span className="text-sm text-gray-700 truncate">
                {slice.label}: ${slice.value.toLocaleString()} ({slice.percentage.toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const CashValueChart = ({ data }: { data: any[] }) => {
    if (!data || data.length === 0) return <div>No projection data available</div>;

    const maxValue = Math.max(...data.map(d => d.value));
    // Standardize to 40 years for consistent X-axis
    const maxYear = 40;
    const width = 600;
    const height = 300;
    const padding = 40;

    const xScale = (year: number) => ((year - 1) / (maxYear - 1)) * (width - 2 * padding) + padding;
    const yScale = (value: number) => height - padding - ((value / maxValue) * (height - 2 * padding));

    const pathData = data.map((point, index) => {
      const x = xScale(point.year);
      const y = yScale(point.value);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    return (
      <div className="w-full">
        <svg width={width} height={height} className="mx-auto">
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map(percent => {
            const y = height - padding - (percent / 100) * (height - 2 * padding);
            return (
              <g key={percent}>
                <line
                  x1={padding}
                  y1={y}
                  x2={width - padding}
                  y2={y}
                  stroke="#E5E7EB"
                  strokeWidth="1"
                />
                <text x={padding - 10} y={y + 4} fontSize="12" fill="#6B7280">
                  ${Math.round((percent / 100) * maxValue).toLocaleString()}
                </text>
              </g>
            );
          })}
          
          {/* X-axis labels - standardized to show key years */}
          {[1, 10, 20, 30, 40].map(year => (
            <text
              key={year}
              x={xScale(year)}
              y={height - 10}
              fontSize="12"
              fill="#6B7280"
              textAnchor="middle"
            >
              Year {year}
            </text>
          ))}
          
          {/* Line chart */}
          <path
            d={pathData}
            stroke="#3B82F6"
            strokeWidth="3"
            fill="none"
          />
          
          {/* Data points */}
          {data.map((point, index) => (
            <circle
              key={index}
              cx={xScale(point.year)}
              cy={yScale(point.value)}
              r="4"
              fill="#3B82F6"
            />
          ))}
        </svg>
      </div>
    );
  };

  

  return (
    <div className="w-full flex flex-col items-center min-h-[70vh] text-black">
      {/* Header */}
      <div className="w-full px-12 pt-8 text-center">
        <h1 className="text-3xl font-bold text-[#1B365D] mb-2">Client Portfolio Assessment</h1>
        <p className="text-gray-600">Upload client files and analyze life insurance in the context of their full portfolio</p>
      </div>

      {!result ? (
        /* Portfolio Assessment Form */
        <div className="w-full px-12 pb-12">
          <div className="bg-white text-black rounded-2xl shadow p-8 min-h-[320px] w-full max-w-4xl mx-auto">
            {/* Progress Indicator */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-[#1B365D]">Step {step + 1} of {steps.length}</h2>
                <span className="text-sm text-gray-600">{Math.round(((step + 1) / steps.length) * 100)}% Complete</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-[#1B365D] h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((step + 1) / steps.length) * 100}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-gray-600">
                {steps.map((stepName, index) => (
                  <span 
                    key={index}
                    className={`${index <= step ? 'text-[#1B365D] font-medium' : ''}`}
                  >
                    {stepName}
                  </span>
                ))}
              </div>
            </div>
            
            {/* Step-based content rendering */}
            {step === 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Client Files (Optional)</h3>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => handleFileUpload(e.target.files)}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-[#1B365D] text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-900 mb-2 text-sm"
                  >
                    Choose Files
                  </button>
                  <p className="text-xs text-gray-600">
                    Upload investment holdings, net worth summary, or other financial documents
                  </p>
                  {fileUploadStatus && (
                    <p className="text-xs mt-2 text-blue-600">{fileUploadStatus}</p>
                  )}
                  
                  {/* File List */}
                  {form.uploaded_files.length > 0 && (
                    <div className="mt-4 text-left">
                      <h4 className="font-semibold text-sm mb-2">Uploaded Files:</h4>
                      <div className="space-y-2">
                        {form.uploaded_files.map((file, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                            <span className="text-xs text-gray-700">{file.name}</span>
                            <button
                              onClick={() => {
                                setForm(prev => ({
                                  ...prev,
                                  uploaded_files: prev.uploaded_files.filter((_, i) => i !== index)
                                }));
                              }}
                              className="text-red-500 hover:text-red-700 text-xs"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                {/* AI Analysis Loading State */}
                {isAnalyzing && (
                  <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-center space-x-3">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                      <div className="text-blue-800 font-medium">
                        {analysisProgress}
                        <span className="animate-pulse">...</span>
                      </div>
                    </div>
                    <p className="text-xs text-blue-600 mt-2 text-center">
                      Our AI is analyzing your files and populating the form
                    </p>
                  </div>
                )}

                {/* File Processing Status */}
                {loading && !isAnalyzing && (
                  <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center justify-center space-x-3">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-600"></div>
                      <div className="text-yellow-800 font-medium">
                        Processing file...
                      </div>
                    </div>
                    <p className="text-xs text-yellow-600 mt-2 text-center">
                      Please wait while we process your file. Do not click Next until processing is complete.
                    </p>
                  </div>
                )}

                {/* File Upload Success Status */}
                {fileUploadStatus && !loading && !isAnalyzing && (
                  <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <p className="text-green-800 text-sm">{fileUploadStatus}</p>
                    </div>
                    <p className="text-xs text-green-600 mt-2">
                      File processed successfully! You can now click Next to continue.
                    </p>
                  </div>
                )}


              </div>
            )}

            {step === 1 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Client Demographics</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Client Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      name="client_name"
                      value={form.client_name}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="Enter client name"
                    />
                  </div>
                  
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
                      placeholder="Enter age"
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
                      Dependents <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      name="dependents"
                      value={form.dependents}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="Number of dependents"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Information</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Health Status</label>
                    <select
                      name="health_status"
                      value={form.health_status}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                    >
                      <option value="">Select health status</option>
                      <option value="excellent">Excellent</option>
                      <option value="good">Good</option>
                      <option value="fair">Fair</option>
                      <option value="poor">Poor</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Tobacco Use</label>
                    <select
                      name="tobacco_use"
                      value={form.tobacco_use}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                    >
                      <option value="">Select tobacco use</option>
                      <option value="no">No</option>
                      <option value="yes">Yes</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Overview</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Total Assets
                    </label>
                    <input
                      type="text"
                      name="total_assets"
                      value={form.total_assets}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 3,000,000"
                    />
                    <p className="text-sm text-gray-600 mt-1">Includes all assets (real estate, investments, cash)</p>
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Investable Portfolio
                    </label>
                    <input
                      type="text"
                      name="investable_portfolio"
                      value={form.investable_portfolio || ''}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 1,500,000"
                    />
                    <p className="text-sm text-gray-600 mt-1">Excludes real estate (for allocation percentages)</p>
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Total Net Worth
                    </label>
                    <input
                      type="text"
                      name="total_net_worth"
                      value={form.total_net_worth}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 5,000,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Liquid Assets
                    </label>
                    <input
                      type="text"
                      name="liquid_assets"
                      value={form.liquid_assets}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 85,000"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Income Information</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Monthly Income</label>
                    <input
                      type="text"
                      name="monthly_income"
                      value={form.monthly_income}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 15,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Monthly Expenses</label>
                    <input
                      type="text"
                      name="monthly_expenses"
                      value={form.monthly_expenses}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 8,000"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 3 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Allocation</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block font-semibold mb-1">Equity</label>
                      <input
                        type="text"
                        name="equity_allocation"
                        value={form.equity_allocation}
                        onChange={handleCurrencyChange}
                        className="w-full border rounded-lg px-3 py-2 text-black"
                        placeholder="e.g. 2,000,000"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold mb-1">Fixed Income</label>
                      <input
                        type="text"
                        name="fixed_income_allocation"
                        value={form.fixed_income_allocation}
                        onChange={handleCurrencyChange}
                        className="w-full border rounded-lg px-3 py-2 text-black"
                        placeholder="e.g. 400,000"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold mb-1">Real Estate</label>
                      <input
                        type="text"
                        name="real_estate_allocation"
                        value={form.real_estate_allocation}
                        onChange={handleCurrencyChange}
                        className="w-full border rounded-lg px-3 py-2 text-black"
                        placeholder="e.g. 3,750,000"
                      />
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="block font-semibold mb-1">Cash</label>
                      <input
                        type="text"
                        name="cash_allocation"
                        value={form.cash_allocation}
                        onChange={handleCurrencyChange}
                        className="w-full border rounded-lg px-3 py-2 text-black"
                        placeholder="e.g. 85,000"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold mb-1">Alternative Investments</label>
                      <input
                        type="text"
                        name="alternative_allocation"
                        value={form.alternative_allocation}
                        onChange={handleCurrencyChange}
                        className="w-full border rounded-lg px-3 py-2 text-black"
                        placeholder="e.g. 1,500,000"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Details</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Retirement Accounts</label>
                    <input
                      type="text"
                      name="retirement_accounts"
                      value={form.retirement_accounts}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 1,200,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Taxable Accounts</label>
                    <input
                      type="text"
                      name="taxable_accounts"
                      value={form.taxable_accounts}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 500,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Education Accounts (529)</label>
                    <input
                      type="text"
                      name="education_accounts"
                      value={form.education_accounts}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 68,640"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Liabilities</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Total Liabilities</label>
                    <input
                      type="text"
                      name="liabilities_total"
                      value={form.liabilities_total}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 1,100,000"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Profile</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Risk Tolerance <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="risk_tolerance"
                      value={form.risk_tolerance}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                    >
                      <option value="">Select risk tolerance</option>
                      <option value="conservative">Conservative</option>
                      <option value="moderate">Moderate</option>
                      <option value="aggressive">Aggressive</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Investment Horizon (Years) <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="investment_horizon"
                      value={form.investment_horizon}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                    >
                      <option value="">Select horizon</option>
                      <option value="5">5 years</option>
                      <option value="10">10 years</option>
                      <option value="15">15 years</option>
                      <option value="20">20 years</option>
                      <option value="25">25 years</option>
                      <option value="30">30+ years</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Financial Goals</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Retirement Target</label>
                    <input
                      type="text"
                      name="retirement_target"
                      value={form.retirement_target}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 5,000,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Legacy Goals</label>
                    <input
                      type="text"
                      name="legacy_goals"
                      value={form.legacy_goals}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 1,000,000"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 6 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Insurance</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Current Life Insurance</label>
                    <input
                      type="text"
                      name="current_life_insurance"
                      value={form.current_life_insurance}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 500,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Individual Life Insurance</label>
                    <input
                      type="text"
                      name="individual_life"
                      value={form.individual_life}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 300,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Group Life Insurance</label>
                    <input
                      type="text"
                      name="group_life"
                      value={form.group_life}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 200,000"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Protection Needs</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Income Replacement Years <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="income_replacement_years"
                      value={form.income_replacement_years}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                    >
                      <option value="">Select years</option>
                      <option value="5">5 years</option>
                      <option value="10">10 years</option>
                      <option value="15">15 years</option>
                      <option value="20">20 years</option>
                    </select>
                  </div>
                  
                </div>
              </div>
            )}

            {step === 7 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Insurance Preferences</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Cash Value Importance <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="cash_value_importance"
                      value={form.cash_value_importance}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                    >
                      <option value="">Select preference</option>
                      <option value="yes">Yes, important</option>
                      <option value="no">No, protection only</option>
                      <option value="unsure">Unsure</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">
                      Permanent Coverage <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="permanent_coverage"
                      value={form.permanent_coverage}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                    >
                      <option value="">Select preference</option>
                      <option value="yes">Yes, permanent</option>
                      <option value="no">No, temporary</option>
                      <option value="unsure">Unsure</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Coverage Goals</h3>
                  
                  <div className="space-y-2">
                    <label className="block font-semibold mb-2">Select Coverage Goals:</label>
                    {["income_replacement", "debt_payoff", "education", "funeral", "legacy"].map((goal) => (
                      <label key={goal} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={form.coverage_goals.includes(goal)}
                          onChange={() => handleGoalChange(goal)}
                          className="mr-2"
                        />
                        <span className="text-sm">
                          {goal === "income_replacement" && "Income Replacement"}
                          {goal === "debt_payoff" && "Debt Payoff"}
                          {goal === "education" && "Education Funding"}
                          {goal === "funeral" && "Funeral Expenses"}
                          {goal === "legacy" && "Legacy/Inheritance"}
                        </span>
                      </label>
                    ))}
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Other Coverage Goal</label>
                    <input
                      type="text"
                      name="other_coverage_goal"
                      value={form.other_coverage_goal}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="Describe other goals"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 8 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Information</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Funeral Expenses</label>
                    <input
                      type="text"
                      name="funeral_expenses"
                      value={form.funeral_expenses}
                      onChange={handleCurrencyChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. 8,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-semibold mb-1">Special Needs</label>
                    <input
                      type="text"
                      name="special_needs"
                      value={form.special_needs}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black"
                      placeholder="e.g. Disabled dependent care"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Notes</h3>
                  
                  <div>
                    <label className="block font-semibold mb-1">Additional Notes</label>
                    <textarea
                      name="other_coverage_goal"
                      value={form.other_coverage_goal}
                      onChange={handleChange}
                      className="w-full border rounded-lg px-3 py-2 text-black h-20"
                      placeholder="Any additional information or special circumstances..."
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 9 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Review Your Data</h3>
                  <p className="text-gray-600">Please review all the information you've provided before proceeding to the analysis</p>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-gray-800 mb-4">Portfolio Assessment Data Summary</h4>
                  <div className="bg-white rounded-lg p-4 border">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
{JSON.stringify({
  // Client Demographics
  "Client Information": {
    "Client Name": form.client_name || "Not provided",
    "Age": form.age || "Not provided",
    "Marital Status": form.marital_status || "Not provided",
    "Dependents": form.dependents || "Not provided",
    "Health Status": form.health_status || "Not provided",
    "Tobacco Use": form.tobacco_use || "Not provided"
  },
  // Portfolio Overview
  "Portfolio Overview": {
            "Total Assets": form.total_assets ? `$${parseCurrency(form.total_assets).toLocaleString()}` : "Not provided",
    "Total Net Worth": form.total_net_worth ? `$${parseCurrency(form.total_net_worth).toLocaleString()}` : "Not provided",
    "Liquid Assets": form.liquid_assets ? `$${parseCurrency(form.liquid_assets).toLocaleString()}` : "Not provided"
  },
  // Asset Allocation
  "Asset Allocation": {
    "Equity Allocation": form.equity_allocation ? `$${parseCurrency(form.equity_allocation).toLocaleString()}` : "Not provided",
    "Fixed Income Allocation": form.fixed_income_allocation ? `$${parseCurrency(form.fixed_income_allocation).toLocaleString()}` : "Not provided",
    "Real Estate Allocation": form.real_estate_allocation ? `$${parseCurrency(form.real_estate_allocation).toLocaleString()}` : "Not provided",
    "Cash Allocation": form.cash_allocation ? `$${parseCurrency(form.cash_allocation).toLocaleString()}` : "Not provided",
    "Alternative Allocation": form.alternative_allocation ? `$${parseCurrency(form.alternative_allocation).toLocaleString()}` : "Not provided"
  },
  // Account Details
  "Account Details": {
    "Retirement Accounts": form.retirement_accounts ? `$${parseCurrency(form.retirement_accounts).toLocaleString()}` : "Not provided",
    "Taxable Accounts": form.taxable_accounts ? `$${parseCurrency(form.taxable_accounts).toLocaleString()}` : "Not provided",
    "Education Accounts": form.education_accounts ? `$${parseCurrency(form.education_accounts).toLocaleString()}` : "Not provided",
    "Liabilities Total": form.liabilities_total ? `$${parseCurrency(form.liabilities_total).toLocaleString()}` : "Not provided"
  },
  // Risk Profile & Goals
  "Risk Profile & Goals": {
    "Risk Tolerance": form.risk_tolerance || "Not provided",
    "Investment Horizon": form.investment_horizon ? `${form.investment_horizon} years` : "Not provided",
    "Retirement Target": form.retirement_target ? `$${parseCurrency(form.retirement_target).toLocaleString()}` : "Not provided",
    "Legacy Goals": form.legacy_goals ? `$${parseCurrency(form.legacy_goals).toLocaleString()}` : "Not provided"
  },
  // Insurance & Protection
  "Insurance & Protection": {
    "Current Life Insurance": form.current_life_insurance ? `$${parseCurrency(form.current_life_insurance).toLocaleString()}` : "Not provided",
    "Individual Life": form.individual_life ? `$${parseCurrency(form.individual_life).toLocaleString()}` : "Not provided",
    "Group Life": form.group_life ? `$${parseCurrency(form.group_life).toLocaleString()}` : "Not provided",
    "Income Replacement Years": form.income_replacement_years ? `${form.income_replacement_years} years` : "Not provided"
  },
  // Financial Goals
  "Financial Goals": {
    "Cash Value Importance": form.cash_value_importance || "Not provided",
    "Permanent Coverage": form.permanent_coverage || "Not provided",
    "Coverage Goals": form.coverage_goals.length > 0 ? form.coverage_goals.join(", ") : "Not provided",
    "Other Coverage Goal": form.other_coverage_goal || "Not provided"
  },
  // Additional Information
  "Additional Information": {
    "Monthly Income": form.monthly_income ? `$${parseCurrency(form.monthly_income).toLocaleString()}` : "Not provided",
    "Monthly Expenses": form.monthly_expenses ? `$${parseCurrency(form.monthly_expenses).toLocaleString()}` : "Not provided",
    "Funeral Expenses": form.funeral_expenses ? `$${parseCurrency(form.funeral_expenses).toLocaleString()}` : "Not provided",
    "Special Needs": form.special_needs || "Not provided"
  },
  // File Upload
  "File Upload": {
    "Uploaded Files": form.uploaded_files.length > 0 ? form.uploaded_files.map(f => f.name).join(", ") : "No files uploaded"
  }
}, null, 2)}
                    </pre>
                  </div>
                </div>
                
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="text-lg font-semibold text-blue-800 mb-2">Ready to Analyze?</h4>
                  <p className="text-blue-700 text-sm">
                    All your portfolio and personal information has been captured. Click "Analyze Portfolio" to generate your comprehensive life insurance needs assessment and portfolio analysis.
                  </p>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="mt-8 flex justify-between">
              <button
                onClick={prevStep}
                disabled={step === 0}
                className="bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              
              {step === 9 ? (
                <button
                  onClick={handleCalculate}
                  disabled={loading || !validateStep()}
                  className="bg-[#1B365D] text-white px-8 py-3 rounded-lg font-semibold shadow hover:bg-blue-900 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Analyzing Portfolio..." : "Analyze Portfolio"}
                </button>
              ) : (
                <button
                  onClick={() => nextStep()}
                  disabled={!validateStep() || isAnalyzing || loading}
                  className="bg-[#1B365D] text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-900 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? "Analyzing..." : loading ? "Processing File..." : "Next"}
                </button>
              )}
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
              <div className="bg-white rounded-lg p-6 shadow-sm border text-center hover:shadow-md transition-shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Recommended Coverage</h3>
                <p className="text-3xl font-bold text-gray-900">${result.recommended_coverage?.toLocaleString() || 0}</p>
                <p className="text-sm text-gray-500 mt-1">Based on your portfolio analysis</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-sm border text-center hover:shadow-md transition-shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Coverage Gap</h3>
                <p className="text-3xl font-bold text-gray-900">${result.gap?.toLocaleString() || 0}</p>
                <p className="text-sm text-gray-500 mt-1">Unprotected financial risk</p>
              </div>
              <div className="bg-white rounded-lg p-6 shadow-sm border text-center hover:shadow-md transition-shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Recommended Duration</h3>
                <p className="text-3xl font-bold text-gray-900">
                  {result.product_recommendation?.includes("IUL") 
                    ? "Permanent" 
                    : `${result.duration_years} Years`}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {result.product_recommendation?.includes("IUL") 
                    ? "Lifetime protection" 
                    : "Term coverage"}
                </p>
              </div>
            </div>

            {/* Enhanced Portfolio Analysis */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Portfolio Analysis</h3>
                <div className="text-sm text-gray-500">
                  Last updated: {new Date().toLocaleDateString()}
                </div>
              </div>
              
              {/* Portfolio Health Score */}
              <div className="mb-8">
                <h4 className="font-semibold text-gray-800 mb-4">Portfolio Health Score</h4>
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <span className="text-xl font-medium text-gray-800">Overall Portfolio Health:</span>
                      <div className="text-3xl font-bold text-gray-900 mt-1">
                        {result?.portfolio_metrics?.portfolio_health_score || 0}/100
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-gray-900">
                        {(() => {
                          const score = result?.portfolio_metrics?.portfolio_health_score || 0;
                          return score >= 85 ? 'Excellent' : score >= 70 ? 'Good' : 'Needs Attention';
                        })()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {(() => {
                          const score = result?.portfolio_metrics?.portfolio_health_score || 0;
                          return score >= 85 ? 'Strong diversification and liquidity' : 
                                 score >= 70 ? 'Good balance with room for improvement' : 
                                 'Consider rebalancing and increasing liquidity';
                        })()}
                      </div>
                    </div>
                  </div>
                  
                  {/* Health Indicators */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-lg font-semibold text-gray-900">✓</div>
                      <div className="text-sm font-medium">Diversification</div>
                      <div className="text-xs text-gray-500">Well balanced</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-lg font-semibold text-gray-900">✓</div>
                      <div className="text-sm font-medium">Liquidity</div>
                      <div className="text-xs text-gray-500">Adequate reserves</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-lg font-semibold text-gray-900">✓</div>
                      <div className="text-sm font-medium">Risk Management</div>
                      <div className="text-xs text-gray-500">Appropriate level</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Asset Allocation Chart */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">Asset Allocation</h4>
                  <CoverageBreakdownChart breakdown={{
                    Equity: parseCurrency(form.equity_allocation),
                    "Fixed Income": parseCurrency(form.fixed_income_allocation),
                    "Real Estate": parseCurrency(form.real_estate_allocation),
                    Cash: parseCurrency(form.cash_allocation),
                    "Alternative Investments": parseCurrency(form.alternative_allocation)
                  }} />
                </div>

                {/* Account Type Breakdown */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">Account Distribution</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Retirement Accounts:</span>
                      <span className="font-semibold">${parseCurrency(form.retirement_accounts).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Taxable Accounts:</span>
                      <span className="font-semibold">${parseCurrency(form.taxable_accounts).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Education Accounts:</span>
                      <span className="font-semibold">${parseCurrency(form.education_accounts).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center border-t pt-2">
                      <span className="font-medium">Total Assets:</span>
                      <span className="font-bold">${(parseCurrency(form.retirement_accounts) + parseCurrency(form.taxable_accounts) + parseCurrency(form.education_accounts)).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center border-t pt-2">
                      <span className="font-medium text-gray-900">Total Liabilities:</span>
                      <span className="font-bold text-gray-900">${parseCurrency(form.liabilities_total).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Comprehensive Portfolio Summary */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-800 mb-3">Portfolio Summary</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h5 className="font-medium text-gray-800 mb-2">Total Assets</h5>
                    <div className="text-2xl font-bold text-gray-900">
                      ${parseCurrency(form.total_assets).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      All assets including real estate
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h5 className="font-medium text-gray-800 mb-2">Investable Portfolio</h5>
                    <div className="text-2xl font-bold text-gray-900">
                      ${parseCurrency(form.investable_portfolio).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Excluding real estate
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h5 className="font-medium text-gray-800 mb-2">Total Net Worth</h5>
                    <div className="text-2xl font-bold text-gray-900">
                      ${parseCurrency(form.total_net_worth).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Including all assets & liabilities
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h5 className="font-medium text-gray-800 mb-2">Liquid Assets</h5>
                    <div className="text-2xl font-bold text-gray-900">
                      ${parseCurrency(form.liquid_assets).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Cash & equivalents
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h5 className="font-medium text-gray-800 mb-2">Total Liabilities</h5>
                    <div className="text-2xl font-bold text-gray-900">
                      ${parseCurrency(form.liabilities_total).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Debts & obligations
                    </div>
                  </div>
                </div>
              </div>

              {/* Enhanced Risk Analysis */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-800 mb-3">Risk Analysis & Benchmarks</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Risk Level</h5>
                    <div className="text-lg font-bold capitalize">
                      {result?.portfolio_metrics?.risk_level || 'moderate'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {(() => {
                        const riskLevel = result?.portfolio_metrics?.risk_level || 'moderate';
                        if (riskLevel === 'aggressive') return 'High equity exposure';
                        if (riskLevel === 'moderate') return 'Balanced allocation';
                        return 'Conservative approach';
                      })()}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Risk Score</h5>
                    <div className="text-lg font-bold">
                      {result?.portfolio_metrics?.risk_score || 50}/100
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {(() => {
                        const riskScore = result?.portfolio_metrics?.risk_score || 50;
                        if (riskScore >= 80) return 'Low risk';
                        if (riskScore < 60) return 'Moderate risk';
                        return 'High risk';
                      })()}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Liquidity Ratio</h5>
                                          <div className="text-lg font-bold">
                        {result?.portfolio_metrics?.liquidity_ratio ? `${result.portfolio_metrics.liquidity_ratio.toFixed(1)}x monthly expenses` : '0x monthly expenses'}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {(() => {
                          const ratio = result?.portfolio_metrics?.liquidity_ratio || 0;
                          return ratio > 20 ? 'Excellent' : ratio > 10 ? 'Good' : 'Consider increasing';
                        })()}
                      </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Coverage Gap</h5>
                    <div className="text-lg font-bold">
                      {(() => {
                        const gap = result?.life_insurance_needs?.coverage_gap || 0;
                        const need = result?.recommended_coverage || 0;
                        return need > 0 ? ((gap / need) * 100).toFixed(1) : '0';
                      })()}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      of insurance need
                    </div>
                  </div>
                </div>
              </div>

              {/* Detailed Asset Allocation Breakdown */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-800 mb-3">Detailed Asset Allocation</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white p-4 rounded-lg border">
                    <h5 className="font-medium text-gray-700 mb-3">Asset Class Breakdown</h5>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Equity
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.equity_allocation).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {result?.portfolio_metrics?.asset_allocation_percentages?.equity || 0}%
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Fixed Income
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.fixed_income_allocation).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {result?.portfolio_metrics?.asset_allocation_percentages?.fixed_income || 0}%
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Real Estate
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.real_estate_allocation).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {result?.portfolio_metrics?.asset_allocation_percentages?.real_estate || 0}%
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Cash
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.cash_allocation).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {result?.portfolio_metrics?.asset_allocation_percentages?.cash || 0}%
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Alternative Investments
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.alternative_allocation).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {result?.portfolio_metrics?.asset_allocation_percentages?.alternative || 0}%
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border">
                    <h5 className="font-medium text-gray-700 mb-3">Account Type Breakdown</h5>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Retirement Accounts
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.retirement_accounts).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {parseCurrency(form.investable_portfolio) > 0 ? 
                              ((parseCurrency(form.retirement_accounts) / parseCurrency(form.investable_portfolio)) * 100).toFixed(1) : 0}%
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Taxable Accounts
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.taxable_accounts).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {parseCurrency(form.investable_portfolio) > 0 ? 
                              ((parseCurrency(form.taxable_accounts) / parseCurrency(form.investable_portfolio)) * 100).toFixed(1) : 0}%
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                          Education Accounts
                        </span>
                        <div className="text-right">
                          <div className="font-semibold">${parseCurrency(form.education_accounts).toLocaleString()}</div>
                          <div className="text-xs text-gray-500">
                            {parseCurrency(form.investable_portfolio) > 0 ? 
                              ((parseCurrency(form.education_accounts) / parseCurrency(form.investable_portfolio)) * 100).toFixed(1) : 0}%
                          </div>
                        </div>
                      </div>
                      
                    </div>
                  </div>
                </div>
              </div>

              {/* Portfolio Benchmarks & Industry Standards */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-800 mb-3">Portfolio Benchmarks & Industry Standards</h4>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Asset Allocation Benchmarks */}
                  <div>
                    <h5 className="font-medium text-gray-700 mb-3">Asset Allocation vs. Industry Standards</h5>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Your Equity Allocation:</span>
                        <span className="font-semibold">
                          {(() => {
                            const equity = parseCurrency(form.equity_allocation);
                            const total = parseCurrency(form.investable_portfolio);
                            return total > 0 ? ((equity / total) * 100).toFixed(1) : '0';
                          })()}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Industry Standard (Age {form.age || 35}):</span>
                        <span className="font-semibold">
                          {(() => {
                            const age = parseInt(form.age || '35');
                            return Math.max(100 - age, 20);
                          })()}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Your Fixed Income:</span>
                        <span className="font-semibold">
                          {(() => {
                            const fixedIncome = parseCurrency(form.fixed_income_allocation);
                            const total = parseCurrency(form.investable_portfolio);
                            return total > 0 ? ((fixedIncome / total) * 100).toFixed(1) : '0';
                          })()}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Recommended Fixed Income:</span>
                        <span className="font-semibold">
                          {(() => {
                            const age = parseInt(form.age || '35');
                            return Math.min(age, 40);
                          })()}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Portfolio Size Benchmarks */}
                  <div>
                    <h5 className="font-medium text-gray-700 mb-3">Portfolio Size Benchmarks</h5>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-2 bg-purple-50 rounded">
                        <span>Total Assets:</span>
                        <span className="font-semibold">${parseCurrency(form.total_assets).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-blue-50 rounded">
                        <span>Investable Portfolio:</span>
                        <span className="font-semibold">${parseCurrency(form.investable_portfolio).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Age {form.age || 35} Average:</span>
                        <span className="font-semibold">
                          {(() => {
                            const age = parseInt(form.age || '35');
                            return age < 30 ? '$50,000' : age < 40 ? '$150,000' : age < 50 ? '$300,000' : '$500,000';
                          })()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Your Net Worth:</span>
                        <span className="font-semibold">${parseCurrency(form.total_net_worth).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Net Worth to Total Assets:</span>
                        <span className="font-semibold">
                          {(() => {
                            const netWorth = parseCurrency(form.total_net_worth);
                            const totalAssets = parseCurrency(form.total_assets);
                            return totalAssets > 0 ? ((netWorth / totalAssets) * 100).toFixed(1) : '0';
                          })()}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Net Worth to Investable:</span>
                        <span className="font-semibold">
                          {(() => {
                            const netWorth = parseCurrency(form.total_net_worth);
                            const investable = parseCurrency(form.investable_portfolio);
                            return investable > 0 ? ((netWorth / investable) * 100).toFixed(1) : '0';
                          })()}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Considerations & Opportunities */}
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                {result.portfolio_analysis?.concentration_risks?.length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-800 mb-2">⚠️ Risk Considerations</h5>
                    <ul className="list-disc ml-4 text-sm text-gray-600">
                      {result.portfolio_analysis.concentration_risks.map((risk: string, index: number) => (
                        <li key={index} className="text-gray-700">{risk}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {result.portfolio_analysis?.diversification_opportunities?.length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-800 mb-2">💡 Diversification Opportunities</h5>
                    <ul className="list-disc ml-4 text-sm text-gray-600">
                      {result.portfolio_analysis.diversification_opportunities.map((opportunity: string, index: number) => (
                        <li key={index} className="text-gray-700">{opportunity}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Product Recommendation */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Product Recommendation</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-2xl font-bold text-gray-900 mb-3">{result?.product_recommendation || 'JPM TermVest+'}</h4>
                {result?.product_recommendation?.includes("IUL") ? (
                  <p className="text-gray-700 mb-2">JPM TermVest+ offers two tracks: Term and IUL. The IUL Track provides immediate access to cash value accumulation with tax-deferred growth potential, flexible premiums, and permanent coverage. Your cash value can grow based on market performance while providing a guaranteed death benefit for life.</p>
                ) : (
                  <p className="text-gray-700 mb-2">JPM TermVest+ offers two tracks: Term and IUL. The Term Track provides essential protection at an affordable premium for a specified period. You can convert to the IUL Track later to begin building cash value savings with permanent coverage when your financial situation allows.</p>
                )}
                <p className="text-gray-700"><b>Why?</b> {result?.rationale || 'Based on your financial profile and goals'}</p>
              </div>
            </div>

            {/* Enhanced IUL Portfolio Integration Analysis */}
            {result.product_recommendation?.includes("IUL") && (
              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold text-gray-900">IUL Portfolio Integration</h3>
                  <div className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium">
                    Recommended Strategy
                  </div>
                </div>
                
                <div className="bg-gray-50 p-6 rounded-lg mb-6">
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">Why IUL Makes Sense for Your Portfolio</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-800">Tax-Deferred Growth</div>
                          <div className="text-sm text-gray-600">Cash value grows tax-deferred, unlike taxable investments</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-800">Portfolio Diversification</div>
                          <div className="text-sm text-gray-600">Reduces equity exposure while maintaining growth potential</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-800">Market Protection</div>
                          <div className="text-sm text-gray-600">0% floor protection with unlimited upside potential</div>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-800">Enhanced Liquidity</div>
                          <div className="text-sm text-gray-600">Tax-free access to cash value for emergencies or opportunities</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-800">Legacy Planning</div>
                          <div className="text-sm text-gray-600">Tax-free death benefit for wealth transfer</div>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-800">Retirement Income</div>
                          <div className="text-sm text-gray-600">Tax-free retirement income supplement</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Current vs. Enhanced Portfolio */}
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Portfolio Enhancement</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span>Current Portfolio Value:</span>
                        <span className="font-semibold">${parseCurrency(form.total_assets).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>IUL Cash Value (Year 10):</span>
                        <span className="font-semibold text-gray-900">${(result.cash_value_projection?.[9]?.value || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center border-t pt-2">
                        <span className="font-medium">Enhanced Portfolio:</span>
                        <span className="font-bold text-gray-900">${(parseCurrency(form.total_assets) + (result.cash_value_projection?.[9]?.value || 0)).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Tax Efficiency Analysis */}
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Tax Efficiency Benefits</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span>Tax-Deferred Growth:</span>
                        <span className="font-semibold text-gray-900">✓ Available</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Tax-Free Withdrawals:</span>
                        <span className="font-semibold text-gray-900">✓ Available</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Tax-Free Death Benefit:</span>
                        <span className="font-semibold text-gray-900">✓ Guaranteed</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>No Required Distributions:</span>
                        <span className="font-semibold text-gray-900">✓ Flexible</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Portfolio Diversification Impact */}
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-800 mb-3">Portfolio Diversification Impact</h4>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {(() => {
                            const currentEquity = parseCurrency(form.equity_allocation);
                            const totalAssets = parseCurrency(form.total_assets);
                            const iulValue = result.cash_value_projection?.[9]?.value || 0;
                            const newTotal = totalAssets + iulValue;
                            const newEquityPct = totalAssets > 0 ? (currentEquity / newTotal) * 100 : 0;
                            return newEquityPct.toFixed(1);
                          })()}%
                        </div>
                        <div className="text-sm text-gray-600">Reduced Equity Exposure</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {(() => {
                            const iulValue = result.cash_value_projection?.[9]?.value || 0;
                            const totalAssets = parseCurrency(form.total_assets);
                            const newTotal = totalAssets + iulValue;
                            return newTotal > 0 ? ((iulValue / newTotal) * 100).toFixed(1) : '0';
                          })()}%
                        </div>
                        <div className="text-sm text-gray-600">IUL Allocation</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {(() => {
                            const currentLiquid = parseCurrency(form.liquid_assets);
                            const iulValue = result.cash_value_projection?.[9]?.value || 0;
                            const totalAssets = parseCurrency(form.total_assets);
                            const newTotal = totalAssets + iulValue;
                            return newTotal > 0 ? (((currentLiquid + iulValue) / newTotal) * 100).toFixed(1) : '0';
                          })()}%
                        </div>
                        <div className="text-sm text-gray-600">Enhanced Liquidity</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Strategic IUL Benefits Timeline */}
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-800 mb-3">Strategic Benefits Timeline</h4>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h5 className="font-semibold text-gray-800 mb-2">Short Term (1-5 years)</h5>
                        <ul className="text-sm text-gray-700 space-y-1">
                          <li>• Tax-deferred growth begins</li>
                          <li>• Death benefit protection</li>
                          <li>• Flexible premium payments</li>
                          <li>• Portfolio diversification</li>
                        </ul>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h5 className="font-semibold text-gray-800 mb-2">Medium Term (5-15 years)</h5>
                        <ul className="text-sm text-gray-700 space-y-1">
                          <li>• Significant cash value accumulation</li>
                          <li>• Tax-free withdrawal options</li>
                          <li>• Enhanced retirement planning</li>
                          <li>• Legacy building potential</li>
                        </ul>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h5 className="font-semibold text-gray-800 mb-2">Long Term (15+ years)</h5>
                        <ul className="text-sm text-gray-700 space-y-1">
                          <li>• Substantial cash value growth</li>
                          <li>• Tax-free retirement income</li>
                          <li>• Wealth transfer benefits</li>
                          <li>• Permanent protection</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* IUL vs. Traditional Investment Comparison */}
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-800 mb-3">IUL vs. Traditional Investment Comparison</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse border border-gray-300">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="border border-gray-300 px-4 py-2 text-left">Feature</th>
                          <th className="border border-gray-300 px-4 py-2 text-center">IUL</th>
                          <th className="border border-gray-300 px-4 py-2 text-center">Traditional Investment</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="border border-gray-300 px-4 py-2">Tax Treatment</td>
                          <td className="border border-gray-300 px-4 py-2 text-center text-gray-900 font-semibold">Tax-Deferred</td>
                          <td className="border border-gray-300 px-4 py-2 text-center">Taxable</td>
                        </tr>
                        <tr className="bg-gray-50">
                          <td className="border border-gray-300 px-4 py-2">Death Benefit</td>
                          <td className="border border-gray-300 px-4 py-2 text-center text-gray-900 font-semibold">Guaranteed</td>
                          <td className="border border-gray-300 px-4 py-2 text-center">None</td>
                        </tr>
                        <tr>
                          <td className="border border-gray-300 px-4 py-2">Withdrawal Flexibility</td>
                          <td className="border border-gray-300 px-4 py-2 text-center text-gray-900 font-semibold">Tax-Free</td>
                          <td className="border border-gray-300 px-4 py-2 text-center">Taxable</td>
                        </tr>
                        <tr className="bg-gray-50">
                          <td className="border border-gray-300 px-4 py-2">Required Distributions</td>
                          <td className="border border-gray-300 px-4 py-2 text-center text-gray-900 font-semibold">None</td>
                          <td className="border border-gray-300 px-4 py-2 text-center">RMDs (IRA)</td>
                        </tr>
                        <tr>
                          <td className="border border-gray-300 px-4 py-2">Market Protection</td>
                          <td className="border border-gray-300 px-4 py-2 text-center text-gray-900 font-semibold">Floor Protection</td>
                          <td className="border border-gray-300 px-4 py-2 text-center">Full Risk</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Enhanced Coverage Breakdown */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Life Insurance Needs Analysis</h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Detailed Needs Breakdown */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">Coverage Needs Breakdown</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-2 bg-blue-50 rounded">
                      <span>Income Replacement:</span>
                      <span className="font-semibold">${result?.life_insurance_needs?.income_replacement?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-green-50 rounded">
                      <span>Debts & Liabilities:</span>
                      <span className="font-semibold">${result?.life_insurance_needs?.debt_payoff?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-yellow-50 rounded">
                      <span>Education Funding:</span>
                      <span className="font-semibold">${result?.life_insurance_needs?.education_funding?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-red-50 rounded">
                      <span>Funeral Expenses:</span>
                      <span className="font-semibold">${result?.life_insurance_needs?.funeral_expenses?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-purple-50 rounded">
                      <span>Legacy/Inheritance:</span>
                      <span className="font-semibold">${result?.life_insurance_needs?.legacy_amount?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span>Special Needs:</span>
                      <span className="font-semibold">${result?.life_insurance_needs?.special_needs?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-blue-100 rounded border-t-2 border-blue-500">
                      <span className="font-bold">Total Need:</span>
                      <span className="font-bold text-xl">${result?.life_insurance_needs?.total_need?.toLocaleString() || 0}</span>
                    </div>
                  </div>
                </div>

                {/* Current Coverage vs. Gap */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">Coverage Gap Analysis</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Current Life Insurance:</span>
                      <span className="font-semibold">${(parseCurrency(form.current_life_insurance) + parseCurrency(form.individual_life) + parseCurrency(form.group_life)).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Individual Life:</span>
                      <span className="font-semibold">${parseCurrency(form.individual_life).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Group Life:</span>
                      <span className="font-semibold">${parseCurrency(form.group_life).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center border-t pt-2">
                      <span className="font-medium">Liquid Assets:</span>
                      <span className="font-semibold">${parseCurrency(form.liquid_assets).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-red-100 rounded border-t-2 border-red-500">
                      <span className="font-bold text-gray-900">Coverage Gap:</span>
                      <span className="font-bold text-xl text-gray-900">${result?.life_insurance_needs?.coverage_gap?.toLocaleString() || 0}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Coverage Breakdown Chart */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-800 mb-3">Coverage Breakdown Visualization</h4>
                <CoverageBreakdownChart breakdown={{
                  "Income Replacement": result?.life_insurance_needs?.income_replacement || 0,
                  "Debts & Liabilities": result?.life_insurance_needs?.debt_payoff || 0,
                  "Education Funding": result?.life_insurance_needs?.education_funding || 0,
                  "Funeral Expenses": result?.life_insurance_needs?.funeral_expenses || 0,
                  "Legacy/Inheritance": result?.life_insurance_needs?.legacy_amount || 0,
                  "Special Needs": result?.life_insurance_needs?.special_needs || 0
                }} />
              </div>
            </div>

            {/* Enhanced Cash Value Projection & Future Scenarios */}
            {result.product_recommendation?.includes("IUL") && (
              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">IUL Cash Value Growth & Future Scenarios</h3>
                <p className="text-gray-600 mb-4">
                  Based on your portfolio analysis, this is our calculated field for suggested monthly cash value savings. 
                  You can change this value during times of financial change (saving more or less).
                </p>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  {/* Monthly Savings Input */}
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Monthly Savings Configuration</h4>
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
                            
                            if (value > maxLimit) {
                              value = maxLimit;
                            }
                            
                            setEditableSavings(value);
                            const newProjection = recalcProjection(value);
                            setCashValueProjection(newProjection);
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
                            color = "text-gray-900";
                          } else if (percentage <= 50) {
                            level = "Medium Savings";
                            color = "text-gray-900";
                          } else if (percentage <= 75) {
                            level = "High Savings";
                            color = "text-gray-900";
                          } else {
                            level = "Maximum Savings";
                            color = "text-gray-900";
                          }
                          
                          return (
                            <div className={`text-sm font-semibold ${color}`}>
                              {level} ({percentage.toFixed(0)}% of maximum)
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </div>

                  {/* Key Milestones */}
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Key Growth Milestones</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Year 5 Cash Value:</span>
                        <span className="font-semibold text-gray-900">${(result.cash_value_projection?.[4]?.value || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Year 10 Cash Value:</span>
                        <span className="font-semibold text-gray-900">${(result.cash_value_projection?.[9]?.value || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Year 20 Cash Value:</span>
                        <span className="font-semibold text-gray-900">${(result.cash_value_projection?.[19]?.value || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Year 30 Cash Value:</span>
                        <span className="font-semibold text-gray-900">${(result.cash_value_projection?.[29]?.value || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Year 40 Cash Value:</span>
                        <span className="font-semibold text-gray-900">${(result.cash_value_projection?.[39]?.value || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span>Total Premiums Paid (40 years):</span>
                        <span className="font-semibold text-gray-900">${((editableSavings || result.recommended_monthly_savings || 400) * 12 * 40).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Cash Value Growth Chart */}
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-800 mb-3">Cash Value Growth Projection</h4>
                  <CashValueChart data={cashValueProjection} />
                  <div className="text-xs italic text-gray-500 mt-2">
                    Projection assumes illustrated rate of 6%, allocations of 85% in year 1 and 95% in subsequent years over 40 years. Actual results may vary and are not guaranteed.
                  </div>
                </div>

                {/* Future Scenarios Analysis */}
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-800 mb-3">Future Financial Scenarios</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Retirement Planning */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-semibold text-gray-800 mb-2">Retirement Planning</h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Age at Retirement:</span>
                          <span className="font-semibold">{parseInt(form.age || '35') + (result.projection_parameters?.duration_years || 30)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>IUL Cash Value:</span>
                          <span className="font-semibold text-gray-900">${(() => {
                            const duration = result.projection_parameters?.duration_years || 30;
                            const finalYearIndex = Math.min(duration - 1, (result.cash_value_projection?.length || 0) - 1);
                            return (result.cash_value_projection?.[finalYearIndex]?.value || 0).toLocaleString();
                          })()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tax-Free Income:</span>
                          <span className="font-semibold text-gray-900">${(() => {
                            const duration = result.projection_parameters?.duration_years || 30;
                            const finalYearIndex = Math.min(duration - 1, (result.cash_value_projection?.length || 0) - 1);
                            return Math.floor((result.cash_value_projection?.[finalYearIndex]?.value || 0) * 0.04).toLocaleString();
                          })()}/year</span>
                        </div>
                      </div>
                    </div>

                    {/* Legacy Planning */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-semibold text-gray-800 mb-2">Legacy Planning</h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Death Benefit:</span>
                          <span className="font-semibold">${result.recommended_coverage?.toLocaleString() || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Cash Value (Year {result.projection_parameters?.duration_years || 30}):</span>
                          <span className="font-semibold text-gray-900">${(() => {
                            const duration = result.projection_parameters?.duration_years || 30;
                            const finalYearIndex = Math.min(duration - 1, (result.cash_value_projection?.length || 0) - 1);
                            return (result.cash_value_projection?.[finalYearIndex]?.value || 0).toLocaleString();
                          })()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tax-Free Transfer:</span>
                          <span className="font-semibold text-gray-900">✓ Available</span>
                        </div>
                      </div>
                    </div>

                    {/* Emergency Fund */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-semibold text-gray-800 mb-2">Emergency Fund</h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Current Liquid Assets:</span>
                          <span className="font-semibold">${parseCurrency(form.liquid_assets).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>IUL Cash Value (Year 5):</span>
                          <span className="font-semibold text-gray-900">${(result.cash_value_projection?.[4]?.value || 0).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Enhanced Emergency Fund:</span>
                          <span className="font-semibold text-gray-900">${(parseCurrency(form.liquid_assets) + (result.cash_value_projection?.[4]?.value || 0)).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Portfolio Protection & Risk Management */}
            {result.product_recommendation?.includes("IUL") && (
              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Protection & Risk Management</h3>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Market Protection Analysis */}
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Market Protection Benefits</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                        <span>Current Market Exposure:</span>
                        <span className="font-semibold text-blue-600">
                          {(() => {
                            const equity = parseCurrency(form.equity_allocation);
                            const totalAssets = parseCurrency(form.total_assets);
                            return totalAssets > 0 ? ((equity / totalAssets) * 100).toFixed(1) : '0';
                          })()}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                        <span>Protected Assets (IUL):</span>
                        <span className="font-semibold text-green-600">
                          {(() => {
                            const iulValue = result.cash_value_projection?.[9]?.value || 0;
                            const totalAssets = parseCurrency(form.total_assets);
                            const newTotal = totalAssets + iulValue;
                            return newTotal > 0 ? ((iulValue / newTotal) * 100).toFixed(1) : '0';
                          })()}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-purple-50 rounded">
                        <span>Floor Protection:</span>
                        <span className="font-semibold text-purple-600">1%</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-orange-50 rounded">
                        <span>Cap Potential (Yearly):</span>
                        <span className="font-semibold text-orange-600">7%</span>
                      </div>
                    </div>
                  </div>

                  {/* Risk Management Strategies */}
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Risk Management Strategies</h4>
                    <div className="space-y-3">
                      <div className="p-3 bg-gray-50 rounded">
                        <h5 className="font-medium text-gray-700 mb-1">Sequence of Returns Risk</h5>
                        <p className="text-sm text-gray-600">IUL provides protection against market downturns during critical retirement years</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded">
                        <h5 className="font-medium text-gray-700 mb-1">Longevity Risk</h5>
                        <p className="text-sm text-gray-600">Permanent coverage ensures protection regardless of life expectancy</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded">
                        <h5 className="font-medium text-gray-700 mb-1">Tax Risk</h5>
                        <p className="text-sm text-gray-600">Tax-free withdrawals and death benefits provide tax efficiency</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded">
                        <h5 className="font-medium text-gray-700 mb-1">Inflation Risk</h5>
                        <p className="text-sm text-gray-600">Cash value growth potential helps maintain purchasing power</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Portfolio Stress Testing */}
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-800 mb-3">Portfolio Stress Testing Scenarios</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-semibold text-gray-800 mb-2">Market Crash Scenario</h5>
                      <div className="text-sm text-gray-700 space-y-1">
                        <div>• Traditional investments: -30%</div>
                        <div>• IUL cash value: 0% (protected)</div>
                        <div>• Portfolio protection: Enhanced</div>
                      </div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-semibold text-gray-800 mb-2">Low Interest Rate Environment</h5>
                      <div className="text-sm text-gray-700 space-y-1">
                        <div>• Traditional bonds: Low returns</div>
                        <div>• IUL cash value: Growth potential</div>
                        <div>• Portfolio yield: Maintained</div>
                      </div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-semibold text-gray-800 mb-2">High Tax Environment</h5>
                      <div className="text-sm text-gray-700 space-y-1">
                        <div>• Traditional investments: Tax burden</div>
                        <div>• IUL withdrawals: Tax-free</div>
                        <div>• Tax efficiency: Maximized</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Actionable Recommendations */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Actionable Recommendations</h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Portfolio Optimization */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">Portfolio Optimization</h4>
                  <div className="space-y-3">
                    {(() => {
                      const equity = parseCurrency(form.equity_allocation);
                      const total = parseCurrency(form.total_assets);
                      const equityPct = total > 0 ? (equity / total) * 100 : 0;
                      const age = parseInt(form.age || '35');
                      const targetEquity = Math.max(100 - age, 20);
                      
                      if (equityPct > targetEquity + 10) {
                        return (
                          <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <h5 className="font-medium text-gray-800 mb-1">Consider Reducing Equity Exposure</h5>
                            <p className="text-sm text-gray-700">
                              Your equity allocation ({equityPct.toFixed(1)}%) is above the recommended {targetEquity}% for your age. 
                              Consider rebalancing by ${Math.round((equityPct - targetEquity) * total / 100).toLocaleString()}.
                            </p>
                          </div>
                        );
                      } else if (equityPct < targetEquity - 10) {
                        return (
                          <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <h5 className="font-medium text-gray-800 mb-1">Consider Increasing Equity Exposure</h5>
                            <p className="text-sm text-gray-700">
                              Your equity allocation ({equityPct.toFixed(1)}%) is below the recommended {targetEquity}% for your age. 
                              Consider increasing by ${Math.round((targetEquity - equityPct) * total / 100).toLocaleString()}.
                            </p>
                          </div>
                        );
                      } else {
                        return (
                          <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <h5 className="font-medium text-gray-800 mb-1">Equity Allocation is Optimal</h5>
                            <p className="text-sm text-gray-700">
                              Your equity allocation ({equityPct.toFixed(1)}%) aligns well with the recommended {targetEquity}% for your age.
                            </p>
                          </div>
                        );
                      }
                    })()}
                    
                    {(() => {
                      const liquid = parseCurrency(form.liquid_assets);
                      const total = parseCurrency(form.total_assets);
                      const liquidPct = total > 0 ? (liquid / total) * 100 : 0;
                      
                      if (liquidPct < 10) {
                        return (
                          <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <h5 className="font-medium text-gray-800 mb-1">Increase Emergency Fund</h5>
                            <p className="text-sm text-gray-700">
                              Your liquidity ratio ({liquidPct.toFixed(1)}%) is below the recommended 10-20%. 
                              Consider increasing liquid assets by ${Math.round((15 - liquidPct) * total / 100).toLocaleString()}.
                            </p>
                          </div>
                        );
                      }
                      return null;
                    })()}
                  </div>
                </div>

                {/* Insurance Recommendations */}
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3">Insurance & Protection</h4>
                  <div className="space-y-3">
                    {(() => {
                      const gap = result.gap || 0;
                      const need = result.recommended_coverage || 0;
                      const gapPct = need > 0 ? (gap / need) * 100 : 0;
                      
                      if (gapPct > 50) {
                        return (
                          <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <h5 className="font-medium text-gray-800 mb-1">Critical Insurance Gap</h5>
                            <p className="text-sm text-gray-700">
                              You have a ${gap.toLocaleString()} insurance gap ({gapPct.toFixed(1)}% of need). 
                              This represents a significant risk to your family's financial security.
                            </p>
                          </div>
                        );
                      } else if (gapPct > 20) {
                        return (
                          <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <h5 className="font-medium text-gray-800 mb-1">Moderate Insurance Gap</h5>
                            <p className="text-sm text-gray-700">
                              You have a ${gap.toLocaleString()} insurance gap ({gapPct.toFixed(1)}% of need). 
                              Consider addressing this gap to ensure adequate protection.
                            </p>
                          </div>
                        );
                      } else {
                        return (
                          <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <h5 className="font-medium text-gray-800 mb-1">Insurance Coverage Adequate</h5>
                            <p className="text-sm text-gray-700">
                              Your insurance gap of ${gap.toLocaleString()} ({gapPct.toFixed(1)}% of need) is within acceptable limits.
                            </p>
                          </div>
                        );
                      }
                    })()}
                    
                    {result.product_recommendation?.includes("IUL") && (
                      <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                        <h5 className="font-medium text-gray-800 mb-1">IUL Integration Opportunity</h5>
                        <p className="text-sm text-gray-700">
                          Consider allocating ${result.recommended_monthly_savings?.toLocaleString() || 0}/month to IUL for 
                          tax-deferred growth and portfolio diversification.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Next Steps */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-800 mb-3">Recommended Next Steps</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h5 className="font-semibold text-gray-800 mb-2">Immediate (1-3 months)</h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Address critical insurance gaps</li>
                      <li>• Review and adjust asset allocation</li>
                      <li>• Establish emergency fund if needed</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h5 className="font-semibold text-gray-800 mb-2">Short-term (3-12 months)</h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Implement IUL strategy if recommended</li>
                      <li>• Rebalance portfolio quarterly</li>
                      <li>• Review tax efficiency opportunities</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h5 className="font-semibold text-gray-800 mb-2">Long-term (1-5 years)</h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Monitor portfolio performance</li>
                      <li>• Adjust strategy as life changes</li>
                      <li>• Plan for major life events</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Comprehensive Summary */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Portfolio Assessment Summary</h3>
                <div className="text-sm text-gray-500">
                  {new Date().toLocaleDateString()}
                </div>
              </div>
              
              {/* Executive Summary */}
              <div className="bg-gradient-to-r from-blue-50 to-green-50 p-6 rounded-lg mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3">Executive Summary</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Portfolio Strengths</h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• Total assets of ${parseCurrency(form.total_assets).toLocaleString()} including real estate</li>
                      <li>• Investable portfolio of ${parseCurrency(form.investable_portfolio).toLocaleString()} for allocation analysis</li>
                      <li>• {parseCurrency(form.liquid_assets) > parseCurrency(form.investable_portfolio) * 0.1 ? 'Strong' : 'Adequate'} liquidity position</li>
                      <li>• {result?.portfolio_metrics?.risk_level === 'low' ? 'Conservative' : result?.portfolio_metrics?.risk_level === 'moderate' ? 'Balanced' : 'Growth-oriented'} risk profile</li>
                      <li>• {result.product_recommendation?.includes("IUL") ? 'IUL integration opportunity identified' : 'Term coverage recommended for current needs'}</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Key Recommendations</h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• ${result.recommended_coverage?.toLocaleString() || 0} in life insurance coverage needed</li>
                      <li>• ${result.gap?.toLocaleString() || 0} coverage gap to address</li>
                      <li>• {result.product_recommendation?.includes("IUL") ? 'IUL Track' : 'Term Track'} recommended for optimal fit</li>
                      <li>• {result.product_recommendation?.includes("IUL") ? `$${result.recommended_monthly_savings?.toLocaleString() || 0}/month IUL allocation suggested` : 'Consider conversion to IUL as financial situation improves'}</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    ${parseCurrency(form.total_assets).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Total Assets</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-900">
                    ${parseCurrency(form.investable_portfolio).toLocaleString()}
                  </div>
                  <div className="text-sm text-blue-600">Investable</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {result?.portfolio_metrics?.risk_level || 'moderate'}
                  </div>
                  <div className="text-sm text-gray-600">Risk Profile</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    ${result.recommended_coverage?.toLocaleString() || 0}
                  </div>
                  <div className="text-sm text-gray-600">Insurance Need</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {result.product_recommendation?.includes("IUL") ? "IUL Track" : "Term Track"}
                  </div>
                  <div className="text-sm text-gray-600">Recommended</div>
                </div>
              </div>

              {/* Key Insights */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-3">Key Insights</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Portfolio Strengths</h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• Total assets of ${parseCurrency(form.total_assets).toLocaleString()} including real estate</li>
                      <li>• Investable portfolio of ${parseCurrency(form.investable_portfolio).toLocaleString()} for allocation analysis</li>
                      <li>• {parseCurrency(form.liquid_assets) > parseCurrency(form.investable_portfolio) * 0.1 ? 'Strong' : 'Adequate'} liquidity position</li>
                      <li>• {result?.portfolio_metrics?.risk_level === 'low' ? 'Conservative' : result?.portfolio_metrics?.risk_level === 'moderate' ? 'Balanced' : 'Growth-oriented'} risk profile</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Insurance Recommendations</h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• ${result.recommended_coverage?.toLocaleString() || 0} in life insurance coverage needed</li>
                      <li>• ${result.gap?.toLocaleString() || 0} coverage gap to address</li>
                      <li>• {result.product_recommendation?.includes("IUL") ? 'IUL Track' : 'Term Track'} recommended for optimal fit</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-[#1B365D] text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-800 transition-colors duration-200 shadow-sm">
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <span>Ask Robo-Advisor</span>
                </div>
              </button>
              <button className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 shadow-sm">
                <div className="flex items-center justify-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Start Application</span>
                </div>
              </button>
            </div>

            {/* Back Button */}
            <div className="text-center">
              <button
                onClick={() => {
                  setResult(null);
                  setForm(initialForm);
                  setError(null);
                  setEditableSavings(null);
                  setCashValueProjection([]);
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