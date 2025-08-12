from langchain_community.document_loaders import PyPDFLoader 
import asyncio
import os

async def load_pdf(file_path: str):
    print(f"=== load_pdf DEBUG START ===")
    print(f"Input file_path: {file_path}")
    
    # Wrap blocking os operations in asyncio.to_thread
    if not isinstance(file_path, str):
        print(f"ERROR: file_path is not a string, it's {type(file_path)}")
        raise ValueError(f"file_path must be a string, got {type(file_path)}")
    
    file_exists = await asyncio.to_thread(os.path.exists, file_path)
    print(f"File exists: {file_exists}")
    
    if file_exists:
        file_size = await asyncio.to_thread(os.path.getsize, file_path)
        print(f"File size: {file_size} bytes")
    
    try:
        print(f"Creating PyPDFLoader...")
        loader = PyPDFLoader(file_path=file_path)
        print(f"PyPDFLoader created successfully")
        
        pages = []
        page_count = 0
        
        print(f"Starting to load pages...")
        async for page in loader.alazy_load():
            page_count += 1
            print(f"Processing page {page_count}")
            print(f"Page type: {type(page)}")
            print(f"Page content type: {type(page.page_content) if hasattr(page, 'page_content') else 'No page_content attr'}")
            
            if hasattr(page, 'page_content') and page.page_content:
                content_preview = str(page.page_content)[:200]
                print(f"Page {page_count} content preview: {content_preview}")
                
                if isinstance(page.page_content, str):
                    pages.append(page.page_content)  # Extract just the text content
                    print(f"Added page {page_count} to results")
                else:
                    print(f"WARNING: Page {page_count} content is not a string: {type(page.page_content)}")
            else:
                print(f"WARNING: Page {page_count} has no content or empty content")
        
        print(f"=== load_pdf DEBUG END ===")
        print(f"Total pages processed: {page_count}")
        print(f"Pages with content: {len(pages)}")
        return pages
        
    except Exception as e:
        print(f"=== load_pdf ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Full traceback:")
        traceback.print_exc()
        print(f"=== load_pdf ERROR END ===")
        raise  # Re-raise the exception

if __name__=="__main__":
    pages = asyncio.run(load_pdf("./test.pdf"))