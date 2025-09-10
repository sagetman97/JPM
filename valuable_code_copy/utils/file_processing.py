"""
File processing utilities for the Financial Advisor Assistant.
Based on patterns from AIE7 course materials.
"""

import os
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader
)
from config.settings import settings


def get_file_loader(file_path: str):
    """
    Get appropriate loader for file type.
    Based on patterns from AIE7 course materials.
    """
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension == '.pdf':
        return PyMuPDFLoader(file_path)
    elif file_extension == '.txt':
        return TextLoader(file_path, encoding='utf-8')
    elif file_extension == '.csv':
        return CSVLoader(file_path)
    elif file_extension == '.docx':
        return UnstructuredWordDocumentLoader(file_path)
    elif file_extension == '.xlsx':
        return UnstructuredExcelLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def process_uploaded_file(file_path: str, session_id: str) -> List[Document]:
    """
    Process an uploaded file and return documents with session metadata.
    
    Args:
        file_path: Path to the uploaded file
        session_id: Unique session identifier
        
    Returns:
        List of documents with session metadata
    """
    try:
        loader = get_file_loader(file_path)
        documents = loader.load()
        
        # Add session metadata
        for doc in documents:
            doc.metadata.update({
                "session_id": session_id,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "source_type": "uploaded_file",
                "upload_timestamp": pd.Timestamp.now().isoformat()
            })
        
        return documents
        
    except Exception as e:
        raise ValueError(f"Error processing file {file_path}: {str(e)}")


def extract_financial_data_from_excel(file_path: str) -> Dict[str, Any]:
    """
    Extract financial data from Excel files for portfolio analysis.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        Dictionary containing extracted financial data
    """
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        financial_data = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Look for common financial data patterns
            if 'portfolio' in sheet_name.lower() or 'allocation' in sheet_name.lower():
                financial_data['portfolio_allocation'] = df.to_dict('records')
            elif 'income' in sheet_name.lower() or 'earnings' in sheet_name.lower():
                financial_data['income_data'] = df.to_dict('records')
            elif 'expenses' in sheet_name.lower() or 'liabilities' in sheet_name.lower():
                financial_data['expense_data'] = df.to_dict('records')
            else:
                financial_data[sheet_name] = df.to_dict('records')
        
        return financial_data
        
    except Exception as e:
        raise ValueError(f"Error extracting financial data from {file_path}: {str(e)}")


def extract_portfolio_summary(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract portfolio summary from financial data.
    
    Args:
        financial_data: Dictionary of financial data
        
    Returns:
        Portfolio summary dictionary
    """
    summary = {
        "total_assets": 0,
        "total_liabilities": 0,
        "asset_allocation": {},
        "risk_profile": "unknown",
        "income": 0,
        "expenses": 0
    }
    
    # Calculate total assets
    if 'portfolio_allocation' in financial_data:
        for item in financial_data['portfolio_allocation']:
            if 'value' in item:
                summary["total_assets"] += float(item['value'])
            if 'asset_type' in item and 'value' in item:
                asset_type = item['asset_type']
                value = float(item['value'])
                summary["asset_allocation"][asset_type] = summary["asset_allocation"].get(asset_type, 0) + value
    
    # Calculate income
    if 'income_data' in financial_data:
        for item in financial_data['income_data']:
            if 'amount' in item:
                summary["income"] += float(item['amount'])
    
    # Calculate expenses
    if 'expense_data' in financial_data:
        for item in financial_data['expense_data']:
            if 'amount' in item:
                summary["expenses"] += float(item['amount'])
    
    # Determine risk profile based on asset allocation
    if summary["asset_allocation"]:
        equity_percentage = sum(value for asset_type, value in summary["asset_allocation"].items() 
                              if 'stock' in asset_type.lower() or 'equity' in asset_type.lower())
        total_assets = summary["total_assets"]
        
        if total_assets > 0:
            equity_ratio = equity_percentage / total_assets
            
            if equity_ratio > 0.7:
                summary["risk_profile"] = "aggressive"
            elif equity_ratio > 0.4:
                summary["risk_profile"] = "moderate"
            else:
                summary["risk_profile"] = "conservative"
    
    return summary


def validate_file_upload(file_path: str) -> bool:
    """
    Validate uploaded file for processing.
    
    Args:
        file_path: Path to uploaded file
        
    Returns:
        True if file is valid for processing
    """
    # Check file exists
    if not os.path.exists(file_path):
        return False
    
    # Check file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        return False
    
    # Check file extension
    file_extension = Path(file_path).suffix.lower()
    if file_extension not in settings.SUPPORTED_FILE_TYPES:
        return False
    
    return True


def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get metadata for uploaded file.
    
    Args:
        file_path: Path to file
        
    Returns:
        File metadata dictionary
    """
    stat = os.stat(file_path)
    
    return {
        "file_name": os.path.basename(file_path),
        "file_size_mb": stat.st_size / (1024 * 1024),
        "file_extension": Path(file_path).suffix.lower(),
        "created_time": pd.Timestamp(stat.st_ctime, unit='s').isoformat(),
        "modified_time": pd.Timestamp(stat.st_mtime, unit='s').isoformat()
    }


def create_session_document_collection(session_id: str) -> str:
    """
    Create a unique collection name for session documents.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Collection name for Qdrant
    """
    return f"session_{session_id}_docs"


def cleanup_session_files(session_id: str, temp_dir: str):
    """
    Clean up temporary files for a session.
    
    Args:
        session_id: Session identifier
        temp_dir: Temporary directory path
    """
    try:
        session_files = [f for f in os.listdir(temp_dir) if session_id in f]
        for file_name in session_files:
            file_path = os.path.join(temp_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not cleanup session files: {e}") 