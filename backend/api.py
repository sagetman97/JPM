"""
Two-Phase Portfolio Analysis API.
Phase 1: Fast CSV parsing and form population (2-5 seconds)
Phase 2: Comprehensive AI analysis after user confirms data (10-30 seconds)
"""

import os
import base64
import json
import asyncio
import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from root directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import Phase 1: Enhanced CSV parsing with LLM understanding
from enhanced_parser import EnhancedCSVParser

# Import Phase 2: Comprehensive AI analysis
from ai_analysis import PortfolioAnalyzer
from schemas import PortfolioAnalysisResult

# Import legacy functions for fallback
from legacy_api import (
    parse_csv_structure, create_default_household_profile, 
    create_default_financial_summary, create_default_asset_allocation,
    create_default_account_breakdown, create_default_insurance_data,
    create_default_liability_data, create_default_financial_goals,
    create_default_additional_fields
)

router = APIRouter()

class PortfolioFileRequest(BaseModel):
    file_content: str
    file_name: str
    file_type: str

class PortfolioAnalysisRequest(BaseModel):
    portfolio_data: Dict[str, Any]
    user_goals: Optional[Dict[str, Any]] = None

# Initialize systems
enhanced_parser = None
portfolio_analyzer = None

def initialize_systems():
    """Initialize both Phase 1 and Phase 2 systems"""
    global enhanced_parser, portfolio_analyzer
    
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            # Phase 1: Universal Financial Parser with LLM understanding
            enhanced_parser = EnhancedCSVParser(openai_api_key)
            print("Phase 1: Universal Financial Parser initialized successfully")
            
            # Phase 2: Comprehensive AI analysis
            portfolio_analyzer = PortfolioAnalyzer(openai_api_key)
            print("Phase 2: AI analysis system initialized successfully")
        else:
            print("OpenAI API key not found, using legacy parsing only")
    except Exception as e:
        print(f"Failed to initialize enhanced systems: {e}")
        print("Falling back to legacy parsing")

# Initialize on import
initialize_systems()

@router.post("/analyze-portfolio-file")
async def analyze_portfolio_file(request: PortfolioFileRequest):
    """
    PHASE 1: Fast CSV parsing and form population (2-5 seconds)
    Goal: Reliable data extraction for form population, no heavy processing
    """
    try:
        start_time = time.time()
        
        # Decode file content
        try:
            file_content = base64.b64decode(request.file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid file content: {str(e)}")
        
        print(f"Phase 1: Starting CSV parsing for {request.file_name}")
        
        # Try Phase 1: Enhanced LLM-based parsing first
        if enhanced_parser:
            try:
                print("Using Phase 1: Universal Financial Parser with LLM understanding...")
                result = await enhanced_parser.parse_any_file(file_content, request.file_name)
                
                if result.get("success"):
                    processing_time = result.get("processing_time_seconds", 0)
                    print(f"Phase 1: Universal LLM parsing successful in {processing_time:.2f} seconds")
                    print(f"Phase 1: Returning data structure: {json.dumps(result.get('data', {}), indent=2, default=str)}")
                    
                    return result
                else:
                    print(f"Phase 1: Enhanced parsing failed: {result.get('error')}")
                    print("Falling back to legacy parsing...")
            except Exception as e:
                print(f"Phase 1: Enhanced parsing error: {e}")
                print("Falling back to legacy parsing...")
        
        # Fallback to legacy parsing
        print("Using legacy CSV parser...")
        result = await legacy_analyze_portfolio_file(file_content, request.file_name, request.file_type)
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "data": result["data"],
            "processing_status": "extraction_complete",
            "ai_analysis_ready": True,  # Ready for Phase 2
            "phase": 1,
            "enhanced_parsing": False,
            "legacy_parsing": True,
            "processing_time_seconds": round(processing_time, 2)
        }
        
    except Exception as e:
        print(f"Phase 1: Portfolio file analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "processing_status": "failed",
            "phase": 1
        }

@router.post("/analyze-portfolio-comprehensive")
async def analyze_portfolio_comprehensive(request: PortfolioAnalysisRequest):
    """
    PHASE 2: Comprehensive AI analysis after user confirms form data (10-30 seconds)
    Goal: Generate comprehensive financial analysis using all calculation modules
    """
    try:
        start_time = time.time()
        
        if not portfolio_analyzer:
            raise HTTPException(status_code=500, detail="AI analysis system not available")
        
        print("Phase 2: Starting comprehensive portfolio analysis...")
        print("This is the heavy processing that happens after user confirms form data")
        
        # Import calculation modules
        from life_insurance_calculator import LifeInsuranceCalculator
        from portfolio_calculator import PortfolioCalculator
        
        # Initialize calculators
        life_insurance_calc = LifeInsuranceCalculator()
        portfolio_calc = PortfolioCalculator()
        
        # Calculate life insurance needs
        print("Calculating life insurance needs...")
        life_insurance_needs = life_insurance_calc.calculate_needs(request.portfolio_data)
        
        # Calculate portfolio metrics
        print("Calculating portfolio metrics...")
        portfolio_metrics = portfolio_calc.calculate_portfolio_metrics(request.portfolio_data)
        
        # Generate AI insights
        print("Generating AI insights...")
        ai_analysis = await portfolio_analyzer.analyze_portfolio(request.portfolio_data)
        
        # Calculate cash value projection data for IUL recommendations
        # Always calculate for full 40 years to provide comprehensive projections
        client_age = request.portfolio_data.get("age", 35)
        retirement_age = 65
        years_to_retirement = max(retirement_age - client_age, 20)  # At least 20 years, up to retirement
        
        print(f"DEBUG: Cash value calculation - client_age: {client_age}, retirement_age: {retirement_age}, years_to_retirement: {years_to_retirement}")
        
        monthly_contribution = _calculate_monthly_iul_contribution(
            life_insurance_needs.total_need, 
            request.portfolio_data.get("monthly_income", 0), 
            client_age
        )
        
        print(f"DEBUG: Cash value calculation - monthly_contribution: ${monthly_contribution}")
        
        # Generate projections for full 40 years, not just years to retirement
        cash_value_projection = _generate_cash_value_projections(monthly_contribution, 40)
        
        print(f"DEBUG: Cash value projection generated - {len(cash_value_projection)} years, final value: ${cash_value_projection[-1]['value'] if cash_value_projection else 0:,.0f}")
        
        comprehensive_analysis = {
            "life_insurance_needs": life_insurance_needs,
            "portfolio_metrics": portfolio_metrics,
            "key_findings": ai_analysis.key_findings,
            "risk_analysis": ai_analysis.risk_analysis,
            "opportunities": ai_analysis.opportunities,
            "recommendations": ai_analysis.recommendations,
            "missing_data": ai_analysis.missing_data,
            "goal_alignment": ai_analysis.goal_alignment,
            "concentration_risks": ai_analysis.concentration_risks,
            "tax_efficiency": ai_analysis.tax_efficiency,
            "rebalancing_needs": ai_analysis.rebalancing_needs,
            
            # Add cash value projection data for IUL recommendations
            "cash_value_projection": cash_value_projection,
            "projection_parameters": {
                "illustrated_rate": 0.06,  # 6% assumed growth rate
                "year1_allocation": 0.85,  # 85% of premium goes to cash value in year 1
                "year2plus_allocation": 0.95,  # 95% of premium goes to cash value in subsequent years
                "duration_years": 40,  # Always calculate for full 40 years
                "monthly_contribution": monthly_contribution
            },
            "recommended_monthly_savings": monthly_contribution,
            "max_monthly_contribution": _calculate_mec_limit(client_age, request.portfolio_data.get("monthly_income", 0), life_insurance_needs.total_need)
        }
        
        processing_time = time.time() - start_time
        
        print(f"Phase 2: Analysis completed in {processing_time:.2f} seconds")
        print(f"Life insurance needs: ${life_insurance_needs.total_need:,.0f}")
        print(f"Product recommendation: {life_insurance_needs.product_recommendation}")
        print(f"Portfolio health score: {portfolio_metrics.portfolio_health_score}/100")
        
        return {
            "success": True,
            "analysis": comprehensive_analysis,
            "processing_status": "analysis_complete",
            "phase": 2,
            "timestamp": time.time(),
            "processing_time_seconds": round(processing_time, 2)
        }
        
    except Exception as e:
        print(f"Phase 2: Comprehensive analysis failed: {e}")
        import traceback
        traceback.print_exc()
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "error": str(e),
            "processing_status": "analysis_failed",
            "phase": 2,
            "processing_time_seconds": round(processing_time, 2)
        }

# Helper functions for IUL calculations
def _calculate_monthly_iul_contribution(total_need: float, monthly_income: float, age: int) -> int:
    """Calculate recommended monthly IUL contribution based on financial profile"""
    try:
        # Base calculation: 2-3% of monthly income for IUL (increased from 1.5%)
        base_monthly = monthly_income * 0.025  # 2.5% of monthly income
        
        # Adjust based on age and need
        if age < 40:
            age_multiplier = 1.3  # Younger clients can contribute more (increased from 1.2)
        elif age < 50:
            age_multiplier = 1.1  # Standard contribution (increased from 1.0)
        else:
            age_multiplier = 0.9  # Older clients may contribute less (increased from 0.8)
        
        # Adjust based on total need (more aggressive for high needs)
        if total_need > 3000000:  # Very high need
            need_multiplier = 1.6  # Increased from 1.3
        elif total_need > 2000000:  # High need
            need_multiplier = 1.4  # Increased from 1.1
        else:
            need_multiplier = 1.2  # Increased from 1.0
        
        # Calculate final monthly contribution
        monthly_contribution = base_monthly * age_multiplier * need_multiplier
        
        # Round to nearest $50 and apply limits
        monthly_contribution = round(monthly_contribution / 50) * 50
        monthly_contribution = max(300, min(monthly_contribution, 3000))  # Increased range $300-$3000
        
        return int(monthly_contribution)
        
    except Exception as e:
        print(f"Error calculating monthly IUL contribution: {e}")
        return 600  # Increased fallback from 400

def _generate_cash_value_projections(monthly_contribution: int, duration_years: int) -> List[Dict[str, Any]]:
    """Generates cash value projections for IUL based on monthly contribution and duration."""
    try:
        projections = []
        cash_value = 0
        illustrated_rate = 0.06  # 6% annual growth
        year1_allocation = 0.85  # 85% of premium goes to cash value in year 1
        year2plus_allocation = 0.95  # 95% of premium goes to cash value in subsequent years
        
        for year in range(1, duration_years + 1):
            if year == 1:
                cash_value += monthly_contribution * 12 * year1_allocation
            else:
                cash_value = cash_value * (1 + illustrated_rate) + monthly_contribution * 12 * year2plus_allocation
            
            projections.append({
                "year": year,
                "value": round(cash_value / 100) * 100  # Round to nearest $100
            })
        
        return projections
        
    except Exception as e:
        print(f"Error generating cash value projections: {e}")
        return []

def _calculate_mec_limit(age: int, monthly_income: float, total_need: float) -> int:
    """Calculate MEC (Modified Endowment Contract) limit based on client profile"""
    try:
        # Base MEC calculation: IRS guidelines for life insurance
        # Generally 7-pay test: premium limit that keeps policy from becoming MEC
        base_mec = monthly_income * 0.25  # 25% of monthly income as base
        
        # Adjust based on age (younger clients can contribute more)
        if age < 35:
            age_multiplier = 1.4
        elif age < 45:
            age_multiplier = 1.2
        elif age < 55:
            age_multiplier = 1.0
        else:
            age_multiplier = 0.8
        
        # Adjust based on total need (higher need = higher MEC limit)
        if total_need > 3000000:  # Very high need
            need_multiplier = 1.5
        elif total_need > 2000000:  # High need
            need_multiplier = 1.3
        elif total_need > 1000000:  # Medium need
            need_multiplier = 1.1
        else:
            need_multiplier = 1.0
        
        # Calculate final MEC limit
        mec_limit = base_mec * age_multiplier * need_multiplier
        
        # Round to nearest $100 and apply reasonable bounds
        mec_limit = round(mec_limit / 100) * 100
        mec_limit = max(500, min(mec_limit, 5000))  # $500-$5000 range
        
        return int(mec_limit)
        
    except Exception as e:
        print(f"Error calculating MEC limit: {e}")
        return 2000  # Fallback to default

# Legacy parsing functions (fallback for Phase 1)
async def legacy_analyze_portfolio_file(file_content: bytes, file_name: str, file_type: str) -> Dict[str, Any]:
    """Legacy portfolio file analysis using existing parsing logic"""
    try:
        # Parse CSV structure
        csv_data = parse_csv_structure(file_content, file_name)
        if not csv_data:
            return {"error": "Failed to parse CSV file"}
        
        print(f"Legacy parsing: Found {len(csv_data['rows'])} rows with record types: {csv_data['record_types']}")
        
        # Extract data using existing functions
        household_profile = await legacy_extract_household_profile(csv_data)
        financial_summary = await legacy_extract_financial_summary(csv_data)
        asset_allocation = await legacy_extract_asset_allocation(csv_data)
        account_breakdown = await legacy_extract_account_breakdown(csv_data)
        insurance_liability = await legacy_extract_insurance_liability_data(csv_data)
        financial_goals = await legacy_extract_financial_goals(csv_data)
        additional_fields = await legacy_extract_additional_fields(csv_data)
        
        # Combine extracted data
        combined_data = {
            "household_profile": household_profile,
            "financial_summary": financial_summary,
            "asset_allocation": asset_allocation,
            "account_breakdown": account_breakdown,
            "current_insurance": insurance_liability["current_insurance"],
            "liabilities_detail": insurance_liability["liabilities_detail"],
            "financial_goals": financial_goals,
            "additional_fields": additional_fields
        }
        
        return {
            "success": True,
            "data": combined_data,
            "processing_status": "extraction_complete",
            "ai_analysis_ready": True
        }
        
    except Exception as e:
        print(f"Legacy analysis failed: {e}")
        return {"error": f"Legacy analysis failed: {str(e)}"}

async def legacy_extract_household_profile(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy household profile extraction"""
    try:
        # Direct extraction from CSV data
        household_data = create_default_household_profile()
        
        # The first row contains household data
        if len(csv_data["rows"]) > 0:
            row = csv_data["rows"][0]  # First data row
            headers = csv_data["headers"]
            
            # Map CSV columns to our fields
            if len(headers) > 0 and len(row) > 0:
                try:
                    # Look for specific columns
                    for i, header in enumerate(headers):
                        if "marital_status" in header.lower() and i < len(row):
                            household_data["marital_status"] = row[i] if row[i] else "Unknown"
                        elif "dependents_count" in header.lower() and i < len(row):
                            try:
                                household_data["dependents_count"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["dependents_count"] = 0
                        elif "dependents_ages" in header.lower() and i < len(row):
                            household_data["dependents_ages"] = row[i] if row[i] else ""
                        elif "risk_tolerance" in header.lower() and i < len(row):
                            household_data["risk_tolerance"] = row[i] if row[i] else "Unknown"
                        elif "time_horizon_years" in header.lower() and i < len(row):
                            try:
                                household_data["time_horizon_years"] = float(row[i]) if row[i] else 20
                            except:
                                household_data["time_horizon_years"] = 20
                        elif "income_w2_annual" in header.lower() and i < len(row):
                            try:
                                household_data["income_w2_annual"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["income_w2_annual"] = 0
                        elif "income_1099_annual" in header.lower() and i < len(row):
                            try:
                                household_data["income_1099_annual"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["income_1099_annual"] = 0
                        elif "spouse_income_annual" in header.lower() and i < len(row):
                            try:
                                household_data["spouse_income_annual"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["spouse_income_annual"] = 0
                        elif "other_income_annual" in header.lower() and i < len(row):
                            try:
                                household_data["other_income_annual"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["other_income_annual"] = 0
                        elif "monthly_expenses_fixed" in header.lower() and i < len(row):
                            try:
                                household_data["monthly_expenses_fixed"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["monthly_expenses_fixed"] = 0
                        elif "monthly_expenses_variable" in header.lower() and i < len(row):
                            try:
                                household_data["monthly_expenses_variable"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["monthly_expenses_variable"] = 0
                        elif "savings_rate_pct" in header.lower() and i < len(row):
                            try:
                                household_data["savings_rate_pct"] = float(row[i]) if row[i] else 0
                            except:
                                household_data["savings_rate_pct"] = 0
                        elif "emergency_fund_target_months" in header.lower() and i < len(row):
                            try:
                                household_data["emergency_fund_target_months"] = float(row[i]) if row[i] else 6
                            except:
                                household_data["emergency_fund_target_months"] = 6
                except Exception as e:
                    print(f"Error parsing household data: {e}")
        
        # Calculate age from DOB if available
        try:
            for i, header in enumerate(headers):
                if "dob" in header.lower() and i < len(row):
                    dob_str = row[i]
                    if dob_str:
                        # Simple age calculation (approximate)
                        import datetime
                        try:
                            dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d")
                            today = datetime.datetime.now()
                            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                            household_data["client_age"] = max(18, min(85, age))
                        except:
                            household_data["client_age"] = 35
                    break
        except Exception as e:
            print(f"Error calculating age: {e}")
            household_data["client_age"] = 35
        
        return household_data
        
    except Exception as e:
        print(f"Household extraction failed: {e}")
        return create_default_household_profile()

async def legacy_extract_financial_summary(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy financial summary extraction"""
    try:
        # Direct extraction from CSV data
        financial_data = create_default_financial_summary()
        
        # Calculate portfolio value from position rows
        total_portfolio = 0
        total_liabilities = 0
        
        for row in csv_data["rows"]:
            if len(row) > 0:
                if len(row) > 55 and row[55] == "Position":  # Column 55 contains record types
                    # Look for market value at position 85
                    if len(row) > 85:
                        try:
                            value = float(row[85]) if row[85] else 0
                            total_portfolio += value
                        except:
                            pass
                elif len(row) > 55 and row[55] == "Liability":  # Column 55 contains record types
                    # Look for liability amounts
                    for i, header in enumerate(csv_data["headers"]):
                        if any(keyword in header.lower() for keyword in ["balance", "amount", "debt"]):
                            try:
                                value = float(row[i]) if row[i] else 0
                                total_liabilities += value
                            except:
                                pass
        
        financial_data["total_portfolio_value"] = total_portfolio
        financial_data["total_liabilities"] = total_liabilities
        financial_data["total_net_worth"] = total_portfolio - total_liabilities
        
        # Extract income and expenses from household data
        for row in csv_data["rows"]:
            if len(row) > 0 and len(row) > 55 and row[55] in ["Household", "Profile"]:
                headers = csv_data["headers"]
                for i, header in enumerate(headers):
                    if "income_w2_annual" in header.lower() and i < len(row):
                        try:
                            income = float(row[i]) if row[i] else 0
                            financial_data["monthly_income_total"] += income / 12
                        except:
                            pass
                    elif "monthly_expenses_fixed" in header.lower() and i < len(row):
                        try:
                            financial_data["monthly_expenses_total"] += float(row[i]) if row[i] else 0
                        except:
                            pass
                    elif "monthly_expenses_variable" in header.lower() and i < len(row):
                        try:
                            financial_data["monthly_expenses_total"] += float(row[i]) if row[i] else 0
                        except:
                            pass
        
        return financial_data
        
    except Exception as e:
        print(f"Financial summary extraction failed: {e}")
        return create_default_financial_summary()

async def legacy_extract_asset_allocation(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy asset allocation extraction"""
    try:
        # Direct extraction from CSV data
        asset_data = create_default_asset_allocation()
        
        # Calculate asset allocation from position rows
        for row in csv_data["rows"]:
            if len(row) > 55 and row[55] == "Position":  # Column 55 contains record types
                market_value = 0
                asset_class = ""
                
                # Get market value and asset class from correct columns
                # Based on CSV structure: asset_class at position 80, market_value at position 85
                if len(row) > 85:
                    try:
                        market_value = float(row[85]) if row[85] else 0
                    except:
                        market_value = 0
                if len(row) > 80:
                    asset_class = row[80].lower() if row[80] else ""
                
                # Classify assets
                if market_value > 0:
                    if "equity" in asset_class or "stock" in asset_class or "fund" in asset_class:
                        asset_data["equity"] += market_value
                    elif "bond" in asset_class or "fixed" in asset_class:
                        asset_data["fixed_income"] += market_value
                    elif "real" in asset_class or "property" in asset_class:
                        asset_data["real_estate"] += market_value
                    elif "cash" in asset_class:
                        asset_data["cash"] += market_value
                    elif "crypto" in asset_class or "alternative" in asset_class:
                        asset_data["alternative_investments"] += market_value
                    else:
                        # Default to equity if unclear
                        asset_data["equity"] += market_value
        
        return asset_data
        
    except Exception as e:
        print(f"Asset allocation extraction failed: {e}")
        return create_default_asset_allocation()

async def legacy_extract_account_breakdown(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy account breakdown extraction"""
    try:
        # For now, return default values
        # This can be enhanced later
        return create_default_account_breakdown()
    except Exception as e:
        print(f"Account breakdown extraction failed: {e}")
        return create_default_account_breakdown()

async def legacy_extract_insurance_liability_data(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy insurance and liability extraction"""
    try:
        # For now, return default values
        # This can be enhanced later
        return {
            "current_insurance": create_default_insurance_data(),
            "liabilities_detail": create_default_liability_data()
        }
    except Exception as e:
        print(f"Insurance/liability extraction failed: {e}")
        return {
            "current_insurance": create_default_insurance_data(),
            "liabilities_detail": create_default_liability_data()
        }

async def legacy_extract_financial_goals(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy financial goals extraction"""
    try:
        # For now, return default values
        # This can be enhanced later
        return create_default_financial_goals()
    except Exception as e:
        print(f"Financial goals extraction failed: {e}")
        return create_default_financial_goals()

async def legacy_extract_additional_fields(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy additional fields extraction"""
    try:
        # For now, return default values
        # This can be enhanced later
        return create_default_additional_fields()
    except Exception as e:
        print(f"Additional fields extraction failed: {e}")
        return create_default_additional_fields()

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint showing system status"""
    return {
        "status": "ok",
        "phase1_ready": enhanced_parser is not None,
        "phase2_ready": portfolio_analyzer is not None,
        "system": "Two-Phase Portfolio Analysis API"
    } 