# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from fastapi import FastAPI, Response, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent.document_loader import load_document
from agent.text_splitter import split_text_into_chunks
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from agent.pinecone_connector import pinecone_connector_start
from agent.reranker import get_reranker
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Initialize pinecone connector as a coroutine that will be awaited when needed
async def get_pinecone_connector():
    return await pinecone_connector_start()

# Define the FastAPI app
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}


# Add a simple health check endpoint for testing
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/vector-store/status")
async def vector_store_status():
    """Check the status of the vector store"""
    global vector_store, retriever
    
    try:
        print(f"========== VECTOR STORE STATUS CHECK ==========")
        
        if vector_store is None:
            print(f"❌ Vector store: NOT INITIALIZED")
            return {
                "status": "not_initialized",
                "message": "Vector store not initialized"
            }
        
        print(f"✅ Vector store: INITIALIZED")
        print(f"   Type: {type(vector_store).__name__}")
        
        if retriever is None:
            print(f"❌ Retriever: NOT AVAILABLE")
        else:
            print(f"✅ Retriever: AVAILABLE")
            print(f"   Type: {type(retriever).__name__}")
            
        # Try to get some basic info about the vector store
        print(f"========== END STATUS CHECK ==========")
        
        return {
            "status": "initialized",
            "message": "Vector store is ready",
            "retriever_available": retriever is not None,
            "vector_store_type": type(vector_store).__name__
        }
    except Exception as e:
        print(f"❌ Error checking vector store: {str(e)}")
        return {
            "status": "error",
            "message": f"Error checking vector store: {str(e)}"
        }

@app.get("/vector-store/info")
async def vector_store_info():
    """Get detailed information about what's stored in the vector store"""
    global vector_store, retriever
    
    try:
        print(f"========== VECTOR STORE INFO REQUEST ==========")
        
        if vector_store is None:
            print(f"❌ Vector store not initialized")
            return {
                "status": "not_initialized",
                "message": "Vector store not initialized"
            }
        
        # Try to get some sample documents to show what's stored
        sample_queries = ["", "document", "text", "content", "information"]
        stored_content_info = []
        
        for query in sample_queries:
            try:
                if retriever:
                    docs = await asyncio.to_thread(
                        retriever.get_relevant_documents, 
                        query if query else "sample"
                    )
                    
                    if docs:
                        print(f"Query '{query}' returned {len(docs)} documents")
                        for i, doc in enumerate(docs[:2]):  # Show first 2 docs
                            content_info = {
                                "query_used": query,
                                "document_index": i,
                                "content_length": len(doc.page_content),
                                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                                "metadata": doc.metadata,
                                "has_score": hasattr(doc, 'score')
                            }
                            stored_content_info.append(content_info)
                            print(f"  Found content: {content_info['content_length']} chars, metadata: {content_info['metadata']}")
                        break  # Stop after finding some content
                    else:
                        print(f"Query '{query}' returned no documents")
                        
            except Exception as e:
                print(f"Error querying with '{query}': {e}")
                continue
        
        print(f"========== END VECTOR STORE INFO ==========")
        
        return {
            "status": "success",
            "vector_store_type": type(vector_store).__name__,
            "retriever_available": retriever is not None,
            "sample_content": stored_content_info,
            "total_samples_found": len(stored_content_info)
        }
        
    except Exception as e:
        print(f"❌ Error getting vector store info: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting vector store info: {str(e)}"
        }

vector_store = None
retriever = None

async def initialize_vector_store():
    """Initialize the vector store with embeddings model"""
    global vector_store, retriever
    
    print(f"========== INITIALIZING VECTOR STORE ==========")
    print(f"Loading HuggingFace embeddings model: sentence-transformers/all-MiniLM-L12-v2")
    
    # Wrap the embedding model creation in asyncio.to_thread
    embeddings_model = await asyncio.to_thread(
        HuggingFaceEmbeddings, 
        model_name='sentence-transformers/all-MiniLM-L12-v2'
    )
    print(f"✅ Embeddings model loaded successfully")
    
    print(f"Connecting to Pinecone...")
    # Get the Pinecone client and index
    pinecone_connector = await get_pinecone_connector()
    index = pinecone_connector.Index("langchain-test-index")
    print(f"✅ Connected to Pinecone index: langchain-test-index")
    
    # Create the vector store with the Pinecone index
    vector_store = PineconeVectorStore(
        index=index, 
        embedding=embeddings_model
    )
    print(f"✅ Vector store created: {type(vector_store).__name__}")
    
    # Create retriever with higher k for initial retrieval (before re-ranking)
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 10, "score_threshold": 0.3},  # Get more docs with lower threshold for re-ranking
    )
    print(f"✅ Retriever created with config:")
    print(f"   - search_type: similarity_score_threshold")
    print(f"   - k (max results): 10 (for initial retrieval before re-ranking)")
    print(f"   - score_threshold: 0.3 (lowered for broader initial retrieval)")
    print(f"========== VECTOR STORE INITIALIZATION COMPLETE ==========\n")
    
    return vector_store


@app.post("/query/")
async def query_documents(request: Request):
    """Query the vector database for relevant documents"""
    global vector_store, retriever
    
    try:
        # Parse the request body
        body = await request.json()
        query_text = body.get("query", "").strip()
        
        if not query_text:
            return {
                "status": "error",
                "message": "Query text is required"
            }
        
        print(f"========== QUERY DEBUG START ==========")
        print(f"Received query: {query_text}")
        
        # Initialize vector store if not already done
        if vector_store is None:
            print("Initializing vector store...")
            await initialize_vector_store()
            print("Vector store initialized")
        
        if retriever is None:
            print("ERROR: Retriever not available")
            return {
                "status": "error",
                "message": "Vector database not properly initialized"
            }
        
        # Perform the search using the retriever
        print("Performing similarity search...")
        relevant_docs = await asyncio.to_thread(
            retriever.get_relevant_documents, 
            query_text
        )
        
        print(f"========== VECTOR STORE RETRIEVAL RESULTS ==========")
        print(f"Query: '{query_text}'")
        print(f"Found {len(relevant_docs)} relevant documents")
        print(f"Retriever config: search_type=similarity_score_threshold, k=10, score_threshold=0.3")
        
        # Apply re-ranking to improve relevance
        print(f"========== APPLYING RE-RANKING ==========")
        reranker = await get_reranker("hybrid")  # Use hybrid re-ranker
        reranked_results = await reranker.rerank_documents(
            query=query_text,
            documents=relevant_docs,
            top_k=5  # Keep top 5 after re-ranking for API endpoint
        )
        
        print(f"Re-ranking complete. Final results: {len(reranked_results)} documents")
        
        # Format the results and print detailed information using re-ranked documents
        results = []
        for i, (doc, relevance_score) in enumerate(reranked_results):
            print(f"\n--- Re-ranked Document {i+1} ---")
            print(f"Content length: {len(doc.page_content)} characters")
            print(f"Metadata: {doc.metadata}")
            print(f"Re-ranking relevance score: {relevance_score:.4f}")
            
            # Preserve original similarity score if available
            original_score = getattr(doc, 'score', None)
            if original_score is not None:
                print(f"Original similarity score: {original_score}")
                
            print(f"Content preview (first 300 chars): {doc.page_content[:300]}...")
            if len(doc.page_content) > 300:
                print(f"Content preview (last 100 chars): ...{doc.page_content[-100:]}")
            
            results.append({
                "id": i,
                "content": doc.page_content,
                "metadata": doc.metadata,
                "original_score": original_score,
                "relevance_score": relevance_score
            })
        
        print(f"========== END RETRIEVAL RESULTS ==========\n")
        
        print("========== QUERY SUCCESS ==========")
        return {
            "status": "success",
            "query": query_text,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        print(f"========== QUERY ERROR ==========")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Full traceback:")
        traceback.print_exc()
        print(f"========== ERROR END ==========")
        
        return {
            "status": "error",
            "message": f"Error querying documents: {str(e)}"
        }


@app.post("/uploadfile/")
async def upload_file(request: Request):
    """
    Upload and process multiple document files.
    Supports: PDF, Word, PowerPoint, Excel, and text files.
    
    This endpoint handles both FastAPI UploadFile format and multipart form data
    to avoid blocking operations while maintaining compatibility.
    """
    global vector_store
    
    print(f"========== UPLOAD DEBUG START ==========")
    print(f"Received file upload request")
    
    try:
        # Try to get files from multipart form without causing blocking operations
        form = await request.form()
        print("Form keys:", list(form.keys()))
        
        # Collect all files from the form
        uploaded_files = []
        
        # Method 1: Check for FastAPI UploadFile format (files)
        if 'files' in form:
            files_data = form.getlist('files')
            for file_data in files_data:
                if hasattr(file_data, 'filename') and file_data.filename:
                    uploaded_files.append(file_data)
        
        # Method 2: Check for old format (file_upload, file_upload_0, etc.)
        if not uploaded_files:
            # Check for single file upload (backward compatibility)
            single_file = form.get("file_upload")
            if single_file and hasattr(single_file, 'filename') and single_file.filename:
                uploaded_files.append(single_file)
            
            # Check for multiple file uploads (file_upload_0, file_upload_1, etc.)
            for key in form.keys():
                if key.startswith("file_upload_") and key != "file_upload":
                    file = form.get(key)
                    if file and hasattr(file, 'filename') and file.filename:
                        uploaded_files.append(file)
        
        print(f"Number of files: {len(uploaded_files)}")
        
        if not uploaded_files:
            print("ERROR: No files received")
            return {
                "status": "error",
                "message": "No files received"
            }
        
        # Process each file
        results = []
        total_chunks = 0
        total_pages = 0
        errors = []
        
        for i, file_upload in enumerate(uploaded_files):
            print(f"\n--- Processing file {i+1}/{len(uploaded_files)}: {file_upload.filename} ---")
            print(f"Content type: {file_upload.content_type}")
            print(f"File size: {file_upload.size if hasattr(file_upload, 'size') else 'Unknown'}")
            
            try:
                print(f"Step 1: Reading file content...")
                # Read the file content
                file_content = await file_upload.read()
                
                # Save to temporary file for inspection  
                import tempfile
                import os
                from pathlib import Path
                temp_file_path = None
                try:
                    # Use asyncio.to_thread for file operations to avoid blocking
                    async def create_temp_file_async(content, original_filename):
                        # Get the original file extension to preserve file type
                        original_extension = Path(original_filename).suffix if original_filename else '.txt'
                        
                        def _create_temp():
                            # Use a known temp directory to avoid getcwd() calls
                            import platform
                            if platform.system() == "Windows":
                                temp_dir = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\temp'))
                            else:
                                temp_dir = '/tmp'
                            
                            # Ensure temp directory exists
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=original_extension, dir=temp_dir) as temp_file:
                                temp_file.write(content)
                                return temp_file.name
                        
                        return await asyncio.to_thread(_create_temp)
                    
                    temp_file_path = await create_temp_file_async(file_content, file_upload.filename)
                except Exception as e:
                    return e
                print(f"Temporary file saved at: {temp_file_path}")
                
                print(f"Step 2: Initializing vector store...")
                if vector_store is None:
                    await initialize_vector_store()
                    print("Vector store initialized successfully")
                
                print(f"Step 3: Calling load_document with temp file...")
                # Load and process the document using the async function directly
                pages = await load_document(temp_file_path)
                print(f"load_document returned {len(pages) if pages else 0} pages")
                
                if pages:
                    print(f"First page preview (first 200 chars): {str(pages[0])[:200] if pages[0] else 'Empty'}")
                
                pages = [str(page) for page in pages if isinstance(page, str)]
                full_text = "\n\n".join(pages)
                print(f"Full text length: {len(full_text)} characters")

                print(f"Step 4: Splitting text into chunks...")
                # Call the async function directly since it already handles threading
                chunks = await split_text_into_chunks(full_text)
                print(f"Created {len(chunks)} chunks")
                print(f"========== CHUNK ANALYSIS ==========")
                for j, chunk in enumerate(chunks[:3]):  # Show first 3 chunks as examples
                    print(f"Chunk {j+1} (length: {len(chunk)} chars): {chunk[:200]}...")
                if len(chunks) > 3:
                    print(f"... and {len(chunks) - 3} more chunks")
                print(f"========== END CHUNK ANALYSIS ==========")

                if vector_store and chunks:
                    print(f"Step 5: Adding chunks to vector store...")
                    print(f"Vector store type: {type(vector_store).__name__}")
                    print(f"Number of chunks to add: {len(chunks)}")
                    
                    # Wrap vector store operations in asyncio.to_thread
                    await asyncio.to_thread(vector_store.add_texts, chunks)
                    print(f"✅ Successfully added {len(chunks)} chunks to vector store")
                    print(f"Each chunk will be embedded and stored for future retrieval")
                else:
                    if not vector_store:
                        print(f"❌ Vector store not available - chunks not added")
                    if not chunks:
                        print(f"❌ No chunks created - nothing to add to vector store")

                # Add to results
                results.append({
                    "filename": file_upload.filename,
                    "status": "success",
                    "pages_processed": len(pages),
                    "chunks_created": len(chunks)
                })
                
                total_pages += len(pages)
                total_chunks += len(chunks)
                
            finally:
                # Clean up temporary file using async thread wrapper
                if temp_file_path:
                    await asyncio.to_thread(lambda: os.path.exists(temp_file_path) and os.unlink(temp_file_path))
                    print(f"Cleaned up temporary file: {temp_file_path}")
                    
            print(f"========== UPLOAD ERROR FOR {file_upload.filename} ==========")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print(f"Full traceback:")
            traceback.print_exc()
            print(f"========== ERROR END ==========")
            
            error_msg = f"Error processing {file_upload.filename}: {str(e)}"
            errors.append(error_msg)
            results.append({
                "filename": file_upload.filename,
                "status": "error",
                "message": str(e)
            })
    except Exception as e:
        return e

    print("========== UPLOAD SUMMARY ==========")
    successful_files = [r for r in results if r["status"] == "success"]
    failed_files = [r for r in results if r["status"] == "error"]
    
    print(f"Total files processed: {len(uploaded_files)}")
    print(f"Successful: {len(successful_files)}")
    print(f"Failed: {len(failed_files)}")
    print(f"Total pages: {total_pages}")
    print(f"Total chunks: {total_chunks}")
    
    # Return comprehensive response
    if len(successful_files) == len(uploaded_files):
        # All files successful
        return {
            "status": "success",
            "message": f"Successfully processed {len(uploaded_files)} file(s)",
            "files_processed": len(uploaded_files),
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "results": results
        }
    elif len(successful_files) > 0:
        # Partial success
        return {
            "status": "partial_success",
            "message": f"Processed {len(successful_files)} out of {len(uploaded_files)} files successfully",
            "files_processed": len(successful_files),
            "files_failed": len(failed_files),
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "results": results,
            "errors": errors
        }
    else:
        # All files failed
        return {
            "status": "error",
            "message": f"Failed to process all {len(uploaded_files)} file(s)",
            "files_failed": len(failed_files),
            "results": results,
            "errors": errors
        }

