"""
Test async functionality in the backend application.
This file tests the async/await patterns implemented throughout the codebase.
"""
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from agent.text_splitter import split_text_into_chunks
    from agent.pinecone_connector import get_pinecone_client
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the backend directory")
    print("and that the agent modules are properly installed")
    sys.exit(1)


async def test_text_splitter():
    """Test the async text splitter."""
    print("Testing async text splitter...")
    
    test_text = """
    This is a test document for the async text splitter functionality.
    It contains multiple sentences and paragraphs to ensure proper chunking.
    The text splitter should create meaningful chunks from this content.
    Each chunk should be of appropriate size and have proper overlap.
    """ * 10  # Make it longer to get multiple chunks
    
    try:
        start_time = asyncio.get_event_loop().time()
        chunks = await split_text_into_chunks(test_text)
        end_time = asyncio.get_event_loop().time()
        
        print(f"✓ Text splitter completed in {end_time - start_time:.4f} seconds")
        print(f"✓ Created {len(chunks)} chunks")
        print(f"✓ First chunk preview: {chunks[0][:100]}...")
        return True
    except Exception as e:
        print(f"✗ Text splitter failed: {e}")
        return False


async def test_pinecone_connection():
    """Test the async Pinecone connection."""
    print("Testing async Pinecone connection...")
    
    try:
        start_time = asyncio.get_event_loop().time()
        pc, index = await get_pinecone_client()
        end_time = asyncio.get_event_loop().time()
        
        print(f"✓ Pinecone connection completed in {end_time - start_time:.4f} seconds")
        print(f"✓ Connected to Pinecone client: {type(pc).__name__}")
        print(f"✓ Got index: {type(index).__name__}")
        return True
    except Exception as e:
        print(f"✗ Pinecone connection failed: {e}")
        return False


async def test_concurrent_operations():
    """Test running multiple async operations concurrently."""
    print("Testing concurrent async operations...")
    
    test_texts = [
        "First test document. " * 20,
        "Second test document. " * 20,
        "Third test document. " * 20,
    ]
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Run all text splitting operations concurrently
        tasks = [split_text_into_chunks(text) for text in test_texts]
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        
        print(f"✓ Concurrent operations completed in {end_time - start_time:.4f} seconds")
        print(f"✓ Processed {len(results)} documents concurrently")
        print(f"✓ Total chunks created: {sum(len(chunks) for chunks in results)}")
        return True
    except Exception as e:
        print(f"✗ Concurrent operations failed: {e}")
        return False


async def test_asyncio_to_thread():
    """Test asyncio.to_thread functionality."""
    print("Testing asyncio.to_thread wrapper...")
    
    def blocking_operation():
        import time
        time.sleep(0.1)  # Simulate a blocking I/O operation
        return "Blocking operation completed successfully"
    
    try:
        start_time = asyncio.get_event_loop().time()
        result = await asyncio.to_thread(blocking_operation)
        end_time = asyncio.get_event_loop().time()
        
        print(f"✓ asyncio.to_thread completed in {end_time - start_time:.4f} seconds")
        print(f"✓ Result: {result}")
        return True
    except Exception as e:
        print(f"✗ asyncio.to_thread failed: {e}")
        return False


async def main():
    """Run all async tests."""
    print("=" * 60)
    print("ASYNC FUNCTIONALITY TESTS")
    print("=" * 60)
    
    tests = [
        ("Text Splitter", test_text_splitter),
        ("Pinecone Connection", test_pinecone_connection),
        ("Concurrent Operations", test_concurrent_operations),
        ("asyncio.to_thread", test_asyncio_to_thread),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Async functionality is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    # Run the async tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)