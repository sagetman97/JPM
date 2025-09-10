"""
Document chunking utilities for the Financial Advisor Assistant.
Based on patterns from AIE7 course materials.
"""

import tiktoken
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config.settings import settings


def tiktoken_len(text: str) -> int:
    """
    Calculate token length using tiktoken.
    Based on patterns from AIE7 course materials.
    """
    encoding = tiktoken.encoding_for_model("gpt-4")
    return len(encoding.encode(text))


def create_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Create a text splitter optimized for financial documents.
    Based on patterns from 04_Production_RAG and 09_Advanced_Retrieval.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False,
    )


def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Chunk documents using the optimized text splitter.
    
    Args:
        documents: List of documents to chunk
        
    Returns:
        List of chunked documents with metadata preserved
    """
    text_splitter = create_text_splitter()
    
    chunked_docs = []
    for doc in documents:
        # Preserve original metadata
        metadata = doc.metadata.copy()
        
        # Add chunk-specific metadata
        metadata["source_type"] = "life_insurance_doc"
        metadata["chunk_index"] = 0
        
        # Split the document
        chunks = text_splitter.split_text(doc.page_content)
        
        # Create new documents for each chunk
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            
            chunked_docs.append(Document(
                page_content=chunk,
                metadata=chunk_metadata
            ))
    
    return chunked_docs


def semantic_chunking(documents: List[Document]) -> List[Document]:
    """
    Advanced semantic chunking for complex financial documents.
    Based on patterns from 09_Advanced_Retrieval.
    
    This approach tries to keep related concepts together.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=tiktoken_len,
        separators=[
            "\n\n## ",  # Markdown headers
            "\n\n### ",
            "\n\n#### ",
            "\n\n",     # Paragraph breaks
            "\n",       # Line breaks
            ". ",       # Sentences
            " ",        # Words
            ""          # Characters
        ],
        is_separator_regex=False,
    )
    
    chunked_docs = []
    for doc in documents:
        metadata = doc.metadata.copy()
        metadata["source_type"] = "life_insurance_doc"
        metadata["chunking_method"] = "semantic"
        
        chunks = text_splitter.split_text(doc.page_content)
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            
            chunked_docs.append(Document(
                page_content=chunk,
                metadata=chunk_metadata
            ))
    
    return chunked_docs


def add_metadata_to_chunks(chunks: List[Document], source_info: Dict[str, Any]) -> List[Document]:
    """
    Add additional metadata to document chunks.
    
    Args:
        chunks: List of document chunks
        source_info: Additional metadata to add
        
    Returns:
        List of chunks with enhanced metadata
    """
    enhanced_chunks = []
    
    for chunk in chunks:
        enhanced_metadata = chunk.metadata.copy()
        enhanced_metadata.update(source_info)
        
        enhanced_chunks.append(Document(
            page_content=chunk.page_content,
            metadata=enhanced_metadata
        ))
    
    return enhanced_chunks 