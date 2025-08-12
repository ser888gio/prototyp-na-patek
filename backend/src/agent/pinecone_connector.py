from pinecone import Pinecone, ServerlessSpec
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def get_pinecone_client():
    """Async function to get Pinecone client and initialize index."""
    def _init_pinecone():
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        index_name = "langchain-test-index"  # change if desired

        if not pc.has_index(index_name):
            pc.create_index(
                name=index_name,
                dimension=1024,  # Changed to match HuggingFace all-MiniLM-L12-v2 model
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        index = pc.Index(index_name)
        return pc, index
    
    return await asyncio.to_thread(_init_pinecone)

# For backward compatibility, maintain the sync version
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = "langchain-test-index"  # change if desired

if not pc.has_index(index_name):
    pc.create_index(
        name=index_name,
        dimension=1024,  # Changed to match HuggingFace all-MiniLM-L12-v2 model
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(index_name)