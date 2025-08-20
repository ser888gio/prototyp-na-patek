# Multi-Format Document Support

This RAG system now supports multiple document formats beyond PDFs. The enhanced document loader can process various file types and extract text content for vector indexing and retrieval.

## Supported Document Types

### 📄 PDF Documents
- **Extensions**: `.pdf`
- **Library**: PyPDFLoader (LangChain Community)
- **Features**: Full text extraction, page-by-page processing

### 📝 Microsoft Word Documents  
- **Extensions**: `.docx`, `.doc`
- **Library**: Docx2txtLoader (LangChain Community + docx2txt)
- **Features**: Text extraction, formatting preservation
- **Dependencies**: `docx2txt`

### 📊 Microsoft PowerPoint Presentations
- **Extensions**: `.pptx`, `.ppt` 
- **Library**: UnstructuredPowerPointLoader (LangChain Community + unstructured)
- **Features**: Slide text extraction, title and content extraction
- **Dependencies**: `unstructured`

### 📈 Microsoft Excel Spreadsheets
- **Extensions**: `.xlsx`, `.xls`
- **Library**: UnstructuredExcelLoader (LangChain Community + unstructured)
- **Features**: Cell content extraction, sheet processing
- **Dependencies**: `unstructured`, `openpyxl`

### 📄 Plain Text Files
- **Extensions**: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.html`, `.htm`, `.log`
- **Library**: TextLoader (LangChain Community)
- **Features**: UTF-8 encoding support, full text extraction

## Usage

### Backend Usage

```python
from agent.document_loader import load_document

# Load any supported document type
pages = await load_document("/path/to/document.docx")
print(f"Loaded {len(pages)} pages/sections")
```

### File Type Detection

The system automatically detects file types based on:
1. File extension
2. MIME type (fallback)

```python
from agent.document_loader import DocumentLoader

file_type = DocumentLoader.get_file_type("document.docx")
print(f"File type: {file_type}")  # Output: docx
```

### Frontend Integration

The upload component now accepts multiple file types:

```tsx
<input 
  type="file" 
  accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.txt,.md,.csv,.json,.xml,.html,.htm,.log"
  multiple 
/>
```

## Dependencies

Add these dependencies to your `pyproject.toml`:

```toml
dependencies = [
    # Core dependencies
    "langchain>=0.3.19",
    "langchain-community",
    
    # Document processing
    "docx2txt>=0.8",              # Word documents
    "unstructured>=0.10.0",       # PowerPoint and Excel  
    "openpyxl>=3.0.0",           # Excel files
    "pandas>=2.0.0",             # Data processing
]
```

## Installation

```bash
# Install document processing dependencies
pip install docx2txt unstructured openpyxl pandas

# Or install from requirements
pip install -e .
```

## Error Handling

The system gracefully handles missing dependencies:

- If `docx2txt` is not installed, Word document support is disabled
- If `unstructured` is not installed, PowerPoint and Excel support is disabled  
- PDF and text file support is always available (core LangChain dependencies)

## File Size Considerations

- **Text files**: Very fast processing
- **PDFs**: Fast processing, page-by-page
- **Word documents**: Medium processing time  
- **PowerPoint**: Medium processing time (depends on slide count)
- **Excel**: Processing time varies by sheet size and complexity

## Testing

Test the document loader with different file types:

```bash
# Test with a text file
python src/agent/document_loader.py sample.txt

# Test with a Word document  
python src/agent/document_loader.py document.docx

# Test with a PowerPoint presentation
python src/agent/document_loader.py presentation.pptx
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
2. **Encoding issues**: Text files should be UTF-8 encoded
3. **Large files**: Very large Excel files may take longer to process
4. **Corrupted files**: The system will report errors for unreadable files

### Debug Information

The document loader provides detailed debug output:
- File existence checks
- File size information  
- File type detection
- Processing status
- Content preview

## Frontend Visual Indicators

The upload component shows file types with color-coded badges:
- 🔴 **PDF**: Red badge
- 🔵 **Word**: Blue badge  
- 🟠 **PowerPoint**: Orange badge
- 🟢 **Excel**: Green badge
- ⚫ **Text**: Gray badge

## Future Enhancements

Potential additions:
- **Image files**: OCR text extraction from images
- **Audio files**: Speech-to-text conversion
- **Video files**: Subtitle/caption extraction
- **ZIP archives**: Extract and process contained documents
- **Email files**: Extract text from .eml files
