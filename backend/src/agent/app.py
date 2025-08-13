# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from fastapi import FastAPI, Response, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
import boto3
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from agent.pdfloader import load_pdf
from agent.text_splitter import split_text_into_chunks
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def pinecone_connector_start():
    # Wrap Pinecone operations in asyncio.to_thread to avoid blocking
    def _create_pinecone_client():
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        index_name = "langchain-test-index"  # change if desired

        if not pc.has_index(index_name):
            pc.create_index(
                name=index_name,
                dimension=384,  # Changed to match HuggingFace all-MiniLM-L12-v2 model
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        index = pc.Index(index_name)
        return pc  # Return the Pinecone client
    
    return await asyncio.to_thread(_create_pinecone_client)

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


class Filelike:
    def __init__(self, q):
        self.q = q
    
    def read(self, size=-1):
        result = b""
        while True:
            chunk = self.q.get()
            if chunk is None:
                break
            result += chunk
            if size != -1 and len(result) >= size:
                # Return exactly 'size' bytes, put remainder back in queue
                if len(result) > size:
                    remainder = result[size:]
                    self.q.put(remainder)
                    result = result[:size]
                break
        return result

R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCOUNT_ID=os.getenv("R2_ACCOUNT_ID")

s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="eeur"
)

def upload_to_r2(file_, bucket, key):
    # Configure R2 client
    r2 = boto3.client(
        's3',
        endpoint_url=f'https://{os.getenv("R2_ACCOUNT_ID")}.r2.cloudflarestorage.com',
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        region_name='eeur'  # R2 uses 'auto' for region
    )
    
    try:
        r2.upload_fileobj(file_, bucket, key)
        print(f"Successfully uploaded {key} to R2 bucket {bucket}")
    except Exception as e:
        print(f"Error uploading to R2: {e}")
        raise


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

# Add a test endpoint that doesn't require file upload
@app.post("/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}

@app.get("/vector-store/status")
async def vector_store_status():
    """Check the status of the vector store"""
    global vector_store, retriever
    
    try:
        if vector_store is None:
            return {
                "status": "not_initialized",
                "message": "Vector store not initialized"
            }
        
        # Try to get some basic info about the vector store
        return {
            "status": "initialized",
            "message": "Vector store is ready",
            "retriever_available": retriever is not None,
            "vector_store_type": type(vector_store).__name__
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking vector store: {str(e)}"
        }

@app.get("/debug/langgraph")
async def debug_langgraph():
    """Debug endpoint to test LangGraph integration"""
    try:
        # Test if we can access the graph
        from agent.graph import graph
        return {
            "status": "success",
            "message": "LangGraph is accessible",
            "graph_name": graph.name if hasattr(graph, 'name') else "unknown"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"LangGraph error: {str(e)}"
        }

vector_store = None
retriever = None

async def initialize_vector_store():
    """Initialize the vector store with embeddings model"""
    global vector_store, retriever
    
    # Wrap the embedding model creation in asyncio.to_thread
    embeddings_model = await asyncio.to_thread(
        HuggingFaceEmbeddings, 
        model_name='sentence-transformers/all-MiniLM-L12-v2'
    )
    
    # Get the Pinecone client and index
    pinecone_connector = await get_pinecone_connector()
    index = pinecone_connector.Index("langchain-test-index")
    
    # Create the vector store with the Pinecone index
    vector_store = PineconeVectorStore(
        index=index, 
        embedding=embeddings_model
    )
    
    # Create retriever
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 3, "score_threshold": 0.4},
    )
    
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
        
        print(f"Found {len(relevant_docs)} relevant documents")
        
        # Format the results
        results = []
        for i, doc in enumerate(relevant_docs):
            results.append({
                "id": i,
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": getattr(doc, 'score', None)  # Some retrievers include scores
            })
            print(f"Document {i} preview: {doc.page_content[:200]}...")
        
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
    global vector_store
    
    form = await request.form()
    print("Form keys:", form.keys())
    file_upload = form.get("file_upload")

    print(f"========== UPLOAD DEBUG START ==========")
    print(f"Received file upload request")
    print(f"File name: {file_upload.filename}")
    print(f"Content type: {file_upload.content_type}")
    print(f"File size: {file_upload.size if hasattr(file_upload, 'size') else 'Unknown'}")
    
    try: 
        if not file_upload or not file_upload.filename:
            print("ERROR: No file received")
            return{
                "status": "error",
                "message": "No file received"
            }
    
        print(f"Step 1: Reading file content...")
        # Read the file content
        file_content = await file_upload.read()
        
        # Save to temporary file for inspection
        import tempfile
        import os
        temp_file_path = None
        try:
            # Use asyncio.to_thread for file operations to avoid blocking
            def create_temp_file(content):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(content)
                    return temp_file.name
            
            temp_file_path = await asyncio.to_thread(create_temp_file, file_content)
            print(f"Temporary file saved at: {temp_file_path}")
            
            print(f"Step 2: Initializing vector store...")
            if vector_store is None:
                await initialize_vector_store()
                print("Vector store initialized successfully")
            
            print(f"Step 3: Calling load_pdf with temp file...")
            # Load and process the PDF using the async function directly
            pages = await load_pdf(temp_file_path)
            print(f"load_pdf returned {len(pages) if pages else 0} pages")
            
            if pages:
                print(f"First page preview (first 200 chars): {str(pages[0])[:200] if pages[0] else 'Empty'}")
            
            pages = [str(page) for page in pages if isinstance(page, str)]
            full_text = "\n\n".join(pages)
            print(f"Full text length: {len(full_text)} characters")

            print(f"Step 4: Splitting text into chunks...")
            # Call the async function directly since it already handles threading
            chunks = await split_text_into_chunks(full_text)
            print(f"Created {len(chunks)} chunks")

            if vector_store and chunks:
                print(f"Step 5: Adding chunks to vector store...")
                # Wrap vector store operations in asyncio.to_thread
                await asyncio.to_thread(vector_store.add_texts, chunks)
                print(f"Added {len(chunks)} chunks to vector store")

            print("========== UPLOAD SUCCESS ==========")
            return {
                "filename": file_upload.filename,
                "status": "success",
                "pages_processed": len(pages),
                "chunks_created": len(chunks),
                "message": f"PDF processed and {len(chunks)} chunks added to vector store"
            }
            
        finally:
            # Clean up temporary file using async thread wrapper
            if temp_file_path:
                await asyncio.to_thread(lambda: os.path.exists(temp_file_path) and os.unlink(temp_file_path))
                print(f"Cleaned up temporary file: {temp_file_path}")
                
    except Exception as e:
        print(f"========== UPLOAD ERROR ==========")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Full traceback:")
        traceback.print_exc()
        print(f"========== ERROR END ==========")
        
        return {
            "filename": file_upload.filename if file_upload else "unknown",
            "status": "error",
            "message": f"Error processing file: {str(e)}"
        }

