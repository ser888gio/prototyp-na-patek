from pinecone import Pinecone, ServerlessSpec
import os
import asyncio
from dotenv import load_dotenv

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
