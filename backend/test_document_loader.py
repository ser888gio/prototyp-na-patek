#!/usr/bin/env python3
"""
Test script for the document loader functionality.
This script tests loading various document types to ensure they work correctly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent.document_loader import load_document, DocumentLoader


async def test_document_loader():
    """Test the document loader with various scenarios."""
    
    print("=== Document Loader Test Suite ===\n")
    
    # Test 1: Check supported extensions
    print("1. Testing supported file type detection:")
    test_files = [
        "test.pdf",
        "document.docx", 
        "presentation.pptx",
        "spreadsheet.xlsx",
        "notes.txt",
        "readme.md",
        "data.csv",
        "unsupported.xyz"
    ]
    
    for test_file in test_files:
        file_type = DocumentLoader.get_file_type(test_file)
        print(f"   {test_file} -> {file_type}")
    
    print(f"\n2. Supported extensions: {list(DocumentLoader.SUPPORTED_EXTENSIONS.keys())}")
    
    # Test 2: Try to load a sample text file if it exists
    print("\n3. Testing actual file loading:")
    
    # Create a temporary test file
    test_content = """This is a test document.
It contains multiple lines of text.
This tests the text file loading functionality."""
    
    test_file_path = "test_sample.txt"
    try:
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"   Created test file: {test_file_path}")
        
        # Test loading the file
        pages = await load_document(test_file_path)
        print(f"   Loaded {len(pages)} pages/sections")
        print(f"   Content preview: {pages[0][:100] if pages else 'No content'}...")
        
        # Clean up
        os.remove(test_file_path)
        print(f"   Cleaned up test file")
        
    except Exception as e:
        print(f"   Error during file test: {e}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_document_loader())
