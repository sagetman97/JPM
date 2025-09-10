"""
PDF generation system for creating reports from tool results.
Generates PDFs from assessment and portfolio analysis results with charts and visual elements.
"""

from typing import Dict, Any, List, Tuple
import uuid
import os
import io
import math
from datetime import datetime
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Wedge
import seaborn as sns
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF

class PDFGenerator:
    """Generates PDF reports from tool results with charts and visual elements"""
    
    def __init__(self):
        self.output_dir = Path("generated_pdfs")
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Color schemes matching frontend
        self.colors = {
            'primary': '#1B365D',
            'secondary': '#3B82F6', 
            'success': '#10B981',
            'warning': '#F59E0B',
            'danger': '#EF4444',
            'info': '#06B6D4',
            'purple': '#8B5CF6'
        }
        
        # Coverage breakdown colors
        self.coverage_colors = {
            'living_expenses': '#1B365D',
            'debts': '#3B82F6',
            'education': '#F59E42',
            'funeral': '#6366F1',
            'legacy': '#10B981',
            'other': '#F43F5E'
        }
    
    def _create_coverage_breakdown_chart(self, breakdown_data: Dict[str, Any]) -> str:
        """Create a pie chart for coverage breakdown"""
        # Filter out zero values
        filtered_data = {k: v for k, v in breakdown_data.items() if v > 0}
        
        if not filtered_data:
            return None
            
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Prepare data
        labels = [k.replace('_', ' ').title() for k in filtered_data.keys()]
        values = list(filtered_data.values())
        colors_list = [self.coverage_colors.get(k, '#cccccc') for k in filtered_data.keys()]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            colors=colors_list,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10}
        )
        
        # Customize
        ax.set_title('Coverage Breakdown', fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels
        for i, (wedge, value) in enumerate(zip(wedges, values)):
            angle = (wedge.theta2 + wedge.theta1) / 2
            x = 0.7 * math.cos(math.radians(angle))
            y = 0.7 * math.sin(math.radians(angle))
            ax.text(x, y, f'${value:,.0f}', ha='center', va='center', fontweight='bold')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_asset_allocation_chart(self, allocation_data: Dict[str, Any]) -> str:
        """Create a pie chart for asset allocation"""
        # Filter out zero values
        filtered_data = {k: v for k, v in allocation_data.items() if v > 0}
        
        if not filtered_data:
            return None
            
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Prepare data
        labels = [k.replace('_', ' ').title() for k in filtered_data.keys()]
        values = list(filtered_data.values())
        colors_list = [self.colors['primary'], self.colors['secondary'], self.colors['success'], 
                      self.colors['warning'], self.colors['danger']]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            colors=colors_list[:len(values)],
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10}
        )
        
        # Customize
        ax.set_title('Asset Allocation', fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels
        for i, (wedge, value) in enumerate(zip(wedges, values)):
            angle = (wedge.theta2 + wedge.theta1) / 2
            x = 0.7 * math.cos(math.radians(angle))
            y = 0.7 * math.sin(math.radians(angle))
            ax.text(x, y, f'${value:,.0f}', ha='center', va='center', fontweight='bold')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_cash_value_projection_chart(self, projection_data: List[Dict[str, Any]]) -> str:
        """Create a line chart for cash value projection"""
        if not projection_data or len(projection_data) == 0:
            return None
            
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data
        years = [d.get('year', 0) for d in projection_data]
        values = [d.get('value', 0) for d in projection_data]
        
        # Create line chart
        ax.plot(years, values, linewidth=3, color=self.colors['primary'], marker='o', markersize=4)
        ax.fill_between(years, values, alpha=0.3, color=self.colors['primary'])
        
        # Customize
        ax.set_title('Cash Value Projection', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Cash Value ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Add value annotations for key years
        key_years = [5, 10, 20, 30, 40]
        for year in key_years:
            if year in years:
                idx = years.index(year)
                ax.annotate(f'${values[idx]:,.0f}', 
                           (year, values[idx]), 
                           textcoords="offset points", 
                           xytext=(0,10), 
                           ha='center',
                           fontsize=9,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_risk_score_gauge(self, risk_score: int, risk_level: str) -> str:
        """Create a gauge chart for risk score"""
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # Gauge parameters
        min_val, max_val = 0, 100
        center = 0
        radius = 1
        
        # Create gauge arc
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta) * radius
        
        # Color based on risk level
        if risk_level.lower() == 'conservative':
            color = self.colors['success']
        elif risk_level.lower() == 'moderate':
            color = self.colors['warning']
        else:
            color = self.colors['danger']
        
        # Draw gauge background
        ax.plot(theta, r, color='lightgray', linewidth=20, alpha=0.3)
        
        # Draw risk score arc
        score_theta = np.linspace(0, np.pi * (risk_score / 100), 50)
        score_r = np.ones_like(score_theta) * radius
        ax.plot(score_theta, score_r, color=color, linewidth=20)
        
        # Add score text
        ax.text(0, 0, f'{risk_score}/100\n{risk_level.title()}', 
                ha='center', va='center', fontsize=16, fontweight='bold')
        
        # Customize
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Risk Score', fontsize=14, fontweight='bold', pad=20)
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
        
    async def generate_assessment_pdf(self, assessment_data: Dict[str, Any], session_id: str) -> str:
        """Generate PDF from assessment results"""
        pdf_id = f"assessment_{session_id}_{uuid.uuid4().hex[:8]}"
        
        # Create actual PDF file
        pdf_path = self.output_dir / f"{pdf_id}.pdf"
        self._create_assessment_pdf_file(assessment_data, pdf_path)
        
        return pdf_id
    
    async def generate_portfolio_pdf(self, portfolio_data: Dict[str, Any], session_id: str) -> str:
        """Generate PDF from portfolio analysis results"""
        pdf_id = f"portfolio_{session_id}_{uuid.uuid4().hex[:8]}"
        
        # Create actual PDF file
        pdf_path = self.output_dir / f"{pdf_id}.pdf"
        self._create_portfolio_pdf_file(portfolio_data, pdf_path)
        
        return pdf_id
    
    def _create_assessment_pdf_file(self, data: Dict[str, Any], pdf_path: Path):
        """Create actual PDF file for assessment with charts and visual elements"""
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor(self.colors['primary'])
        )
        story.append(Paragraph("CLIENT ASSESSMENT REPORT", title_style))
        story.append(Spacer(1, 12))
        
        # Date
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Client Information
        story.append(Paragraph("Client Information:", styles['Heading2']))
        client_data = [
            ['Name:', data.get('client_name', 'N/A')],
            ['Age:', str(data.get('age', 'N/A'))],
            ['Marital Status:', data.get('marital_status', 'N/A')],
            ['Dependents:', str(data.get('dependents', 'N/A'))],
            ['Health Status:', data.get('health_status', 'N/A')],
            ['Tobacco Use:', data.get('tobacco_use', 'N/A')]
        ]
        client_table = Table(client_data, colWidths=[2*inch, 3*inch])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(client_table)
        story.append(Spacer(1, 20))
        
        # Financial Information
        story.append(Paragraph("Financial Information:", styles['Heading2']))
        financial_data = [
            ['Monthly Income:', f"${data.get('monthly_income', 0):,.2f}"],
            ['Monthly Expenses:', f"${data.get('monthly_expenses', 0):,.2f}"],
            ['Mortgage Balance:', f"${data.get('mortgage_balance', 0):,.2f}"],
            ['Other Debts:', f"${data.get('other_debts', 0):,.2f}"],
            ['Additional Obligations:', f"${data.get('additional_obligations', 0):,.2f}"],
            ['Savings:', f"${data.get('savings', 0):,.2f}"],
            ['Investments:', f"${data.get('investments', 0):,.2f}"],
            ['Other Assets:', f"${data.get('other_assets', 0):,.2f}"]
        ]
        financial_table = Table(financial_data, colWidths=[2*inch, 3*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['secondary'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(financial_table)
        story.append(Spacer(1, 20))
        
        # Coverage Breakdown Chart
        needs_breakdown = data.get('needs_breakdown', {})
        if needs_breakdown:
            story.append(Paragraph("Coverage Breakdown:", styles['Heading2']))
            chart_buffer = self._create_coverage_breakdown_chart(needs_breakdown)
            if chart_buffer:
                chart_img = Image(chart_buffer, width=6*inch, height=4.5*inch)
                story.append(chart_img)
                story.append(Spacer(1, 20))
        
        # Assessment Results
        story.append(Paragraph("Assessment Results:", styles['Heading2']))
        assessment_data = [
            ['Recommended Coverage:', f"${data.get('recommended_coverage', 0):,.2f}"],
            ['Coverage Gap:', f"${data.get('gap', 0):,.2f}"],
            ['Product Recommendation:', data.get('product_recommendation', 'N/A')],
            ['Duration:', f"{data.get('duration_years', 'N/A')} years"],
            ['Recommended Monthly Savings:', f"${data.get('recommended_monthly_savings', 0):,.2f}"],
            ['Max Monthly Contribution:', f"${data.get('max_monthly_contribution', 0):,.2f}"]
        ]
        assessment_table = Table(assessment_data, colWidths=[2*inch, 3*inch])
        assessment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['success'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(assessment_table)
        story.append(Spacer(1, 20))
        
        # Cash Value Projection Chart
        cash_value_projection = data.get('cash_value_projection', [])
        if cash_value_projection:
            story.append(Paragraph("Cash Value Projection:", styles['Heading2']))
            chart_buffer = self._create_cash_value_projection_chart(cash_value_projection)
            if chart_buffer:
                chart_img = Image(chart_buffer, width=7*inch, height=4.5*inch)
                story.append(chart_img)
                story.append(Spacer(1, 20))
        
        # Rationale
        if data.get('rationale'):
            story.append(Paragraph("Rationale:", styles['Heading2']))
            rationale_style = ParagraphStyle(
                'RationaleStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=12,
                leftIndent=20,
                rightIndent=20,
                borderColor=colors.HexColor(self.colors['primary']),
                borderWidth=1,
                borderPadding=10,
                backColor=colors.HexColor('#f8f9fa')
            )
            story.append(Paragraph(data.get('rationale', ''), rationale_style))
            story.append(Spacer(1, 20))
        
        # Advisor Notes
        if data.get('advisor_notes'):
            story.append(Paragraph("Advisor Notes:", styles['Heading2']))
            notes_style = ParagraphStyle(
                'NotesStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=12,
                leftIndent=20,
                rightIndent=20,
                borderColor=colors.HexColor(self.colors['warning']),
                borderWidth=1,
                borderPadding=10,
                backColor=colors.HexColor('#fff8e1')
            )
            story.append(Paragraph(data.get('advisor_notes', ''), notes_style))
            story.append(Spacer(1, 20))
        
        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=12,
            textColor=colors.grey,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Disclaimer:", styles['Heading3']))
        story.append(Paragraph("This report is for informational purposes only. Please consult with a qualified financial advisor for personalized advice.", disclaimer_style))
        
        doc.build(story)
    
    def _create_assessment_pdf_content(self, data: Dict[str, Any]) -> str:
        """Create assessment PDF content"""
        return f"""
CLIENT ASSESSMENT REPORT
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Client Information:
- Age: {data.get('age', 'N/A')}
- Marital Status: {data.get('marital_status', 'N/A')}
- Dependents: {data.get('dependents', 'N/A')}
- Health Status: {data.get('health_status', 'N/A')}
- Tobacco Use: {data.get('tobacco_use', 'N/A')}

Financial Information:
- Monthly Income: ${data.get('monthly_income', 0):,.2f}
- Monthly Expenses: ${data.get('monthly_expenses', 0):,.2f}
- Mortgage Balance: ${data.get('mortgage_balance', 0):,.2f}
- Other Debts: ${data.get('other_debts', 0):,.2f}
- Additional Obligations: ${data.get('additional_obligations', 0):,.2f}

Education Planning:
- Provide Education: {data.get('provide_education', 'N/A')}
- Number of Children: {data.get('num_children', 'N/A')}
- Education Type: {data.get('education_type', 'N/A')}
- Cost per Child: ${data.get('education_cost_per_child', 0):,.2f}

Final Expenses & Legacy:
- Funeral Expenses: ${data.get('funeral_expenses', 0):,.2f}
- Legacy Amount: ${data.get('legacy_amount', 0):,.2f}
- Special Needs: {data.get('special_needs', 'N/A')}

Existing Assets & Coverage:
- Savings: ${data.get('savings', 0):,.2f}
- Investments: ${data.get('investments', 0):,.2f}
- Individual Life Insurance: ${data.get('individual_life', 0):,.2f}
- Group Life Insurance: ${data.get('group_life', 0):,.2f}
- Other Assets: ${data.get('other_assets', 0):,.2f}

RECOMMENDATIONS:
- Recommended Coverage: ${data.get('recommended_coverage', 0):,.2f}
- Coverage Gap: ${data.get('gap', 0):,.2f}
- Product Recommendation: {data.get('product_recommendation', 'N/A')}
- Duration: {data.get('duration_years', 'N/A')} years
- Rationale: {data.get('rationale', 'N/A')}

Cash Value Projection:
{json.dumps(data.get('cash_value_projection', []), indent=2)}

Advisor Notes:
{data.get('advisor_notes', 'None')}

---
This report is for informational purposes only. Please consult with a qualified financial advisor for personalized advice.
        """
    
    def _create_portfolio_pdf_file(self, data: Dict[str, Any], pdf_path: Path):
        """Create actual PDF file for portfolio analysis with charts and visual elements"""
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor(self.colors['primary'])
        )
        story.append(Paragraph("PORTFOLIO ANALYSIS REPORT", title_style))
        story.append(Spacer(1, 12))
        
        # Date
        story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Client Information
        story.append(Paragraph("Client Information:", styles['Heading2']))
        client_data = [
            ['Name:', data.get('client_name', 'N/A')],
            ['Age:', str(data.get('age', 'N/A'))],
            ['Marital Status:', data.get('marital_status', 'N/A')],
            ['Dependents:', str(data.get('dependents', 'N/A'))],
            ['Health Status:', data.get('health_status', 'N/A')],
            ['Tobacco Use:', data.get('tobacco_use', 'N/A')]
        ]
        client_table = Table(client_data, colWidths=[2*inch, 3*inch])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(client_table)
        story.append(Spacer(1, 20))
        
        # Portfolio Summary
        story.append(Paragraph("Portfolio Summary:", styles['Heading2']))
        portfolio_data = [
            ['Total Assets:', f"${data.get('total_assets', 0):,.2f}"],
            ['Investable Portfolio:', f"${data.get('investable_portfolio', 0):,.2f}"],
            ['Total Net Worth:', f"${data.get('total_net_worth', 0):,.2f}"],
            ['Liquid Assets:', f"${data.get('liquid_assets', 0):,.2f}"],
            ['Monthly Income:', f"${data.get('monthly_income', 0):,.2f}"],
            ['Monthly Expenses:', f"${data.get('monthly_expenses', 0):,.2f}"]
        ]
        portfolio_table = Table(portfolio_data, colWidths=[2*inch, 3*inch])
        portfolio_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['secondary'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(portfolio_table)
        story.append(Spacer(1, 20))
        
        # Asset Allocation Chart
        asset_allocation = data.get('asset_allocation', {})
        if asset_allocation:
            story.append(Paragraph("Asset Allocation:", styles['Heading2']))
            chart_buffer = self._create_asset_allocation_chart(asset_allocation)
            if chart_buffer:
                chart_img = Image(chart_buffer, width=6*inch, height=4.5*inch)
                story.append(chart_img)
                story.append(Spacer(1, 20))
        
        # Account Breakdown
        story.append(Paragraph("Account Breakdown:", styles['Heading2']))
        account_data = [
            ['Retirement Accounts:', f"${data.get('retirement_accounts', 0):,.2f}"],
            ['Taxable Accounts:', f"${data.get('taxable_accounts', 0):,.2f}"],
            ['Education Accounts:', f"${data.get('education_accounts', 0):,.2f}"],
            ['Real Estate Value:', f"${data.get('real_estate_value', 0):,.2f}"],
            ['Total Liabilities:', f"${data.get('liabilities_total', 0):,.2f}"]
        ]
        account_table = Table(account_data, colWidths=[2*inch, 3*inch])
        account_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['info'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(account_table)
        story.append(Spacer(1, 20))
        
        # Analysis Results with Risk Gauge
        portfolio_metrics = data.get('portfolio_metrics', {})
        life_insurance_needs = data.get('life_insurance_needs', {})
        
        story.append(Paragraph("Analysis Results:", styles['Heading2']))
        
        # Risk Score Gauge
        risk_score = portfolio_metrics.get('risk_score', 0)
        risk_level = portfolio_metrics.get('risk_level', 'moderate')
        if risk_score > 0:
            gauge_buffer = self._create_risk_score_gauge(risk_score, risk_level)
            if gauge_buffer:
                gauge_img = Image(gauge_buffer, width=3*inch, height=3*inch)
                story.append(gauge_img)
                story.append(Spacer(1, 10))
        
        analysis_data = [
            ['Risk Level:', portfolio_metrics.get('risk_level', 'N/A')],
            ['Risk Score:', f"{portfolio_metrics.get('risk_score', 0)}/100"],
            ['Portfolio Health Score:', f"{portfolio_metrics.get('portfolio_health_score', 0)}/100"],
            ['Liquidity Ratio:', f"{portfolio_metrics.get('liquidity_ratio', 0):.2f}"],
            ['Diversification Score:', f"{portfolio_metrics.get('diversification_score', 0)}/100"]
        ]
        analysis_table = Table(analysis_data, colWidths=[2*inch, 3*inch])
        analysis_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['warning'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(analysis_table)
        story.append(Spacer(1, 20))
        
        # Life Insurance Needs
        story.append(Paragraph("Life Insurance Needs:", styles['Heading2']))
        insurance_data = [
            ['Total Coverage Need:', f"${life_insurance_needs.get('total_need', 0):,.2f}"],
            ['Income Replacement:', f"${life_insurance_needs.get('income_replacement', 0):,.2f}"],
            ['Debt Payoff:', f"${life_insurance_needs.get('debt_payoff', 0):,.2f}"],
            ['Education Funding:', f"${life_insurance_needs.get('education_funding', 0):,.2f}"],
            ['Funeral Expenses:', f"${life_insurance_needs.get('funeral_expenses', 0):,.2f}"],
            ['Legacy Amount:', f"${life_insurance_needs.get('legacy_amount', 0):,.2f}"],
            ['Coverage Gap:', f"${life_insurance_needs.get('coverage_gap', 0):,.2f}"]
        ]
        insurance_table = Table(insurance_data, colWidths=[2*inch, 3*inch])
        insurance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['danger'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(insurance_table)
        story.append(Spacer(1, 20))
        
        # Cash Value Projection Chart
        cash_value_projection = data.get('cash_value_projection', [])
        if cash_value_projection:
            story.append(Paragraph("Cash Value Projection:", styles['Heading2']))
            chart_buffer = self._create_cash_value_projection_chart(cash_value_projection)
            if chart_buffer:
                chart_img = Image(chart_buffer, width=7*inch, height=4.5*inch)
                story.append(chart_img)
                story.append(Spacer(1, 20))
        
        # Product Recommendation
        story.append(Paragraph("Product Recommendation:", styles['Heading2']))
        product_data = [
            ['Recommended Product:', data.get('product_recommendation', 'N/A')],
            ['Duration:', f"{data.get('duration_years', 'N/A')} years"],
            ['Recommended Monthly Savings:', f"${data.get('recommended_monthly_savings', 0):,.2f}"],
            ['Max Monthly Contribution:', f"${data.get('max_monthly_contribution', 0):,.2f}"]
        ]
        product_table = Table(product_data, colWidths=[2*inch, 3*inch])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.colors['success'])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(product_table)
        story.append(Spacer(1, 20))
        
        # Key Findings and Analysis
        key_findings = data.get('key_findings', [])
        if key_findings:
            story.append(Paragraph("Key Findings:", styles['Heading2']))
            for finding in key_findings:
                finding_style = ParagraphStyle(
                    'FindingStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceAfter=6,
                    leftIndent=20,
                    bulletText='•'
                )
                story.append(Paragraph(finding, finding_style))
            story.append(Spacer(1, 20))
        
        # Risk Analysis
        risk_analysis = data.get('risk_analysis', [])
        if risk_analysis:
            story.append(Paragraph("Risk Analysis:", styles['Heading2']))
            for risk in risk_analysis:
                risk_style = ParagraphStyle(
                    'RiskStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceAfter=6,
                    leftIndent=20,
                    bulletText='•'
                )
                story.append(Paragraph(risk, risk_style))
            story.append(Spacer(1, 20))
        
        # Recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Recommendations:", styles['Heading2']))
            for rec in recommendations:
                rec_style = ParagraphStyle(
                    'RecStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceAfter=6,
                    leftIndent=20,
                    bulletText='•'
                )
                story.append(Paragraph(rec, rec_style))
            story.append(Spacer(1, 20))
        
        # Rationale
        if data.get('rationale'):
            story.append(Paragraph("Rationale:", styles['Heading2']))
            rationale_style = ParagraphStyle(
                'RationaleStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=12,
                leftIndent=20,
                rightIndent=20,
                borderColor=colors.HexColor(self.colors['primary']),
                borderWidth=1,
                borderPadding=10,
                backColor=colors.HexColor('#f8f9fa')
            )
            story.append(Paragraph(data.get('rationale', ''), rationale_style))
            story.append(Spacer(1, 20))
        
        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=12,
            textColor=colors.grey,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Disclaimer:", styles['Heading3']))
        story.append(Paragraph("This report is for informational purposes only. Please consult with a qualified financial advisor for personalized advice.", disclaimer_style))
        
        doc.build(story)
    
    def _create_portfolio_pdf_content(self, data: Dict[str, Any]) -> str:
        """Create portfolio PDF content"""
        # Extract data from the actual structure being sent
        portfolio_metrics = data.get('portfolio_metrics', {})
        asset_allocation = data.get('asset_allocation', {})
        life_insurance_needs = data.get('life_insurance_needs', {})
        
        return f"""
PORTFOLIO ANALYSIS REPORT
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Client Information:
- Name: {data.get('client_name', 'N/A')}
- Age: {data.get('age', 'N/A')}
- Marital Status: {data.get('marital_status', 'N/A')}
- Dependents: {data.get('dependents', 'N/A')}

Portfolio Summary:
- Total Assets: ${data.get('total_assets', 0):,.2f}
- Investable Portfolio: ${data.get('investable_portfolio', 0):,.2f}
- Total Net Worth: ${data.get('total_net_worth', 0):,.2f}
- Liquid Assets: ${data.get('liquid_assets', 0):,.2f}

Asset Allocation:
- Equity: {asset_allocation.get('equity', 0):.1f}%
- Fixed Income: {asset_allocation.get('fixed_income', 0):.1f}%
- Real Estate: {asset_allocation.get('real_estate', 0):.1f}%
- Cash: {asset_allocation.get('cash', 0):.1f}%
- Alternative Investments: {asset_allocation.get('alternative_investments', 0):.1f}%

Account Breakdown:
- Retirement Accounts: ${data.get('retirement_accounts', 0):,.2f}
- Taxable Accounts: ${data.get('taxable_accounts', 0):,.2f}
- Education Accounts: ${data.get('education_accounts', 0):,.2f}
- Real Estate Value: ${data.get('real_estate_value', 0):,.2f}
- Total Liabilities: ${data.get('liabilities_total', 0):,.2f}

Risk Profile & Goals:
- Risk Tolerance: {data.get('risk_tolerance', 'N/A')}
- Investment Horizon: {data.get('investment_horizon', 'N/A')} years
- Retirement Target: ${data.get('retirement_target', 0):,.2f}
- Legacy Goals: ${data.get('legacy_goals', 0):,.2f}

Insurance & Protection:
- Current Life Insurance: ${data.get('current_life_insurance', 0):,.2f}
- Individual Life: ${data.get('individual_life', 0):,.2f}
- Group Life: ${data.get('group_life', 0):,.2f}
- Income Replacement Years: {data.get('income_replacement_years', 'N/A')}

ANALYSIS RESULTS:
- Risk Level: {portfolio_metrics.get('risk_level', 'N/A')}
- Risk Score: {portfolio_metrics.get('risk_score', 0)}/100
- Portfolio Health Score: {portfolio_metrics.get('portfolio_health_score', 0)}/100

LIFE INSURANCE NEEDS:
- Total Coverage Need: ${life_insurance_needs.get('total_need', 0):,.2f}
- Income Replacement: ${life_insurance_needs.get('income_replacement', 0):,.2f}
- Debt Payoff: ${life_insurance_needs.get('debt_payoff', 0):,.2f}
- Education Funding: ${life_insurance_needs.get('education_funding', 0):,.2f}
- Funeral Expenses: ${life_insurance_needs.get('funeral_expenses', 0):,.2f}
- Legacy Amount: ${life_insurance_needs.get('legacy_amount', 0):,.2f}
- Coverage Gap: ${life_insurance_needs.get('coverage_gap', 0):,.2f}

PRODUCT RECOMMENDATION:
- Recommended Product: {data.get('product_recommendation', 'N/A')}
- Duration: {data.get('duration_years', 'N/A')} years
- Rationale: {data.get('rationale', 'N/A')}

Key Findings:
{json.dumps(data.get('key_findings', []), indent=2)}

Risk Analysis:
{json.dumps(data.get('risk_analysis', []), indent=2)}

Opportunities:
{json.dumps(data.get('opportunities', []), indent=2)}

Recommendations:
{json.dumps(data.get('recommendations', []), indent=2)}

---
This report is for informational purposes only. Please consult with a qualified financial advisor for personalized advice.
        """
    
    def get_pdf_path(self, pdf_id: str) -> Path:
        """Get the file path for a PDF"""
        return self.output_dir / f"{pdf_id}.pdf"
    
    def cleanup_old_pdfs(self, max_age_hours: int = 24):
        """Clean up old PDF files"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        for pdf_file in self.output_dir.glob("*.pdf"):
            if pdf_file.stat().st_mtime < cutoff_time.timestamp():
                pdf_file.unlink()
    
    def get_pdf_stats(self) -> Dict[str, Any]:
        """Get statistics about generated PDFs"""
        pdf_files = list(self.output_dir.glob("*.pdf"))
        return {
            "total_pdfs": len(pdf_files),
            "output_directory": str(self.output_dir),
            "oldest_pdf": min([f.stat().st_mtime for f in pdf_files]) if pdf_files else None,
            "newest_pdf": max([f.stat().st_mtime for f in pdf_files]) if pdf_files else None
        }
