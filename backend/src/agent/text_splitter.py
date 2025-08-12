from langchain_text_splitters import RecursiveCharacterTextSplitter
import asyncio

async def split_text_into_chunks(pages):
    """Async wrapper for text splitting to avoid blocking the event loop."""
    def _split_sync():
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024, chunk_overlap=150
        )
        texts = text_splitter.split_text(pages)
        return texts
    
    return await asyncio.to_thread(_split_sync)

def split_text_into_chunks_sync(pages):
    """Synchronous version for backward compatibility."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024, chunk_overlap=150
    )
    texts = text_splitter.split_text(pages)
    return texts