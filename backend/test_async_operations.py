"""
Test file to verify async/await patterns are working correctly.
Run this with: python -m pytest test_async_operations.py -v
"""
import asyncio
import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Import the async functions we want to test
from agent.text_splitter import split_text_into_chunks
from agent.pdfloader import load_pdf


@pytest.mark.asyncio
async def test_async_text_splitting():
    """Test that text splitting works asynchronously."""
    test_text = "This is a test document. " * 100  # Create a longer text
    
    start_time = asyncio.get_event_loop().time()
    chunks = await split_text_into_chunks(test_text)
    end_time = asyncio.get_event_loop().time()
    
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    print(f"Text splitting took {end_time - start_time:.4f} seconds")


@pytest.mark.asyncio
async def test_async_pdf_loading():
    """Test that PDF loading works asynchronously."""
    # Create a temporary file path (we'll mock the actual PDF loading)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(b"Fake PDF content")
    
    try:
        # Mock the PyPDFLoader to avoid needing a real PDF
        with patch('agent.pdfloader.PyPDFLoader') as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader_class.return_value = mock_loader
            
            # Create mock pages
            mock_page1 = MagicMock()
            mock_page1.page_content = "This is page 1 content"
            mock_page2 = MagicMock()
            mock_page2.page_content = "This is page 2 content"
            
            # Mock the async iterator
            async def mock_alazy_load():
                yield mock_page1
                yield mock_page2
            
            mock_loader.alazy_load = mock_alazy_load
            
            start_time = asyncio.get_event_loop().time()
            pages = await load_pdf(temp_path)
            end_time = asyncio.get_event_loop().time()
            
            assert isinstance(pages, list)
            assert len(pages) == 2
            assert pages[0] == "This is page 1 content"
            assert pages[1] == "This is page 2 content"
            print(f"PDF loading took {end_time - start_time:.4f} seconds")
            
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.asyncio
async def test_concurrent_async_operations():
    """Test that multiple async operations can run concurrently."""
    test_texts = [
        "First document content. " * 50,
        "Second document content. " * 50,
        "Third document content. " * 50,
    ]
    
    start_time = asyncio.get_event_loop().time()
    
    # Run text splitting operations concurrently
    tasks = [split_text_into_chunks(text) for text in test_texts]
    results = await asyncio.gather(*tasks)
    
    end_time = asyncio.get_event_loop().time()
    
    assert len(results) == 3
    assert all(isinstance(chunks, list) for chunks in results)
    assert all(len(chunks) > 0 for chunks in results)
    print(f"Concurrent operations took {end_time - start_time:.4f} seconds")


@pytest.mark.asyncio
async def test_asyncio_to_thread_wrapper():
    """Test that asyncio.to_thread wrapper works correctly."""
    def blocking_operation():
        import time
        time.sleep(0.1)  # Simulate blocking I/O
        return "Operation completed"
    
    start_time = asyncio.get_event_loop().time()
    result = await asyncio.to_thread(blocking_operation)
    end_time = asyncio.get_event_loop().time()
    
    assert result == "Operation completed"
    assert end_time - start_time >= 0.1  # Should take at least 0.1 seconds
    print(f"Blocking operation (in thread) took {end_time - start_time:.4f} seconds")


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    async def run_tests():
        print("Running async operation tests...")
        
        try:
            await test_async_text_splitting()
            print("✓ Text splitting test passed")
        except Exception as e:
            print(f"✗ Text splitting test failed: {e}")
        
        try:
            await test_async_pdf_loading()
            print("✓ PDF loading test passed")
        except Exception as e:
            print(f"✗ PDF loading test failed: {e}")
        
        try:
            await test_concurrent_async_operations()
            print("✓ Concurrent operations test passed")
        except Exception as e:
            print(f"✗ Concurrent operations test failed: {e}")
        
        try:
            await test_asyncio_to_thread_wrapper()
            print("✓ asyncio.to_thread test passed")
        except Exception as e:
            print(f"✗ asyncio.to_thread test failed: {e}")
        
        print("All tests completed!")
    
    asyncio.run(run_tests())
