from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader
)

# Import optional dependencies with fallbacks
try:
    from langchain_community.document_loaders import Docx2txtLoader
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: docx2txt not available. Word document support disabled.")

try:
    from langchain_community.document_loaders import UnstructuredPowerPointLoader
    POWERPOINT_AVAILABLE = True
except ImportError:
    POWERPOINT_AVAILABLE = False
    print("Warning: unstructured PowerPoint loader not available. PowerPoint support disabled.")

try:
    from langchain_community.document_loaders import UnstructuredExcelLoader
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("Warning: unstructured Excel loader not available. Excel support disabled.")

import asyncio
import os
from pathlib import Path
from typing import List, Optional
import mimetypes


class DocumentLoader:
    """
    A comprehensive document loader that supports multiple file formats:
    - PDF files (.pdf)
    - Word documents (.docx, .doc)
    - PowerPoint presentations (.pptx, .ppt)
    - Excel spreadsheets (.xlsx, .xls)
    - Plain text files (.txt, .md, .csv)
    """
    
    # Define supported file extensions and their corresponding loaders
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'docx',
        '.pptx': 'powerpoint',
        '.ppt': 'powerpoint', 
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.txt': 'text',
        '.md': 'text',
        '.csv': 'text',
        '.log': 'text',
        '.json': 'text',
        '.xml': 'text',
        '.html': 'text',
        '.htm': 'text'
    }

    @staticmethod
    def get_file_type(file_path: str) -> Optional[str]:
        """
        Determine the file type based on extension and MIME type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type string or None if not supported
        """
        # Get extension from file path
        extension = Path(file_path).suffix.lower()
        
        # Check if extension is supported
        if extension in DocumentLoader.SUPPORTED_EXTENSIONS:
            return DocumentLoader.SUPPORTED_EXTENSIONS[extension]
        
        # Fallback to MIME type detection
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith('text/'):
                return 'text'
            elif mime_type == 'application/pdf':
                return 'pdf'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/msword']:
                return 'docx'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.presentationml.presentation',
                              'application/vnd.ms-powerpoint']:
                return 'powerpoint'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                              'application/vnd.ms-excel']:
                return 'excel'
        
        return None

    @staticmethod
    async def load_pdf(file_path: str) -> List[str]:
        """Load PDF document and return text content."""
        print(f"Loading PDF: {file_path}")
        loader = PyPDFLoader(file_path=file_path)
        pages = []
        
        async for page in loader.alazy_load():
            if hasattr(page, 'page_content') and page.page_content:
                if isinstance(page.page_content, str):
                    pages.append(page.page_content)
        
        return pages

    @staticmethod
    async def load_docx(file_path: str) -> List[str]:
        """Load Word document and return text content."""
        if not DOCX_AVAILABLE:
            raise ValueError("Word document support not available. Please install docx2txt: pip install docx2txt")
        
        print(f"Loading Word document: {file_path}")
        
        def _load_docx_sync():
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            return [doc.page_content for doc in documents if hasattr(doc, 'page_content')]
        
        return await asyncio.to_thread(_load_docx_sync)

    @staticmethod
    async def load_powerpoint(file_path: str) -> List[str]:
        """Load PowerPoint presentation and return text content."""
        if not POWERPOINT_AVAILABLE:
            raise ValueError("PowerPoint support not available. Please install unstructured: pip install unstructured")
        
        print(f"Loading PowerPoint presentation: {file_path}")
        
        def _load_ppt_sync():
            loader = UnstructuredPowerPointLoader(file_path)
            documents = loader.load()
            return [doc.page_content for doc in documents if hasattr(doc, 'page_content')]
        
        return await asyncio.to_thread(_load_ppt_sync)

    @staticmethod
    async def load_excel(file_path: str) -> List[str]:
        """Load Excel spreadsheet and return text content."""
        if not EXCEL_AVAILABLE:
            raise ValueError("Excel support not available. Please install unstructured: pip install unstructured")
        
        print(f"Loading Excel spreadsheet: {file_path}")
        
        def _load_excel_sync():
            loader = UnstructuredExcelLoader(file_path)
            documents = loader.load()
            return [doc.page_content for doc in documents if hasattr(doc, 'page_content')]
        
        return await asyncio.to_thread(_load_excel_sync)

    @staticmethod
    async def load_text(file_path: str) -> List[str]:
        """Load text file and return content."""
        print(f"Loading text file: {file_path}")
        
        def _load_text_sync():
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            return [doc.page_content for doc in documents if hasattr(doc, 'page_content')]
        
        return await asyncio.to_thread(_load_text_sync)


async def load_document(file_path: str) -> List[str]:
    """
    Main function to load any supported document type.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        List of text content from the document
        
    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file doesn't exist
    """
    print(f"=== load_document DEBUG START ===")
    print(f"Input file_path: {file_path}")
    
    # Validate input
    if not isinstance(file_path, str):
        print(f"ERROR: file_path is not a string, it's {type(file_path)}")
        raise ValueError(f"file_path must be a string, got {type(file_path)}")
    
    # Check if file exists
    file_exists = await asyncio.to_thread(os.path.exists, file_path)
    print(f"File exists: {file_exists}")
    
    if not file_exists:
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get file size for logging
    file_size = await asyncio.to_thread(os.path.getsize, file_path)
    print(f"File size: {file_size} bytes")
    
    # Determine file type
    file_type = DocumentLoader.get_file_type(file_path)
    print(f"Detected file type: {file_type}")
    
    if not file_type:
        supported_exts = list(DocumentLoader.SUPPORTED_EXTENSIONS.keys())
        raise ValueError(f"Unsupported file type. Supported extensions: {supported_exts}")
    
    try:
        # Load document based on type
        if file_type == 'pdf':
            pages = await DocumentLoader.load_pdf(file_path)
        elif file_type == 'docx':
            pages = await DocumentLoader.load_docx(file_path)
        elif file_type == 'powerpoint':
            pages = await DocumentLoader.load_powerpoint(file_path)
        elif file_type == 'excel':
            pages = await DocumentLoader.load_excel(file_path)
        elif file_type == 'text':
            pages = await DocumentLoader.load_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        print(f"=== load_document DEBUG END ===")
        print(f"Total pages/sections processed: {len(pages)}")
        print(f"Content preview: {pages[0][:200] if pages else 'No content'}")
        
        return pages
        
    except Exception as e:
        print(f"=== load_document ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Full traceback:")
        traceback.print_exc()
        print(f"=== load_document ERROR END ===")
        raise


# Backward compatibility - keep the original function name
async def load_pdf(file_path: str) -> List[str]:
    """
    Backward compatibility function for PDF loading.
    This maintains compatibility with existing code.
    """
    return await load_document(file_path)


if __name__ == "__main__":
    # Test the document loader
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        pages = asyncio.run(load_document(test_file))
        print(f"Loaded {len(pages)} pages/sections")
        for i, page in enumerate(pages[:3]):  # Show first 3 pages
            print(f"Page {i+1}: {page[:200]}...")
    else:
        print("Usage: python document_loader.py <file_path>")
