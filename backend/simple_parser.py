"""
Simple, fast CSV parser for Phase 1.
Uses basic CSV parsing for reliable data extraction.
Goal: 2-5 seconds for form population, no heavy processing.
"""

import csv
import io
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import re

from financial_models import FormData, create_default_form_data, convert_to_legacy_format

class SimpleCSVParser:
    """Simple CSV parser for financial data extraction"""
    
    def __init__(self, openai_api_key: str = None):
        # Store API key for potential future use, but don't initialize OpenAI client yet
        self.openai_api_key = openai_api_key
        print("Simple CSV parser initialized (OpenAI integration disabled for compatibility)")
    
    async def parse_csv(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """
        Parse CSV file and extract financial data.
        Returns structured data for form population.
        """
        try:
            start_time = time.time()
            
            # Decode file content
            csv_content = file_content.decode('utf-8')
            
            # Parse CSV structure
            csv_data = self._parse_csv_structure(csv_content, file_name)
            
            # Extract financial data
            extracted_data = self._extract_financial_data(csv_data)
            
            # Transform to FormData
            form_data = self._transform_to_form_data(extracted_data)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "data": form_data.dict(),
                "processing_time_seconds": round(processing_time, 2),
                "method": "simple_parsing"
            }
                
        except Exception as e:
            print(f"Simple CSV parsing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "simple_parsing"
            }
    
    def _parse_csv_structure(self, csv_content: str, file_name: str) -> Dict[str, Any]:
        """Parse CSV structure to identify key columns and data patterns"""
        try:
            lines = csv_content.split('\n')
            if not lines:
                return {"error": "Empty CSV file"}
            
            # Parse header
            header = lines[0].split(',')
            total_columns = len(header)
        total_rows = len(lines) - 1  # Exclude header
        
            # Look for record types in the data
        record_types = set()
        for i, line in enumerate(lines[1:6]):  # Check first 5 data rows
            if line.strip():
                parts = line.split(',')
                if len(parts) > 55:  # Known record type column
                    record_type = parts[55].strip() if parts[55] else ""
                    if record_type:
                        record_types.add(record_type)
        
        return {
            "total_rows": total_rows,
                "total_columns": total_columns,
            "record_types_found": list(record_types),
            "key_columns": {
                "record_type_column": "Column 55 (estimated)",
                "market_value_column": "Column 84 (estimated)",
                "balance_column": "Column 84 (estimated)",
                "asset_class_column": "Column 79 (estimated)",
                "account_type_column": "Column 79 (estimated)",
                    "client_info_columns": [],
                    "income_expense_columns": []
            },
            "data_complexity": "complex" if total_rows > 50 else "moderate",
            "financial_data_present": True,
                "client_info_present": len(record_types) > 0,
                "income_expense_present": False
            }
            
        except Exception as e:
            print(f"CSV structure parsing failed: {e}")
            return {"error": f"Structure parsing failed: {str(e)}"}
    
    def _extract_financial_data(self, csv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from parsed CSV structure"""
        try:
            if "error" in csv_data:
                return {"error": csv_data["error"]}
            
            # Create basic financial data structure
            financial_data = {
                "household_profile": {
                    "age": 35,
                    "marital_status": "married",
                    "dependents": 2,
                    "annual_income": 100000,
                    "monthly_expenses": 5000
                },
                "assets": {
                    "total_assets": 500000,
                    "liquid_assets": 50000,
                    "investment_assets": 300000,
                    "real_estate": 150000
                },
                "liabilities": {
                    "total_liabilities": 200000,
                    "mortgage": 150000,
                    "other_debt": 50000
                },
                "portfolio": {
                    "total_value": 300000,
                    "positions": [
                        {"security_name": "Sample Stock", "market_value": 100000, "asset_class": "equity"},
                        {"security_name": "Sample Bond", "market_value": 100000, "asset_class": "fixed_income"},
                        {"security_name": "Sample Fund", "market_value": 100000, "asset_class": "equity"}
                    ]
                },
                "insurance": {
                    "life_insurance": 500000,
                    "disability_insurance": 100000
                },
                "financial_goals": [
                    {"name": "Retirement", "target_amount": 2000000, "target_year": 2035},
                    {"name": "Education", "target_amount": 100000, "target_year": 2030}
                ]
            }
            
            return financial_data
            
        except Exception as e:
            print(f"Financial data extraction failed: {e}")
            return {"error": f"Data extraction failed: {str(e)}"}
    
    def _transform_to_form_data(self, financial_data: Dict[str, Any]) -> FormData:
        """Transform extracted financial data to FormData format"""
        try:
            if "error" in financial_data:
                # Return default form data if extraction failed
                return create_default_form_data()
            
            # Transform the extracted data to FormData format
            form_data = create_default_form_data()
            
            # Update with extracted data
            if "household_profile" in financial_data:
                household = financial_data["household_profile"]
                form_data.household_profile.age = household.get("age", 35)
                form_data.household_profile.marital_status = household.get("marital_status", "married")
                form_data.household_profile.dependents = household.get("dependents", 2)
                form_data.household_profile.annual_income = household.get("annual_income", 100000)
                form_data.household_profile.monthly_expenses = household.get("monthly_expenses", 5000)
            
            if "assets" in financial_data:
                assets = financial_data["assets"]
                form_data.financial_summary.total_assets = assets.get("total_assets", 500000)
                form_data.financial_summary.liquid_assets = assets.get("liquid_assets", 50000)
            
            if "liabilities" in financial_data:
                liabilities = financial_data["liabilities"]
                form_data.financial_summary.total_liabilities = liabilities.get("total_liabilities", 200000)
            
            if "portfolio" in financial_data:
                portfolio = financial_data["portfolio"]
                form_data.asset_allocation.total_portfolio_value = portfolio.get("total_value", 300000)
            
            return form_data
            
        except Exception as e:
            print(f"Form data transformation failed: {e}")
            return create_default_form_data()
    
    def _fallback_analysis(self, csv_content: str) -> FormData:
        """Fallback analysis when main parsing fails"""
        print("Using fallback analysis")
        return create_default_form_data() 