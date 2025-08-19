import logging
import httpx
from typing import Dict, Any, Optional, List
from .schemas import ConversationContext
from .config import config

logger = logging.getLogger(__name__)

class BackendAPIIntegrator:
    """Integrates with existing backend APIs for calculations and analysis"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"  # Backend API base URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def calculate_life_insurance_needs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate life insurance needs using existing backend API"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/life-insurance/calculate",
                json=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Life insurance calculation failed: {response.status_code}")
                return {"error": "Calculation failed", "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"Error calling life insurance API: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    async def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio using existing backend API"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/portfolio/analyze",
                json=portfolio_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Portfolio analysis failed: {response.status_code}")
                return {"error": "Analysis failed", "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"Error calling portfolio API: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    async def process_csv_data(self, csv_data: str) -> Dict[str, Any]:
        """Process CSV data using existing backend API"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/portfolio/process-csv",
                json={"csv_data": csv_data}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"CSV processing failed: {response.status_code}")
                return {"error": "Processing failed", "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"Error calling CSV processing API: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    async def get_client_assessment(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get client assessment using existing backend API"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/client/assess",
                json=client_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Client assessment failed: {response.status_code}")
                return {"error": "Assessment failed", "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"Error calling client assessment API: {e}")
            return {"error": f"API call failed: {str(e)}"}
    
    async def close(self):
        """Close the HTTP client"""
        
        await self.client.aclose()

class LifeInsuranceCalculator:
    """Enhanced life insurance calculator using existing backend APIs"""
    
    def __init__(self, backend_integrator: BackendAPIIntegrator):
        self.backend = backend_integrator
    
    async def calculate_quick_needs(self, age: int, income: float, dependents: int, debt: float, goals: str) -> Dict[str, Any]:
        """Calculate quick insurance needs estimate"""
        
        try:
            # Prepare data for backend API
            calculation_data = {
                "age": age,
                "annual_income": income,
                "dependents": dependents,
                "total_debt": debt,
                "financial_goals": goals,
                "calculation_type": "quick_estimate"
            }
            
            # Call backend API
            result = await self.backend.calculate_life_insurance_needs(calculation_data)
            
            if "error" not in result:
                return {
                    "status": "success",
                    "recommended_coverage": result.get("recommended_coverage", 0),
                    "monthly_premium_estimate": result.get("monthly_premium_estimate", 0),
                    "calculation_method": result.get("calculation_method", "DIME + Income Replacement"),
                    "key_factors": result.get("key_factors", []),
                    "next_steps": result.get("next_steps", [])
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error in quick needs calculation: {e}")
            return {"error": f"Calculation failed: {str(e)}"}
    
    async def calculate_detailed_needs(self, comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed insurance needs using comprehensive data"""
        
        try:
            # Add calculation type
            comprehensive_data["calculation_type"] = "detailed_analysis"
            
            # Call backend API
            result = await self.backend.calculate_life_insurance_needs(comprehensive_data)
            
            if "error" not in result:
                return {
                    "status": "success",
                    "detailed_analysis": result,
                    "recommendations": result.get("recommendations", []),
                    "risk_assessment": result.get("risk_assessment", {}),
                    "product_recommendations": result.get("product_recommendations", [])
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error in detailed needs calculation: {e}")
            return {"error": f"Calculation failed: {str(e)}"}

class PortfolioAnalyzer:
    """Portfolio analyzer using existing backend APIs"""
    
    def __init__(self, backend_integrator: BackendAPIIntegrator):
        self.backend = backend_integrator
    
    async def analyze_portfolio_comprehensive(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive portfolio analysis"""
        
        try:
            # Call backend API
            result = await self.backend.analyze_portfolio(portfolio_data)
            
            if "error" not in result:
                return {
                    "status": "success",
                    "portfolio_analysis": result,
                    "risk_assessment": result.get("risk_assessment", {}),
                    "recommendations": result.get("recommendations", []),
                    "insurance_implications": result.get("insurance_implications", {})
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error in portfolio analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def process_portfolio_csv(self, csv_data: str) -> Dict[str, Any]:
        """Process portfolio CSV data"""
        
        try:
            # Call backend API
            result = await self.backend.process_csv_data(csv_data)
            
            if "error" not in result:
                return {
                    "status": "success",
                    "processed_data": result,
                    "portfolio_summary": result.get("portfolio_summary", {}),
                    "analysis_ready": result.get("analysis_ready", False)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error processing portfolio CSV: {e}")
            return {"error": f"Processing failed: {str(e)}"}

class ClientAssessmentManager:
    """Manages client assessments using existing backend APIs"""
    
    def __init__(self, backend_integrator: BackendAPIIntegrator):
        self.backend = backend_integrator
    
    async def perform_client_assessment(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive client assessment"""
        
        try:
            # Call backend API
            result = await self.backend.get_client_assessment(client_data)
            
            if "error" not in result:
                return {
                    "status": "success",
                    "assessment_results": result,
                    "client_profile": result.get("client_profile", {}),
                    "recommendations": result.get("recommendations", []),
                    "next_steps": result.get("next_steps", [])
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error in client assessment: {e}")
            return {"error": f"Assessment failed: {str(e)}"}
    
    async def generate_assessment_report(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive assessment report"""
        
        try:
            # This would typically call a report generation service
            # For now, we'll format the assessment data
            report = {
                "report_id": f"ASSESS_{assessment_data.get('client_id', 'UNKNOWN')}_{int(datetime.now().timestamp())}",
                "generated_at": datetime.now().isoformat(),
                "client_summary": assessment_data.get("client_profile", {}),
                "assessment_findings": assessment_data.get("assessment_results", {}),
                "recommendations": assessment_data.get("recommendations", []),
                "action_items": assessment_data.get("next_steps", []),
                "report_type": "comprehensive_client_assessment"
            }
            
            return {
                "status": "success",
                "report": report,
                "download_url": f"/reports/{report['report_id']}.pdf"  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Error generating assessment report: {e}")
            return {"error": f"Report generation failed: {str(e)}"}

# Import datetime for report generation
from datetime import datetime 