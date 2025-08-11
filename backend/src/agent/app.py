# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from queue import Queue
from threading import Thread
from fastapi import FastAPI, Response, UploadFile, File, HTTPException
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

import aiofiles

load_dotenv()

def pinecone_connector_start():

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

pinecone_connector = pinecone_connector_start()

# Define the FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

vector_store = None
retriever = None

async def initialize_vector_store():
    """Initialize the vector store with embeddings model"""
    global vector_store, retriever
    
    # Create the embedding model instance for the vector store
    embeddings_model = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2')
    
    # Get the index from the Pinecone client
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


@app.post("/uploadfilepleasefortheloveofgod/")
async def upload_file(file_upload: UploadFile = File(...)):
    global vector_store

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
        print(f"File content length: {len(file_content)} bytes")
        print(f"First 100 bytes: {file_content[:100]}")
        
        # Save to temporary file for inspection
        import tempfile
        import os
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            print(f"Temporary file saved at: {temp_file_path}")
            
            # Reset file pointer for further processing
            await file_upload.seek(0)
            
            print(f"Step 2: Initializing vector store...")
            if vector_store is None:
                await initialize_vector_store()
                print("Vector store initialized successfully")
            
            print(f"Step 3: Calling load_pdf with temp file...")
            # Load and process the PDF using the temporary file path
            pages = await load_pdf(temp_file_path)
            print(f"load_pdf returned {len(pages) if pages else 0} pages")
            
            if pages:
                print(f"First page preview (first 200 chars): {str(pages[0])[:200] if pages[0] else 'Empty'}")
            
            pages = [str(page) for page in pages if isinstance(page, str)]
            full_text = "\n\n".join(pages)
            print(f"Full text length: {len(full_text)} characters")

            print(f"Step 4: Splitting text into chunks...")
            chunks = split_text_into_chunks(full_text)
            print(f"Created {len(chunks)} chunks")

            if vector_store and chunks:
                print(f"Step 5: Adding chunks to vector store...")
                vector_store.add_texts(chunks)
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
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
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

@app.post("/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}

# Simple test endpoint for file upload without PDF processing
@app.post("/test-upload/")
async def test_upload(file_upload: UploadFile = File(...)):
    print(f"TEST UPLOAD: Received {file_upload.filename}")
    try:
        content = await file_upload.read()
        return {
            "filename": file_upload.filename,
            "size": len(content),
            "content_type": file_upload.content_type,
            "status": "success",
            "message": "File received successfully without processing"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error: {str(e)}"
        }