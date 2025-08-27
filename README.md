# RAG Chatbot with LangGraph - Advanced Document Analysis & Research

This project is a comprehensive RAG (Retrieval-Augmented Generation) chatbot system built with a React frontend and a Python FastAPI backend powered by LangGraph. The system combines advanced document analysis, web research, and conversational AI to provide intelligent, context-aware responses. It leverages Google Gemini models for natural language processing and integrates multiple data sources including uploaded documents and real-time web search.

<img src="./app.png" title="RAG Chatbot with LangGraph" alt="RAG Chatbot with LangGraph" width="90%">

## 🌟 Key Capabilities

- **🧠 Intelligent Document Processing**: Upload and analyze multiple document formats (PDF, Word, PowerPoint, Excel, text files)
- **🔍 Hybrid Search**: Combines document retrieval with real-time web search for comprehensive answers
- **💬 Advanced Chat Interface**: Persistent chat history with conversation management
- **🎯 Smart Re-ranking**: Uses cross-encoder models to improve document relevance
- **🤔 Reflective Reasoning**: Iteratively refines searches based on knowledge gap analysis
- **📊 Real-time Processing**: Live updates on document processing and query execution
- **🔄 Vector Database Integration**: Efficient semantic search using Pinecone vector store

## ✨ Features

### Core Functionality
- 💬 **Fullstack RAG Application**: React frontend with LangGraph-powered backend
- 🧠 **Advanced Research Agent**: Multi-step reasoning and iterative query refinement
- 🔍 **Dynamic Query Generation**: Smart search term generation using Google Gemini models
- 🌐 **Integrated Web Research**: Real-time web search via Google Search API
- 🤔 **Reflective Analysis**: Identifies knowledge gaps and refines search strategies

### Document Management
- 📄 **Multi-format Support**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), and text files
- 📚 **Intelligent Processing**: Automatic text extraction, chunking, and embedding generation
- 🎯 **Advanced Re-ranking**: Cross-encoder models for improved document relevance
- 💾 **Vector Storage**: Efficient semantic search using Pinecone vector database
- 📊 **Processing Status**: Real-time updates on document upload and processing

### Chat & History
- 💬 **Persistent Conversations**: Chat history with session management
- 🔄 **Conversation Management**: Create, view, and manage multiple chat sessions
- 💾 **Local & Cloud Storage**: Conversations stored locally and optionally in PostgreSQL
- 🔍 **Search History**: Find previous conversations and messages

### Development Features
- 🔄 **Hot-reloading**: Live updates for both frontend and backend during development
- 🧪 **Comprehensive Testing**: Unit tests, integration tests, and manual testing interfaces
- 📈 **Activity Timeline**: Real-time visualization of processing steps
- 🛠️ **Development Tools**: Built-in health checks and vector store status endpoints

## 🏗️ Project Structure

```
prototyp-na-patek/
├── frontend/                    # React + TypeScript frontend
│   ├── src/
│   │   ├── components/         # UI components
│   │   │   ├── ChatMessagesView.tsx
│   │   │   ├── ConversationList.tsx
│   │   │   ├── InputForm.tsx
│   │   │   ├── UploadFile.tsx
│   │   │   ├── ActivityTimeline.tsx
│   │   │   └── ui/            # Shadcn UI components
│   │   ├── hooks/             # Custom React hooks
│   │   │   └── useChatHistory.ts
│   │   ├── App.tsx            # Main application
│   │   └── EnhancedApp.tsx    # Enhanced chat interface
│   ├── package.json
│   └── vite.config.ts
├── backend/                     # Python FastAPI + LangGraph backend
│   ├── src/agent/
│   │   ├── app.py             # FastAPI application & API endpoints
│   │   ├── graph.py           # LangGraph agent definition
│   │   ├── document_loader.py # Multi-format document processing
│   │   ├── rag.py             # RAG pipeline implementation
│   │   ├── reranker.py        # Document re-ranking logic
│   │   ├── pinecone_connector.py # Vector database integration
│   │   ├── chat_history_api.py   # Chat history endpoints
│   │   ├── embeddings.py      # Text embedding generation
│   │   ├── prompts.py         # LLM prompts and templates
│   │   └── utils.py           # Utility functions
│   ├── tests/                 # Test files and manual testing interfaces
│   ├── pyproject.toml         # Python dependencies
│   └── langgraph.json         # LangGraph configuration
├── docker-compose.yml          # Production deployment
├── Dockerfile                  # Multi-stage Docker build
├── README.md                   # This file
├── SYSTEMOVA_DOKUMENTACE.md   # Detailed system documentation (Czech)
└── CHAT_HISTORY_README.md     # Chat history implementation guide
```

## 🚀 Getting Started: Development and Local Testing

Follow these steps to get the application running locally for development and testing.

### Prerequisites

- **Node.js 18+** and npm (or yarn/pnpm)
- **Python 3.11+** with pip or uv
- **Google Gemini API Key**: Required for LLM functionality
- **Pinecone API Key**: For vector database (optional, can use local embeddings)
- **Google Search API Key**: For web search functionality (optional)

### Environment Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Configure your API keys in `.env`:**
   ```env
   GEMINI_API_KEY="your_gemini_api_key_here"
   PINECONE_API_KEY="your_pinecone_api_key_here"  # Optional
   GOOGLE_SEARCH_API_KEY="your_google_search_key"  # Optional
   LANGSMITH_API_KEY="your_langsmith_key"  # Optional for monitoring
   ```

   Setting up the API keys:
   1) Google Gemini API Key (Google AI studio):
   Go to this site: https://aistudio.google.com/app/apikey
   Click on Create API key in the top-right corner
   Pick a Google Cloud Project (https://developers.google.com/workspace/guides/create-project)
   Copy the key to the env, created from env-example

   2) Pinecone:
   Cick on Create index in the top right corner
   Name the index
   Pick the multilingaul - e5 - large config
   Pick cloud provider - aws (the only free)
   Press create index
   On the left panel, there is API keys section
   Create API key in the top right corner
   Name the name and copy it

   PINECONE_ENVIRONMENT=used model
   In indexes, under the index name on the right there is Model: name

   3) Database URL (this is the DB to store chat history implemented in PostgreSQL)
   template = postgresql://username:password@localhost:5432/database_name

   4) Langsmith API key
   On the left panel pick API keys
   Click on the button in the top right corner

### Installation

**Backend Dependencies:**
```bash
cd backend
pip install .
# or with uv (recommended)
uv sync
```

**Frontend Dependencies:**
```bash
cd frontend
npm install
```

### Running the Application

**Quick Start (Recommended):**
```bash
# From project root
make dev
```

This command runs both backend and frontend development servers simultaneously.

**Manual Start:**

1. **Backend Server** (Terminal 1):
   ```bash
   cd backend
   langgraph dev
   ```
   Backend API: `http://127.0.0.1:2024`
   LangGraph UI: `http://127.0.0.1:2024/docs`

2. **Frontend Server** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend: `http://localhost:5173/app`

### First Steps

1. **Upload Documents**: Use the upload interface to add your documents
2. **Start Chatting**: Ask questions about your uploaded documents
3. **Explore Features**: Try web search, document analysis, and chat history

## 🧠 How the System Works

### RAG Pipeline Architecture

The system implements a sophisticated RAG pipeline that combines document analysis with web research:

<img src="./agent.png" title="Agent Flow" alt="Agent Flow" width="50%">

### Document Processing Flow

1. **Upload & Processing**: Documents are uploaded and processed through format-specific loaders
2. **Text Extraction**: Content is extracted and split into semantic chunks
3. **Embedding Generation**: Text chunks are converted to vector embeddings
4. **Vector Storage**: Embeddings are stored in Pinecone for efficient retrieval
5. **Indexing**: Metadata and references are maintained for source tracking

### Query Processing Flow

1. **Query Analysis**: User input is analyzed and search strategies are determined
2. **Document Retrieval**: Relevant document chunks are retrieved from vector store
3. **Re-ranking**: Results are re-ranked using cross-encoder models for relevance
4. **Web Research** (if needed): Additional web search for missing information
5. **Knowledge Gap Analysis**: System identifies if more information is needed
6. **Response Generation**: Final answer is synthesized with citations

### LangGraph Agent Workflow

1. **Generate Initial Queries**: Creates targeted search queries from user input
2. **Multi-source Research**: Searches both documents and web simultaneously  
3. **Reflection & Analysis**: Evaluates completeness and identifies knowledge gaps
4. **Iterative Refinement**: Refines queries and searches until sufficient information is gathered
5. **Answer Synthesis**: Combines all sources into a coherent, cited response

### Key Components

- **Document Loader**: Handles PDF, Word, PowerPoint, Excel, and text files
- **Embedding Service**: Generates semantic embeddings for text chunks
- **Vector Store**: Pinecone database for efficient similarity search
- **Re-ranker**: Cross-encoder model for improving result relevance
- **Chat History**: Persistent conversation management
- **Activity Timeline**: Real-time processing visualization

## 🔌 API Endpoints

### Core Functionality
- `POST /uploadfile/` - Upload and process documents (PDF, Word, Excel, etc.)
- `POST /query/` - Query the vector database with natural language
- `GET /vector-store/status` - Check vector database status and statistics
- `GET /vector-store/info` - Get detailed information about stored documents
- `GET /health` - System health check

### Chat History Management
- `GET /conversations/` - List all conversations with pagination
- `POST /conversations/` - Create a new conversation
- `GET /conversations/{id}` - Get specific conversation details
- `DELETE /conversations/{id}` - Delete a conversation
- `POST /conversations/{id}/messages` - Add message to conversation

### Development & Monitoring
- `GET /` - Frontend application (production)
- `GET /app/` - Frontend application (development)
- `GET /docs` - LangGraph API documentation
- WebSocket endpoints for real-time updates during processing

## 🧪 CLI Example

For quick testing and automation, you can execute the agent from the command line:

```bash
cd backend
python examples/cli_research.py "What are the latest trends in renewable energy?"
```

## 🧪 Testing

### Manual Testing Interfaces
The backend includes HTML testing interfaces for development:
- `backend/rag_test.html` - Test RAG functionality
- `backend/enhanced_chat_test.html` - Test chat interface
- `backend/test_upload.html` - Test file upload

### Automated Testing
```bash
cd backend

# Run all tests
python -m pytest

# Specific test files
python test_document_loader.py
python test_reranking.py
python test_async_operations.py
python test_upload_api.py
```

### Frontend Testing
```bash
cd frontend

# Linting
npm run lint

# Type checking
npm run build
```


## 🚢 Production Deployment

The application is designed for production deployment using Docker and supports horizontal scaling.

### Docker Deployment

**1. Build the Docker Image:**
```bash
# Build multi-stage image (from project root)
docker build -t rag-chatbot-langgraph -f Dockerfile .
```

**2. Run with Docker Compose:**
```bash
# Set environment variables and start services
GEMINI_API_KEY=<your_gemini_api_key> \
LANGSMITH_API_KEY=<your_langsmith_api_key> \
PINECONE_API_KEY=<your_pinecone_api_key> \
docker-compose up
```

**Access the application:**
- Frontend: `http://localhost:8123/app/`
- API: `http://localhost:8123`
- Health Check: `http://localhost:8123/health`

### Environment Configuration

#### Required Environment Variables
```env
GEMINI_API_KEY=your_gemini_api_key      # Google Gemini for LLM
```

#### Optional Environment Variables
```env
PINECONE_API_KEY=your_pinecone_key      # Vector database
GOOGLE_SEARCH_API_KEY=your_search_key   # Web search functionality
LANGSMITH_API_KEY=your_langsmith_key    # Monitoring and observability
DATABASE_URL=postgresql://...           # Chat history storage
REDIS_URL=redis://...                   # Caching and pub-sub
```

### Infrastructure Requirements

#### Minimum Requirements
- **CPU**: 2+ cores
- **Memory**: 4GB+ RAM  
- **Storage**: 10GB+ for documents and cache
- **Network**: Internet access for API calls

#### Recommended for Production
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ SSD
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **Vector DB**: Pinecone or self-hosted alternative

### Scaling Considerations

- **Stateless Design**: Backend can be horizontally scaled
- **External Dependencies**: Vector DB, PostgreSQL, and Redis support scaling
- **File Storage**: Consider cloud storage for document uploads in multi-instance setups
- **Load Balancing**: Use nginx or cloud load balancers for high availability

### Production Checklist

- [ ] Set all required environment variables
- [ ] Configure HTTPS/TLS certificates  
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies for databases
- [ ] Implement rate limiting
- [ ] Set up health check endpoints
- [ ] Configure CORS for your domain
- [ ] Set up log aggregation
- [ ] Implement error tracking

## 🛠️ Technologies Used

### Frontend Stack
- **[React 18](https://reactjs.org/)** - Modern UI library with hooks and concurrent features
- **[TypeScript](https://www.typescriptlang.org/)** - Type-safe JavaScript development
- **[Vite](https://vitejs.dev/)** - Fast build tool and development server
- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[Shadcn UI](https://ui.shadcn.com/)** - Beautiful and accessible component library

### Backend Stack
- **[Python 3.11+](https://python.org/)** - Core backend language
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for APIs
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Advanced agent orchestration framework
- **[LangChain](https://github.com/langchain-ai/langchain)** - LLM application development framework
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation using Python type annotations

### AI & ML Components
- **[Google Gemini](https://ai.google.dev/models/gemini)** - Large language model for reasoning and generation
- **[Sentence Transformers](https://www.sbert.net/)** - Text embedding generation and re-ranking
- **[Pinecone](https://www.pinecone.io/)** - Managed vector database for semantic search
- **[Google Search API](https://developers.google.com/custom-search/v1/overview)** - Web search integration

### Document Processing
- **[unstructured](https://github.com/Unstructured-IO/unstructured)** - Multi-format document parsing
- **[docx2txt](https://github.com/ankushshah89/python-docx2txt)** - Word document processing  
- **[openpyxl](https://openpyxl.readthedocs.io/)** - Excel file handling
- **[python-pptx](https://python-pptx.readthedocs.io/)** - PowerPoint processing
- **[PyPDF2](https://pypdf2.readthedocs.io/)** - PDF text extraction

### Infrastructure & DevOps
- **[Docker](https://www.docker.com/)** - Containerization and deployment
- **[PostgreSQL](https://www.postgresql.org/)** - Relational database for chat history
- **[Redis](https://redis.io/)** - Caching and pub-sub messaging
- **[UV](https://github.com/astral-sh/uv)** - Fast Python package installer and resolver

### Development Tools
- **[ESLint](https://eslint.org/)** - JavaScript/TypeScript linting
- **[Prettier](https://prettier.io/)** - Code formatting
- **[Ruff](https://github.com/astral-sh/ruff)** - Fast Python linter and formatter
- **[pytest](https://pytest.org/)** - Python testing framework
- **[LangSmith](https://smith.langchain.com/)** - LLM application monitoring and observability

## 📚 Documentation

- **[SYSTEMOVA_DOKUMENTACE.md](SYSTEMOVA_DOKUMENTACE.md)** - Comprehensive system documentation (Czech)
- **[CHAT_HISTORY_README.md](CHAT_HISTORY_README.md)** - Chat history implementation guide
- **[Backend Tests](backend/tests/)** - Manual testing interfaces and examples
- **[LangGraph Documentation](https://langchain-ai.github.io/langgraph/)** - Official LangGraph docs
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)** - API framework documentation

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `make test`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines
- Follow TypeScript and Python type hints
- Add tests for new functionality
- Update documentation for API changes
- Use conventional commit messages
- Ensure all tests pass before submitting

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues
1. **API Key Errors**: Verify all required API keys are set in `.env`
2. **Docker Issues**: Ensure Docker and docker-compose are properly installed
3. **Port Conflicts**: Check that ports 2024 (backend) and 5173 (frontend) are available
4. **Vector Database**: Verify Pinecone API key and index configuration

### Getting Help
- Check the [Issues](https://github.com/ser888gio/prototyp-na-patek/issues) page for known problems
- Review the comprehensive [system documentation](SYSTEMOVA_DOKUMENTACE.md)
- Examine the manual testing interfaces in `backend/tests/`

---

**Built with ❤️ using LangGraph, React, and Google Gemini** 
