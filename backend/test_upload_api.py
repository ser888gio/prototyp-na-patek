#!/usr/bin/env python3
"""
Test script to verify the file upload API works correctly.
"""

import asyncio
import requests
import io

def test_upload_endpoint():
    """Test the upload endpoint with a simple text file."""
    
    # Create a simple text file in memory
    file_content = b"This is a test document for the multi-format document loader.\nIt tests the upload functionality."
    file_like = io.BytesIO(file_content)
    
    # Prepare the request
    files = {
        'files': ('test.txt', file_like, 'text/plain')
    }
    
    try:
        print("Testing upload endpoint...")
        response = requests.post(
            'http://127.0.0.1:2024/uploadfile/',
            files=files,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Upload test successful!")
        else:
            print("❌ Upload test failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on http://127.0.0.1:2024")
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_upload_endpoint()
