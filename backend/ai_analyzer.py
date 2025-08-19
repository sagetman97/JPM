"""
AI Portfolio Analyzer for comprehensive financial analysis.
Generates GPT-5 level insights after user confirms form data.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import re

# Fix: Use direct OpenAI import instead of langchain_openai for compatibility
from openai import OpenAI
from financial_models import FormData, create_default_form_data, convert_to_legacy_format

class AIAnalyzer:
    """AI-powered financial data analyzer"""
    
    def __init__(self, openai_api_key: str):
        self.llm = OpenAI(
            api_key=openai_api_key
        )
        self.model = "gpt-4o-mini"
        self.max_tokens = 2000
        self.temperature = 0 