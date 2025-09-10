"""
Simple PDF Generator for RoboAdvisor
Uses screenshot-based approach to generate exact 1:1 copies of frontend reports
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .screenshot_pdf_generator import ScreenshotPDFGenerator

logger = logging.getLogger(__name__)


class SimplePDFGenerator:
    """Simple PDF generator using screenshot approach"""
    
    def __init__(self, frontend_url: str = None, output_dir: str = "chatbot/generated_pdfs"):
        self.frontend_url = frontend_url or os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_portfolio_pdf(self, portfolio_data: Dict[str, Any], session_id: str) -> str:
        """
        Generate portfolio PDF using screenshot approach
        
        Args:
            portfolio_data: The portfolio analysis data
            session_id: Unique session identifier
            
        Returns:
            PDF file ID for retrieval
        """
        try:
            async with ScreenshotPDFGenerator(self.frontend_url, str(self.output_dir)) as generator:
                pdf_id = await generator.generate_portfolio_pdf(portfolio_data, session_id)
                logger.info(f"Portfolio PDF generated successfully: {pdf_id}")
                return pdf_id
        except Exception as e:
            logger.error(f"Error generating portfolio PDF: {e}")
            raise
    
    async def generate_assessment_pdf(self, assessment_data: Dict[str, Any], session_id: str, pdf_url: str = None) -> str:
        """
        Generate assessment PDF using screenshot approach
        
        Args:
            assessment_data: The assessment data
            session_id: Unique session identifier
            pdf_url: Optional URL to use for PDF generation
            
        Returns:
            PDF file ID for retrieval
        """
        try:
            async with ScreenshotPDFGenerator(self.frontend_url, str(self.output_dir)) as generator:
                pdf_id = await generator.generate_assessment_pdf(assessment_data, session_id, pdf_url)
                logger.info(f"Assessment PDF generated successfully: {pdf_id}")
                return pdf_id
        except Exception as e:
            logger.error(f"Error generating assessment PDF: {e}")
            raise
    
    def get_pdf_path(self, pdf_id: str) -> Path:
        """Get the file path for a generated PDF"""
        return self.output_dir / f"{pdf_id}.pdf"
    
    def pdf_exists(self, pdf_id: str) -> bool:
        """Check if a PDF exists"""
        return self.get_pdf_path(pdf_id).exists()


# Global instance for backward compatibility
_pdf_generator = None

def get_pdf_generator() -> SimplePDFGenerator:
    """Get the global PDF generator instance"""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = SimplePDFGenerator()
    return _pdf_generator

# Convenience functions for backward compatibility
async def generate_portfolio_pdf(portfolio_data: Dict[str, Any], session_id: str) -> str:
    """Generate portfolio PDF using screenshot approach"""
    generator = get_pdf_generator()
    return await generator.generate_portfolio_pdf(portfolio_data, session_id)

async def generate_assessment_pdf(assessment_data: Dict[str, Any], session_id: str, pdf_url: str = None) -> str:
    """Generate assessment PDF using screenshot approach"""
    generator = get_pdf_generator()
    return await generator.generate_assessment_pdf(assessment_data, session_id, pdf_url)
