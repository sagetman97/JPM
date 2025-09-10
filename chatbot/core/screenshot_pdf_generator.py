"""
Screenshot-based PDF Generator for RoboAdvisor
Generates PDFs by taking screenshots of the actual frontend pages
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


class ScreenshotPDFGenerator:
    """Generates PDFs by taking screenshots of frontend pages"""
    
    def __init__(self, frontend_url: str = None, output_dir: str = "chatbot/generated_pdfs"):
        self.frontend_url = frontend_url or os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Browser instance (will be initialized when needed)
        self._browser: Optional[Browser] = None
        self._playwright = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def _ensure_browser(self):
        """Ensure browser is initialized"""
        if not self._browser:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
    
    async def generate_portfolio_pdf(self, portfolio_data: Dict[str, Any], session_id: str) -> str:
        """
        Generate PDF by taking screenshot of portfolio assessment page with analysis data in URL
        
        Args:
            portfolio_data: The portfolio analysis data (not used directly, data is in URL)
            session_id: Unique session identifier
            
        Returns:
            PDF file ID for retrieval
        """
        logger.info(f"=== PDF GENERATOR DEBUG: Starting generate_portfolio_pdf with session_id: {session_id}")
        logger.info(f"=== PDF GENERATOR DEBUG: Portfolio data keys: {list(portfolio_data.keys()) if portfolio_data else 'None'}")
        
        await self._ensure_browser()
        
        # Create a temporary page
        page = await self._browser.new_page()
        
        try:
            # Set viewport for consistent rendering - wider for better content capture
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate to the frontend URL with analysis data
            # The URL should contain the analysis data and step=10 for results
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            encoded_data = self._encode_analysis_data(portfolio_data)
            logger.info(f"Encoded analysis data length: {len(encoded_data)}")
            if not encoded_data:
                logger.error("Failed to encode analysis data - using fallback URL")
                pdf_url = f"{self.frontend_url}/portfolio-assessment?session_id={session_id}&knowledge_level=beginner&source=robo_advisor_chatbot&timestamp={timestamp}&step=10"
            else:
                pdf_url = f"{self.frontend_url}/portfolio-assessment?session_id={session_id}&knowledge_level=beginner&source=robo_advisor_chatbot&timestamp={timestamp}&step=10&analysis_data={encoded_data}"
            logger.info(f"Navigating to portfolio URL with analysis data: {pdf_url}")
            
            await page.goto(pdf_url)
            
            # Wait for the page to load completely
            await page.wait_for_load_state("networkidle")
            await page.wait_for_load_state("domcontentloaded")
            
            # Wait for the analysis state to be restored and results to render
            await asyncio.sleep(8)  # Wait for content to load
            
            # Wait for specific portfolio results content to be visible
            try:
                # Wait for key portfolio results elements
                await page.wait_for_selector('.portfolio-results', timeout=15000)
                await page.wait_for_selector('.life-insurance-needs', timeout=10000)
                logger.info("Portfolio results content detected")
            except Exception as e:
                logger.warning(f"Portfolio results selectors not found, proceeding anyway: {e}")
            
            # Additional wait to ensure all content is fully rendered
            await asyncio.sleep(3)
            
            # Check if the page loaded successfully and shows results
            page_title = await page.title()
            logger.info(f"Page loaded with title: {page_title}")
            
            # Generate multi-page PDF by capturing different sections
            pdf_id = f"portfolio_{session_id}"
            
            # Get the full page height to determine how many pages we need
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = 1080
            total_pages = max(1, (page_height + viewport_height - 1) // viewport_height)
            
            logger.info(f"Full page height: {page_height}px, generating {total_pages} pages")
            
            # Create PDF with multiple pages
            pdf_path = await self._generate_multi_page_pdf(page, pdf_id, total_pages, viewport_height)
            
            logger.info(f"Portfolio PDF generated: {pdf_path}")
            return pdf_id
            
        except Exception as e:
            logger.error(f"Error generating portfolio PDF: {e}")
            raise
        finally:
            await page.close()
    
    def _encode_analysis_data(self, portfolio_data: Dict[str, Any]) -> str:
        """Encode portfolio data for URL parameter"""
        import base64
        import json
        
        try:
            logger.info(f"Encoding portfolio data with keys: {list(portfolio_data.keys()) if portfolio_data else 'None'}")
            
            # The portfolio_data now contains the complete structure from frontend
            # It should have formData, result, and step
            if 'formData' in portfolio_data and 'result' in portfolio_data:
                # Use the data structure as-is from frontend
                analysis_data = portfolio_data
            else:
                # Fallback: create the structure (for backward compatibility)
                analysis_data = {
                    "formData": portfolio_data,
                    "result": portfolio_data,
                    "step": 10
                }
            
            # Encode as base64
            json_str = json.dumps(analysis_data)
            encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            logger.info(f"Successfully encoded analysis data, length: {len(encoded)}")
            return encoded
        except Exception as e:
            logger.error(f"Error encoding analysis data: {e}")
            return ""
    
    async def generate_assessment_pdf(self, assessment_data: Dict[str, Any], session_id: str, pdf_url: str = None) -> str:
        """
        Generate PDF by taking screenshot of assessment page with data
        
        Args:
            assessment_data: The assessment data
            session_id: Unique session identifier
            pdf_url: Optional URL to use for PDF generation (if provided, uses this instead of constructing)
            
        Returns:
            PDF file ID for retrieval
        """
        await self._ensure_browser()
        
        # Create a temporary page with the assessment data
        page = await self._browser.new_page()
        
        try:
            # Set viewport for consistent rendering - wider for better content capture
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Use provided URL or construct one with analysis data
            if pdf_url:
                logger.info(f"Using provided PDF URL: {pdf_url}")
                final_url = pdf_url
            else:
                # Navigate to the frontend URL with analysis data
                # The URL should contain the analysis data and step=10 for results
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                encoded_data = self._encode_analysis_data(assessment_data)
                logger.info(f"Encoded assessment data length: {len(encoded_data)}")
                if not encoded_data:
                    logger.error("Failed to encode assessment data - using fallback URL")
                    final_url = f"{self.frontend_url}/assessment?session_id={session_id}&knowledge_level=beginner&source=robo_advisor_chatbot&timestamp={timestamp}&step=10"
                else:
                    final_url = f"{self.frontend_url}/assessment?session_id={session_id}&knowledge_level=beginner&source=robo_advisor_chatbot&timestamp={timestamp}&step=10&analysis_data={encoded_data}"
                logger.info(f"Constructed assessment URL with analysis data: {final_url}")
            
            await page.goto(final_url)
            
            # Wait for the page to load completely
            await page.wait_for_load_state("networkidle")
            await page.wait_for_load_state("domcontentloaded")
            
            # Wait for the analysis state to be restored and results to render
            await asyncio.sleep(8)  # Wait for content to load
            
            # Wait for specific assessment results content to be visible
            try:
                # Wait for key assessment results elements
                await page.wait_for_selector('[data-testid="assessment-results"]', timeout=15000)
                logger.info("Assessment results container found")
                
                # Wait for coverage breakdown to be visible
                await page.wait_for_selector('.coverage-breakdown, .mb-4', timeout=10000)
                logger.info("Assessment content loaded")
                
            except Exception as e:
                logger.warning(f"Timeout waiting for assessment content: {e}")
                # Continue anyway - might still work
            
            # Additional wait for any animations or dynamic content
            await asyncio.sleep(3)
            
            # Wait for results to be rendered
            try:
                await page.wait_for_selector('[data-testid="assessment-results"]', timeout=10000)
                await asyncio.sleep(3)  # Additional buffer for charts to render
                logger.info("Assessment results section found and rendered")
            except Exception as e:
                logger.warning(f"Results selector not found, proceeding with full page: {e}")
                await asyncio.sleep(3)  # Fallback delay
            
            # Take screenshot of results section
            pdf_id = f"assessment_{session_id}"
            screenshot_path = self.output_dir / f"{pdf_id}.png"
            
            # Try to screenshot just the results section first
            try:
                results_element = await page.query_selector('[data-testid="assessment-results"]')
                if results_element:
                    await results_element.screenshot(path=str(screenshot_path), type='png')
                    logger.info("Screenshot taken of results section")
                else:
                    # Fallback to full page
                    await page.screenshot(path=str(screenshot_path), full_page=True, type='png')
                    logger.info("Screenshot taken of full page (fallback)")
            except Exception as e:
                logger.warning(f"Error taking results screenshot, using full page: {e}")
                await page.screenshot(path=str(screenshot_path), full_page=True, type='png')
            
            # Convert screenshot to PDF
            pdf_path = await self._screenshot_to_pdf(screenshot_path, pdf_id)
            
            logger.info(f"Assessment PDF generated: {pdf_path}")
            return pdf_id
            
        except Exception as e:
            logger.error(f"Error generating assessment PDF: {e}")
            raise
        finally:
            await page.close()
    
    async def _generate_multi_page_pdf(self, page, pdf_id: str, total_pages: int, viewport_height: int) -> str:
        """
        Generate a multi-page PDF by capturing different sections of the page
        
        Args:
            page: Playwright page object
            pdf_id: Unique PDF identifier
            total_pages: Number of pages to generate
            viewport_height: Height of each viewport section
            
        Returns:
            Path to the generated PDF file
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        from PIL import Image
        import io
        
        pdf_path = self.output_dir / f"{pdf_id}.pdf"
        page_width, page_height = letter
        
        # Create PDF canvas
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        try:
            for page_num in range(total_pages):
                # Scroll to the appropriate position
                scroll_y = page_num * viewport_height
                await page.evaluate(f"window.scrollTo(0, {scroll_y})")
                await asyncio.sleep(1)  # Wait for scroll to complete
                
                # Take screenshot of current viewport
                screenshot_data = await page.screenshot(type='png')
                
                # Convert to PIL Image
                img = Image.open(io.BytesIO(screenshot_data))
                img_width, img_height = img.size
                
                # Calculate scaling to fit image on page with better readability
                scale_x = page_width / img_width
                scale_y = page_height / img_height
                # Use max scaling to make content larger and more readable
                scale = max(scale_x, scale_y) * 0.85  # Scale up for better readability
                
                # Calculate final dimensions
                final_width = img_width * scale
                final_height = img_height * scale
                
                # Center the image on the page
                x_offset = (page_width - final_width) / 2
                y_offset = (page_height - final_height) / 2
                
                # Add the image to PDF
                c.drawImage(
                    ImageReader(io.BytesIO(screenshot_data)),
                    x_offset,
                    y_offset,
                    width=final_width,
                    height=final_height
                )
                
                # Add page number
                c.setFont("Helvetica", 10)
                c.drawString(page_width - 100, 50, f"Page {page_num + 1} of {total_pages}")
                
                # Start new page if not the last page
                if page_num < total_pages - 1:
                    c.showPage()
                
                logger.info(f"Generated page {page_num + 1}/{total_pages}")
            
            # Save the PDF
            c.save()
            logger.info(f"Multi-page PDF saved: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Error generating multi-page PDF: {e}")
            raise

    async def _screenshot_to_pdf(self, screenshot_path: Path, pdf_id: str) -> Path:
        """
        Convert screenshot to PDF using reportlab
        
        Args:
            screenshot_path: Path to the screenshot image
            pdf_id: PDF identifier
            
        Returns:
            Path to the generated PDF
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.utils import ImageReader
        from PIL import Image
        
        pdf_path = self.output_dir / f"{pdf_id}.pdf"
        
        # Get image dimensions
        with Image.open(screenshot_path) as img:
            img_width, img_height = img.size
        
        # Use Letter size for better US printing and larger content
        page_width, page_height = letter
        
        # Calculate scaling - scale up to make content larger and more readable
        scale_x = page_width / img_width
        scale_y = page_height / img_height
        # Use max scaling to make content as large as possible while fitting the page
        scale = max(scale_x, scale_y) * 0.9  # Scale up to fill page better
        
        # Calculate final dimensions
        final_width = img_width * scale
        final_height = img_height * scale
        
        # Center the image on the page
        x_offset = (page_width - final_width) / 2
        y_offset = (page_height - final_height) / 2
        
        # Create PDF with Letter size (consistent with calculations)
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        # Add the image
        c.drawImage(
            ImageReader(str(screenshot_path)),
            x_offset,
            y_offset,
            width=final_width,
            height=final_height
        )
        
        c.save()
        
        # Clean up screenshot file
        screenshot_path.unlink(missing_ok=True)
        
        return pdf_path
    
    def get_pdf_path(self, pdf_id: str) -> Path:
        """Get the file path for a generated PDF"""
        return self.output_dir / f"{pdf_id}.pdf"
    
    def pdf_exists(self, pdf_id: str) -> bool:
        """Check if a PDF exists"""
        return self.get_pdf_path(pdf_id).exists()


# Convenience functions for backward compatibility
async def generate_portfolio_pdf(portfolio_data: Dict[str, Any], session_id: str) -> str:
    """Generate portfolio PDF using screenshot approach"""
    async with ScreenshotPDFGenerator() as generator:
        return await generator.generate_portfolio_pdf(portfolio_data, session_id)


async def generate_assessment_pdf(assessment_data: Dict[str, Any], session_id: str) -> str:
    """Generate assessment PDF using screenshot approach"""
    async with ScreenshotPDFGenerator() as generator:
        return await generator.generate_assessment_pdf(assessment_data, session_id)
