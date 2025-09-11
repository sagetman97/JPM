import os
import json
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('PORT', os.getenv('API_PORT', 8000)))
# CORS configuration - support multiple environments
default_origins = 'https://roboadvisor-mu.vercel.app,http://localhost:3000'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', default_origins).split(',')

app = FastAPI(title="Everly x JPMorgan RoboAdvisor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Import and include API routes
from api import router as api_router
app.include_router(api_router, prefix="/api")

# In-memory storage for PDF data (in production, use Redis or database)
pdf_data_store = {}

# In-memory storage for comprehensive report data for chatbot context
report_context_store = {}

@app.post("/api/pdf/portfolio-data")
async def store_portfolio_pdf_data(data: dict):
    """Store portfolio analysis data for PDF generation"""
    try:
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Store data with timestamp
        pdf_data_store[session_id] = {
            "data": data,
            "timestamp": time.time(),
            "type": "portfolio"
        }
        
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/portfolio-data/{session_id}")
async def get_portfolio_pdf_data(session_id: str):
    """Get portfolio analysis data for PDF generation"""
    try:
        if session_id not in pdf_data_store:
            raise HTTPException(status_code=404, detail="Session not found")
        
        stored_data = pdf_data_store[session_id]
        
        # Check if data is too old (1 hour)
        if time.time() - stored_data["timestamp"] > 3600:
            del pdf_data_store[session_id]
            raise HTTPException(status_code=404, detail="Session expired")
        
        return stored_data["data"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report-context/portfolio")
async def store_portfolio_report_context(data: dict):
    """Store comprehensive portfolio report data for chatbot context"""
    try:
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Extract and structure the comprehensive report data
        report_data = {
            "session_id": session_id,
            "timestamp": time.time(),
            "type": "portfolio",
            "form_data": data.get("formData", {}),
            "analysis_result": data.get("result", {}),
            "summary": {
                "total_assets": data.get("result", {}).get("total_assets", 0),
                "risk_level": data.get("result", {}).get("portfolio_metrics", {}).get("risk_level", "N/A"),
                "life_insurance_need": data.get("result", {}).get("life_insurance_needs", {}).get("total_need", 0),
                "current_life_insurance": data.get("result", {}).get("individual_life", 0) + data.get("result", {}).get("group_life", 0),
                "coverage_gap": data.get("result", {}).get("gap", 0),
                "product_recommendation": data.get("result", {}).get("product_recommendation", "N/A"),
                "portfolio_health_score": data.get("result", {}).get("portfolio_metrics", {}).get("portfolio_health_score", 0),
                "recommended_coverage": data.get("result", {}).get("recommended_coverage", 0),
                "rationale": data.get("result", {}).get("rationale", ""),
                "cash_value_projection": data.get("result", {}).get("cash_value_projection", []),
                "asset_allocation": data.get("result", {}).get("asset_allocation", {}),
                "asset_allocation_dollars": {
                    "equity": data.get("result", {}).get("equity", 0),
                    "fixed_income": data.get("result", {}).get("fixed_income", 0),
                    "real_estate": data.get("result", {}).get("real_estate", 0),
                    "cash": data.get("result", {}).get("cash", 0),
                    "alternative_investments": data.get("result", {}).get("alternative_investments", 0)
                },
                "asset_allocation_percentages": data.get("result", {}).get("asset_allocation", {}),
                "key_findings": data.get("result", {}).get("key_findings", []),
                "risk_analysis": data.get("result", {}).get("risk_analysis", []),
                "opportunities": data.get("result", {}).get("opportunities", []),
                "recommendations": data.get("result", {}).get("recommendations", []),
                "life_insurance_needs_breakdown": data.get("result", {}).get("life_insurance_needs", {}),
                "portfolio_metrics": data.get("result", {}).get("portfolio_metrics", {}),
                "projection_parameters": data.get("result", {}).get("projection_parameters", {}),
                "recommended_monthly_savings": data.get("result", {}).get("recommended_monthly_savings", 0),
                "max_monthly_contribution": data.get("result", {}).get("max_monthly_contribution", 0)
            },
            "raw_data": data  # Store the complete raw data for reference
        }
        
        # Store in report context store
        report_context_store[session_id] = report_data
        
        return {"status": "success", "session_id": session_id, "message": "Report context stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report-context/assessment")
async def store_assessment_report_context(data: dict):
    """Store comprehensive assessment report data for chatbot context"""
    try:
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Extract and structure the comprehensive report data
        report_data = {
            "session_id": session_id,
            "timestamp": time.time(),
            "type": "assessment",
            "form_data": data.get("formData", {}),
            "analysis_result": data.get("result", {}),
            "summary": {
                "recommended_coverage": data.get("result", {}).get("recommended_coverage", 0),
                "current_coverage": data.get("result", {}).get("individual_life", 0) + data.get("result", {}).get("group_life", 0),
                "coverage_gap": data.get("result", {}).get("gap", 0),
                "product_recommendation": data.get("result", {}).get("product_recommendation", "N/A"),
                "rationale": data.get("result", {}).get("rationale", ""),
                "duration_years": data.get("result", {}).get("duration_years", 0),
                "life_insurance_needs": data.get("result", {}).get("life_insurance_needs", {}),
                "client_profile": {
                    "age": data.get("formData", {}).get("age", 0),
                    "marital_status": data.get("formData", {}).get("marital_status", ""),
                    "dependents": data.get("formData", {}).get("dependents", 0),
                    "monthly_income": data.get("formData", {}).get("monthly_income", 0),
                    "monthly_expenses": data.get("formData", {}).get("monthly_expenses", 0)
                },
                "coverage_goals": data.get("formData", {}).get("coverage_goals", []),
                "education_funding": data.get("formData", {}).get("provide_education", False),
                "cash_value_importance": data.get("formData", {}).get("cash_value_importance", ""),
                "permanent_coverage": data.get("formData", {}).get("permanent_coverage", ""),
                "income_replacement_years": data.get("formData", {}).get("income_replacement_years", 10)
            },
            "raw_data": data  # Store the complete raw data for reference
        }
        
        # Store in report context store
        report_context_store[session_id] = report_data
        
        return {"status": "success", "session_id": session_id, "message": "Assessment report context stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report-context/portfolio/{session_id}")
async def get_portfolio_report_context(session_id: str):
    """Get comprehensive portfolio report data for chatbot context"""
    try:
        if session_id not in report_context_store:
            raise HTTPException(status_code=404, detail="Report context not found")
        
        stored_data = report_context_store[session_id]
        
        # Check if data is too old (24 hours for report context)
        if time.time() - stored_data["timestamp"] > 86400:
            del report_context_store[session_id]
            raise HTTPException(status_code=404, detail="Report context expired")
        
        return stored_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report-context/session/{chat_session_id}")
async def get_session_report_contexts(chat_session_id: str):
    """Get all report contexts for a chat session"""
    try:
        # Find all report contexts that might be related to this chat session
        # This is a simple implementation - in production, you'd have better session linking
        related_contexts = []
        
        for session_id, context_data in report_context_store.items():
            # Check if this might be related to the chat session
            # In a real implementation, you'd have better session linking
            if chat_session_id in session_id or session_id in chat_session_id:
                related_contexts.append(context_data)
        
        return {
            "chat_session_id": chat_session_id,
            "report_contexts": related_contexts,
            "count": len(related_contexts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio-assessment/pdf/{session_id}", response_class=HTMLResponse)
async def portfolio_pdf_page(session_id: str):
    """Render portfolio assessment results as static HTML for PDF generation"""
    try:
        # Get the stored data
        data_response = await get_portfolio_pdf_data(session_id)
        portfolio_data = data_response
        
        # Generate static HTML with the results
        html_content = generate_portfolio_pdf_html(portfolio_data)
        return HTMLResponse(content=html_content)
        
    except HTTPException as e:
        return HTMLResponse(content=f"<h1>Error: {e.detail}</h1>", status_code=e.status_code)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>", status_code=500)

@app.get("/assessment/pdf/{session_id}", response_class=HTMLResponse)
async def assessment_pdf_page(session_id: str):
    """Render assessment results as static HTML for PDF generation"""
    try:
        # Get the stored data from report context
        if session_id not in report_context_store:
            return HTMLResponse(content="<h1>Assessment data not found</h1>", status_code=404)
        
        stored_data = report_context_store[session_id]
        
        # Check if data is too old (24 hours)
        if time.time() - stored_data["timestamp"] > 86400:
            del report_context_store[session_id]
            return HTMLResponse(content="<h1>Assessment data expired</h1>", status_code=410)
        
        # Generate static HTML with the results
        html_content = generate_assessment_pdf_html(stored_data)
        return HTMLResponse(content=html_content)
        
    except HTTPException as e:
        return HTMLResponse(content=f"<h1>Error: {e.detail}</h1>", status_code=e.status_code)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>", status_code=500)

def generate_portfolio_pdf_html(data: dict) -> str:
    """Generate static HTML for portfolio assessment PDF"""
    
    # Extract data with defaults
    result = data.get("result_data", {})
    analysis = data.get("analysis", {})
    
    # Basic info
    client_name = result.get("client_name", "Client")
    total_assets = result.get("total_assets", 0)
    net_worth = result.get("total_net_worth", 0)
    
    # Coverage needs
    needs_breakdown = result.get("needs_breakdown", {})
    recommended_coverage = result.get("recommended_coverage", 0)
    gap = result.get("gap", 0)
    
    # Portfolio metrics
    portfolio_health_score = result.get("portfolio_health_score", 0)
    risk_level = result.get("risk_level", "Unknown")
    
    # Cash value projection
    cash_value_projection = result.get("cash_value_projection", [])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portfolio Analysis Report - {client_name}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f8f9fa;
            }}
            .header {{
                background: #1B365D;
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .section {{
                background: white;
                padding: 25px;
                margin-bottom: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #1B365D;
                border-bottom: 3px solid #1B365D;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }}
            .metric-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #1B365D;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #1B365D;
            }}
            .metric-label {{
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }}
            .coverage-breakdown {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }}
            .coverage-item {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
            .coverage-amount {{
                font-size: 1.5em;
                font-weight: bold;
                color: #1976d2;
            }}
            .chart-placeholder {{
                background: #f5f5f5;
                border: 2px dashed #ccc;
                padding: 40px;
                text-align: center;
                border-radius: 8px;
                color: #666;
            }}
            .recommendations {{
                background: #e8f5e8;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #4caf50;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Portfolio Analysis Report</h1>
            <p>Comprehensive Financial Assessment for {client_name}</p>
        </div>

        <div class="section">
            <h2>📊 Portfolio Overview</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${total_assets:,.0f}</div>
                    <div class="metric-label">Total Assets</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${net_worth:,.0f}</div>
                    <div class="metric-label">Net Worth</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{portfolio_health_score}/100</div>
                    <div class="metric-label">Portfolio Health Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{risk_level}</div>
                    <div class="metric-label">Risk Level</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🛡️ Life Insurance Needs Analysis</h2>
            <div class="coverage-breakdown">
                <div class="coverage-item">
                    <div class="coverage-amount">${needs_breakdown.get('income_replacement', 0):,.0f}</div>
                    <div class="metric-label">Income Replacement</div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-amount">${needs_breakdown.get('debt_payoff', 0):,.0f}</div>
                    <div class="metric-label">Debt Payoff</div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-amount">${needs_breakdown.get('education', 0):,.0f}</div>
                    <div class="metric-label">Education Funding</div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-amount">${needs_breakdown.get('funeral', 0):,.0f}</div>
                    <div class="metric-label">Final Expenses</div>
                </div>
            </div>
            
            <div style="margin-top: 30px; text-align: center;">
                <div class="metric-card" style="display: inline-block; min-width: 300px;">
                    <div class="metric-value">${recommended_coverage:,.0f}</div>
                    <div class="metric-label">Recommended Coverage</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Cash Value Projection</h2>
            <div class="chart-placeholder">
                <h3>40-Year Cash Value Growth Projection</h3>
                <p>Projected final value: ${cash_value_projection[-1].get('value', 0):,.0f} if available</p>
                <p>This chart would show the growth of cash value over time</p>
            </div>
        </div>

        <div class="section">
            <h2>💡 Key Recommendations</h2>
            <div class="recommendations">
                <p><strong>Portfolio Health:</strong> Your portfolio health score of {portfolio_health_score}/100 indicates {'excellent' if portfolio_health_score >= 80 else 'good' if portfolio_health_score >= 60 else 'needs improvement'} overall financial health.</p>
                <p><strong>Life Insurance Gap:</strong> You have a coverage gap of ${gap:,.0f}. Consider increasing your life insurance coverage to better protect your family.</p>
                <p><strong>Risk Management:</strong> Your current risk level is {risk_level}. Ensure your portfolio aligns with your risk tolerance and financial goals.</p>
            </div>
        </div>

        <div class="footer">
            <p>Generated on {time.strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>This report is for informational purposes only and should not be considered as financial advice.</p>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_assessment_pdf_html(data: dict) -> str:
    """Generate static HTML for assessment PDF"""
    
    # Extract data with defaults
    result = data.get("analysis_result", {})
    form_data = data.get("form_data", {})
    summary = data.get("summary", {})
    
    # Basic info
    client_name = form_data.get("client_name", "Client")
    age = form_data.get("age", 0)
    marital_status = form_data.get("marital_status", "")
    dependents = form_data.get("dependents", 0)
    
    # Coverage needs
    recommended_coverage = result.get("recommended_coverage", 0)
    current_coverage = result.get("individual_life", 0) + result.get("group_life", 0)
    gap = result.get("gap", 0)
    product_recommendation = result.get("product_recommendation", "N/A")
    rationale = result.get("rationale", "")
    duration_years = result.get("duration_years", 0)
    
    # Life insurance needs breakdown
    life_insurance_needs = result.get("life_insurance_needs", {})
    income_replacement = life_insurance_needs.get("income_replacement", 0)
    debt_payoff = life_insurance_needs.get("debt_payoff", 0)
    education_funding = life_insurance_needs.get("education_funding", 0)
    funeral_expenses = life_insurance_needs.get("funeral_expenses", 0)
    legacy_amount = life_insurance_needs.get("legacy_amount", 0)
    special_needs = life_insurance_needs.get("special_needs", 0)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Life Insurance Assessment Report - {client_name}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f8f9fa;
            }}
            .header {{
                background: #1B365D;
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .section {{
                background: white;
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #1B365D;
                margin-top: 0;
                font-size: 1.8em;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 10px;
            }}
            .coverage-summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .coverage-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #1B365D;
            }}
            .coverage-card h3 {{
                margin: 0 0 10px 0;
                color: #1B365D;
                font-size: 1.1em;
            }}
            .coverage-card .amount {{
                font-size: 2em;
                font-weight: bold;
                color: #28a745;
            }}
            .needs-breakdown {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .need-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
            .need-item h4 {{
                margin: 0 0 8px 0;
                color: #1B365D;
                font-size: 0.9em;
            }}
            .need-item .amount {{
                font-size: 1.3em;
                font-weight: bold;
                color: #495057;
            }}
            .client-profile {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .profile-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
            }}
            .profile-item h4 {{
                margin: 0 0 8px 0;
                color: #1B365D;
                font-size: 0.9em;
            }}
            .profile-item .value {{
                font-size: 1.2em;
                font-weight: bold;
                color: #495057;
            }}
            .recommendation {{
                background: #e8f5e8;
                border: 1px solid #28a745;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            .recommendation h3 {{
                margin: 0 0 15px 0;
                color: #28a745;
            }}
            .rationale {{
                font-style: italic;
                color: #6c757d;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Life Insurance Assessment Report</h1>
            <p>Comprehensive Coverage Analysis for {client_name}</p>
        </div>
        
        <div class="section">
            <h2>Coverage Summary</h2>
            <div class="coverage-summary">
                <div class="coverage-card">
                    <h3>Recommended Coverage</h3>
                    <div class="amount">${recommended_coverage:,.0f}</div>
                </div>
                <div class="coverage-card">
                    <h3>Current Coverage</h3>
                    <div class="amount">${current_coverage:,.0f}</div>
                </div>
                <div class="coverage-card">
                    <h3>Coverage Gap</h3>
                    <div class="amount">${gap:,.0f}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Coverage Needs Breakdown</h2>
            <div class="needs-breakdown">
                <div class="need-item">
                    <h4>Income Replacement</h4>
                    <div class="amount">${income_replacement:,.0f}</div>
                </div>
                <div class="need-item">
                    <h4>Debt Payoff</h4>
                    <div class="amount">${debt_payoff:,.0f}</div>
                </div>
                <div class="need-item">
                    <h4>Education Funding</h4>
                    <div class="amount">${education_funding:,.0f}</div>
                </div>
                <div class="need-item">
                    <h4>Funeral Expenses</h4>
                    <div class="amount">${funeral_expenses:,.0f}</div>
                </div>
                <div class="need-item">
                    <h4>Legacy Amount</h4>
                    <div class="amount">${legacy_amount:,.0f}</div>
                </div>
                <div class="need-item">
                    <h4>Special Needs</h4>
                    <div class="amount">${special_needs:,.0f}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Client Profile</h2>
            <div class="client-profile">
                <div class="profile-item">
                    <h4>Age</h4>
                    <div class="value">{age} years</div>
                </div>
                <div class="profile-item">
                    <h4>Marital Status</h4>
                    <div class="value">{marital_status}</div>
                </div>
                <div class="profile-item">
                    <h4>Dependents</h4>
                    <div class="value">{dependents}</div>
                </div>
                <div class="profile-item">
                    <h4>Monthly Income</h4>
                    <div class="value">${form_data.get('monthly_income', 0):,.0f}</div>
                </div>
                <div class="profile-item">
                    <h4>Monthly Expenses</h4>
                    <div class="value">${form_data.get('monthly_expenses', 0):,.0f}</div>
                </div>
                <div class="profile-item">
                    <h4>Coverage Goals</h4>
                    <div class="value">{', '.join(form_data.get('coverage_goals', []))}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Product Recommendation</h2>
            <div class="recommendation">
                <h3>{product_recommendation}</h3>
                <p><strong>Duration:</strong> {duration_years} years</p>
                <div class="rationale">
                    <strong>Rationale:</strong> {rationale}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# Note: Chatbot functionality moved to separate VM/env
# This VM focuses on portfolio analysis, client assessment, and quick calculator

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True) 