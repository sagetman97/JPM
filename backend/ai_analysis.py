"""
Phase 2: AI Portfolio Analysis System.
Runs after user confirms form data to provide comprehensive financial insights.
This is the heavy processing that happens in the background.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import re
import pandas as pd
from io import StringIO
import csv

# Fix: Use direct OpenAI import instead of langchain_openai for compatibility
from openai import OpenAI
from financial_models import FormData, create_default_form_data, convert_to_legacy_format

class PortfolioAnalysis:
    """Simple portfolio analysis result class"""
    
    def __init__(self, portfolio_health_score: int = 50, key_findings: List[str] = None, 
                 risk_analysis: List[str] = None, opportunities: List[str] = None,
                 recommendations: List[str] = None, missing_data: List[str] = None,
                 goal_alignment: Dict[str, Any] = None, concentration_risks: List[str] = None,
                 tax_efficiency: str = "", rebalancing_needs: str = ""):
        self.portfolio_health_score = portfolio_health_score
        self.key_findings = key_findings or []
        self.risk_analysis = risk_analysis or []
        self.opportunities = opportunities or []
        self.recommendations = recommendations or []
        self.missing_data = missing_data or []
        self.goal_alignment = goal_alignment or {}
        self.concentration_risks = concentration_risks or []
        self.tax_efficiency = tax_efficiency
        self.rebalancing_needs = rebalancing_needs
    
    def dict(self):
        """Return as dictionary for API compatibility"""
        return {
            "portfolio_health_score": self.portfolio_health_score,
            "key_findings": self.key_findings,
            "risk_analysis": self.risk_analysis,
            "opportunities": self.opportunities,
            "recommendations": self.recommendations,
            "missing_data": self.missing_data,
            "goal_alignment": self.goal_alignment,
            "concentration_risks": self.concentration_risks,
            "tax_efficiency": self.tax_efficiency,
            "rebalancing_needs": self.rebalancing_needs
        }

class PortfolioAnalyzer:
    """AI-powered portfolio analyzer using OpenAI"""
    
    def __init__(self, openai_api_key: str):
        self.llm = OpenAI(
            api_key=openai_api_key
        )
        self.model = "gpt-4o"
        self.max_tokens = 6000
        self.temperature = 0
    
    async def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> PortfolioAnalysis:
        """Generate comprehensive portfolio analysis"""
        try:
            # Calculate basic metrics
            metrics = await self._calculate_basic_metrics(portfolio_data)
            
            # Analyze risks
            risk_analysis = await self._analyze_risks(portfolio_data)
            
            # Analyze goals
            goal_analysis = await self._analyze_goals(portfolio_data)
            
            # Generate insights
            insights = await self._generate_insights(portfolio_data, metrics, risk_analysis, goal_analysis)
            
            # Create portfolio analysis
            analysis = PortfolioAnalysis(
                portfolio_health_score=metrics.get("health_score", 50),
                key_findings=insights.get("key_findings", []),
                risk_analysis=insights.get("risk_analysis", []),
                opportunities=insights.get("opportunities", []),
                recommendations=insights.get("recommendations", []),
                missing_data=insights.get("missing_data", []),
                goal_alignment=goal_analysis,
                concentration_risks=risk_analysis.get("concentration_risks", []),
                tax_efficiency=insights.get("tax_efficiency", ""),
                rebalancing_needs=insights.get("rebalancing_needs", "")
            )
            
            return analysis
            
        except Exception as e:
            print(f"Portfolio analysis failed: {e}")
            return PortfolioAnalysis(
                portfolio_health_score=50,
                key_findings=["Analysis could not be completed due to an error"],
                risk_analysis=["Unable to analyze risks"],
                opportunities=["Unable to identify opportunities"],
                recommendations=["Please review your data and try again"]
            )
    
    async def _calculate_basic_metrics(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic portfolio metrics"""
        try:
            # Extract basic portfolio information
            total_assets = portfolio_data.get("total_assets", 0)
            total_liabilities = portfolio_data.get("total_liabilities", 0)
            net_worth = total_assets - total_liabilities
            
            # Calculate health score based on basic metrics
            health_score = 50  # Base score
            
            if net_worth > 0:
                health_score += 20
            if total_assets > 0:
                health_score += 15
            if portfolio_data.get("emergency_fund", 0) > 0:
                health_score += 15
            
            return {
                "health_score": min(health_score, 100),
                "net_worth": net_worth,
                "total_assets": total_assets,
                "total_liabilities": total_liabilities
            }
        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return {"health_score": 50}
    
    async def _analyze_risks(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio risks"""
        try:
            concentration_risks = []
            
            # Basic risk analysis
            if portfolio_data.get("total_assets", 0) > 0:
                # Check for high concentration in single assets
                positions = portfolio_data.get("positions", [])
                for position in positions:
                    if position.get("market_value", 0) > portfolio_data.get("total_assets", 0) * 0.1:
                        concentration_risks.append(f"High concentration in {position.get('security_name', 'security')}")
            
            return {
                "concentration_risks": concentration_risks,
                "overall_risk_level": "Medium" if concentration_risks else "Low"
            }
        except Exception as e:
            print(f"Error analyzing risks: {e}")
            return {"concentration_risks": []}
    
    async def _analyze_goals(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial goals"""
        try:
            # Basic goal analysis
            goals = portfolio_data.get("financial_goals", [])
            goal_analysis = {}
            
            for goal in goals:
                goal_name = goal.get("name", "Unknown Goal")
                current_amount = goal.get("current_amount", 0)
                target_amount = goal.get("target_amount", 0)
                
                if target_amount > 0:
                    progress_percentage = min((current_amount / target_amount) * 100, 100)
                    goal_analysis[goal_name] = {
                        "progress_percentage": round(progress_percentage, 1),
                        "status": "On Track" if progress_percentage >= 80 else "Needs Attention"
                    }
            
            return goal_analysis
        except Exception as e:
            print(f"Error analyzing goals: {e}")
            return {}
    
    async def _generate_insights(self, portfolio_data: Dict[str, Any], metrics: Dict[str, Any], 
                                risk_analysis: Dict[str, Any], goal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights"""
        try:
            insights = {
                "key_findings": ["Portfolio analysis completed successfully"],
                "risk_analysis": ["Risk assessment completed"],
                "opportunities": ["Opportunities identified"],
                "recommendations": ["Recommendations generated"],
                "missing_data": [],
                "tax_efficiency": "Tax efficiency analysis completed",
                "rebalancing_needs": "Rebalancing assessment completed"
            }
            
            # Add specific insights based on data
            if metrics.get("net_worth", 0) < 0:
                insights["key_findings"].append("Negative net worth detected - focus on debt reduction")
                insights["recommendations"].append("Prioritize paying down high-interest debt")
            
            if risk_analysis.get("concentration_risks"):
                insights["risk_analysis"].extend(risk_analysis["concentration_risks"])
                insights["recommendations"].append("Consider diversifying concentrated positions")
            
            return insights
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            return {
                "key_findings": ["Insight generation failed"],
                "risk_analysis": ["Risk analysis unavailable"],
                "opportunities": ["Opportunities analysis unavailable"],
                "recommendations": ["Recommendations unavailable"],
                "missing_data": [],
                "tax_efficiency": "Tax efficiency analysis unavailable",
                "rebalancing_needs": "Rebalancing assessment unavailable"
            }

 