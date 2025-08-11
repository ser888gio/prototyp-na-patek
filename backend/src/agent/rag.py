from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import asyncio
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

async def main():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "langchain-test-index"

    if index_name not in pc.list_indexes().names():
        print("Index not found")
        pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    print(f"Pinecone index: {index_name} initialized")

    #Embedding of the upcoming text. The model is Open source - Sentences Transformers. Batch embedding for faster process
    def get_embeddings_batch(texts: str):
        model = SentenceTransformer("intfloat/multilingual-e5-large")
        return model.encode(texts).toList() #pinecone wants it to be inserted as a list. Because the embeddings are a list of floats    
    

if __name__=="__main__":
    asyncio.run(main())
