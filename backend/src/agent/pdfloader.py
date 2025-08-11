from langchain_community.document_loaders import PyPDFLoader 
import asyncio

async def load_pdf(file: str):
    loader = PyPDFLoader(file_path=file)
    pages = []
    async for page in loader.alazy_load():
        if page.page_content and isinstance(page.page_content, str):
            pages.append(page.page_content)  # Extract just the text content
    return pages

if __name__=="__main__":
    pages = asyncio.run(load_pdf("./test.pdf"))