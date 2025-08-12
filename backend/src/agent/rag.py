from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import asyncio
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

async def get_embeddings_batch(texts: str):
    """Async wrapper for SentenceTransformer embedding generation."""
    def _encode_sync():
        model = SentenceTransformer("intfloat/multilingual-e5-large")
        return model.encode(texts).tolist()  # Fixed typo: toList() -> tolist()
    
    return await asyncio.to_thread(_encode_sync)

async def initialize_pinecone_async():
    """Async function to initialize Pinecone index."""
    def _init_pinecone():
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = "langchain-test-index"

        if index_name not in pc.list_indexes().names():
            print("Index not found")
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        print(f"Pinecone index: {index_name} initialized")
        return pc.Index(index_name)
    
    return await asyncio.to_thread(_init_pinecone)

async def main():
    index = await initialize_pinecone_async()
    
    # Example usage:
    # embeddings = await get_embeddings_batch("Your text here")
    # print(f"Generated embeddings with shape: {len(embeddings)}")

if __name__=="__main__":
    asyncio.run(main())
