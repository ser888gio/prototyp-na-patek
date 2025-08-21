# Systémová Dokumentace - RAG Chatbot s LangGraph

## 📋 Obsah
1. [Přehled Systému](#přehled-systému)
2. [Architektura](#architektura)
3. [Technologie](#technologie)
4. [Komponenty](#komponenty)
5. [Databáze a Storage](#databáze-a-storage)
6. [API Endpointy](#api-endpointy)
7. [Instalace a Spuštění](#instalace-a-spuštění)
8. [Konfigurace](#konfigurace)
9. [Testování](#testování)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## 🔍 Přehled Systému

Tento projekt představuje pokročilý RAG (Retrieval-Augmented Generation) chatbot postavený na LangGraph frameworku s React frontend aplikací. Systém kombinuje webové vyhledávání s pokročilou analýzou dokumentů a využívá Google Gemini modely pro generování odpovědí.

### 🎯 Hlavní Funkcionality

- **💬 Konverzační AI**: Inteligentní chatbot s možností streamování odpovědí
- **📄 Multi-format dokumenty**: Podpora PDF, Word, PowerPoint, Excel, text souborů
- **🔍 Webové vyhledávání**: Dynamické generování vyhledávacích dotazů pomocí Google Search API
- **🎯 Re-ranking**: Pokročilé přeřazování dokumentů pro lepší relevanci
- **🤔 Reflexe**: Analýza znalostních mezer a iterativní vylepšování vyhledávání
- **📊 Vektorová databáze**: Pinecone pro ukládání a vyhledávání embeddings
- **📈 Real-time updates**: Sledování průběhu zpracování v reálném čase

---

## 🏗️ Architektura

### Celková Architektura

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   React Frontend    │    │   FastAPI Backend   │    │   External APIs     │
│                     │    │                     │    │                     │
│ • Chat Interface    │◄──►│ • LangGraph Agent   │◄──►│ • Google Gemini     │
│ • File Upload       │    │ • Document Loader   │    │ • Google Search     │
│ • Progress Tracking │    │ • RAG Pipeline      │    │ • Pinecone          │
│ • Real-time Updates │    │ • Re-ranking        │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                           │                           │
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Infrastruktura                                    │
│                                                                             │
│ • Redis (pub-sub, cache)                                                   │
│ • PostgreSQL (metadata, state)                                             │
│ • Docker Containers                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### LangGraph Agent Flow

```mermaid
graph TD
    A[User Query] --> B[Generate Initial Queries]
    B --> C[Web Research]
    C --> D[RAG Search]
    D --> E[Re-ranking]
    E --> F[Reflection & Analysis]
    F --> G{Sufficient Info?}
    G -->|No| H[Generate Follow-up Queries]
    H --> C
    G -->|Yes| I[Finalize Answer]
    I --> J[Response with Citations]
```

---

## 💻 Technologie

### Frontend Stack
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool a dev server
- **Tailwind CSS** - Styling framework  
- **Shadcn UI** - Komponenty knihovna
- **Axios** - HTTP klient
- **React Router** - Routing

### Backend Stack
- **Python 3.11+** - Runtime
- **FastAPI** - Web framework
- **LangGraph** - AI agent orchestrace
- **LangChain** - LLM tooling
- **Pydantic** - Data validace

### AI & ML
- **Google Gemini 2.0 Flash** - LLM model
- **HuggingFace Transformers** - Embedding modely
- **Sentence Transformers** - Re-ranking modely
- **Cross-encoder models** - Relevance scoring

### Databáze & Storage
- **Pinecone** - Vektorová databáze
- **Redis** - Cache a pub-sub
- **PostgreSQL** - Metadata storage
- **Local filesystem** - Dočasné soubory

### DevOps & Infrastructure
- **Docker** - Kontejnerizace
- **Docker Compose** - Orchestrace
- **UV** - Python package manager
- **ESLint** - Code linting
- **Ruff** - Python linter

---

## 🧩 Komponenty

### 📱 Frontend Komponenty

#### `App.tsx`
- **Role**: Hlavní aplikační komponenta
- **Funkce**: Routing, state management, real-time komunikace s backendem
- **Key features**: 
  - WebSocket komunikace pro streamování
  - Processing events tracking
  - Error handling

#### `ChatMessagesView.tsx`
- **Role**: Zobrazení konverzace
- **Funkce**: Renderování zpráv, progress indikátory, citations
- **Key features**: 
  - Markdown support
  - Citation linking
  - Message typing animation

#### `InputForm.tsx`
- **Role**: Input pro uživatelské dotazy
- **Funkce**: Odeslání dotazů, validation
- **Key features**: 
  - Multi-line support
  - Keyboard shortcuts
  - Loading states

#### `UploadFile.tsx`
- **Role**: Nahrávání souborů
- **Funkce**: Drag & drop, multiple files, progress tracking
- **Key features**: 
  - File type validation
  - Progress bars
  - Error handling

#### `ActivityTimeline.tsx`
- **Role**: Sledování průběhu zpracování
- **Funkce**: Real-time updates procesních kroků
- **Key features**: 
  - Step visualization
  - Time tracking
  - Status indicators

### 🔧 Backend Komponenty

#### `app.py`
- **Role**: FastAPI aplikace a API endpointy
- **Funkce**: HTTP routing, CORS, static files serving
- **Key endpoints**: 
  - `/uploadfile/` - nahrávání souborů
  - `/query/` - dotazování vektorové DB
  - `/health` - health check

#### `graph.py`
- **Role**: LangGraph agent definice
- **Funkce**: Orchestrace AI workflow
- **Key nodes**: 
  - `generate_queries` - generování vyhledávacích dotazů
  - `web_research` - webové vyhledávání
  - `rag_search` - vektorové vyhledávání
  - `reflection` - analýza a rozhodování
  - `finalize_answer` - generování finální odpovědi

#### `document_loader.py`
- **Role**: Načítání a zpracování dokumentů
- **Funkce**: Multi-format support, text extraction
- **Supported formats**: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV

#### `reranker.py`
- **Role**: Re-ranking načtených dokumentů
- **Funkce**: Zlepšení relevance pomocí cross-encoder modelů
- **Strategies**: 
  - CrossEncoderReranker
  - HybridReranker

#### `text_splitter.py`
- **Role**: Rozdělení textu na chunky
- **Funkce**: Optimalizace pro embedding a retrieval

#### `pinecone_connector.py`
- **Role**: Připojení k Pinecone vektorové databázi
- **Funkce**: Index management, embedding storage

---

## 💾 Databáze a Storage

### Pinecone Vector Database
```
Index: "document-embeddings"
Dimensions: 384 (sentence-transformers/all-MiniLM-L6-v2)
Metric: cosine
```

**Uložená data:**
- Document chunks (text segments)
- Embeddings vectors
- Metadata (filename, chunk_id, source_type)

### Redis Cache
**Použití:**
- Session data
- Temporary query results
- Pub-sub messaging pro real-time updates

### PostgreSQL
**Schéma:**
- Conversations history
- User sessions
- Processing status
- Agent state persistence

### File System
**Struktura:**
```
/temp/
  ├── uploads/          # Uploaded files
  ├── processed/        # Processed documents
  └── cache/           # Temporary cache
```

---

## 🔌 API Endpointy

### Core API

#### `POST /uploadfile/`
**Popis**: Nahrání a zpracování dokumentů
```python
# Request
files: List[UploadFile]

# Response
{
  "status": "success",
  "message": "Files processed successfully",
  "files_processed": 3,
  "chunks_created": 127
}
```

#### `POST /query/`
**Popis**: Dotazování vektorové databáze
```python
# Request
{
  "query": "What is machine learning?"
}

# Response
{
  "status": "success",
  "results": [
    {
      "id": 0,
      "content": "Machine learning is...",
      "metadata": {...},
      "original_score": 0.75,
      "relevance_score": 0.95
    }
  ]
}
```

#### `GET /vector-store/status`
**Popis**: Status vektorové databáze
```python
# Response
{
  "index_exists": true,
  "total_vectors": 1250,
  "index_name": "document-embeddings"
}
```

#### `GET /health`
**Popis**: Health check
```python
# Response
{
  "status": "healthy",
  "version": "0.0.1"
}
```

### LangGraph API

#### `POST /runs/stream`
**Popis**: Streamování AI agent execution
```python
# Request
{
  "assistant_id": "agent",
  "input": {"user_input": "Explain quantum computing"},
  "config": {...}
}

# Stream Response
data: {"event": "on_chat_model_stream", "data": {...}}
```

---

## 🚀 Instalace a Spuštění

### Předpoklady
- **Node.js 18+** a npm
- **Python 3.11+**
- **Docker** a Docker Compose
- **Git**

### Lokální Vývoj

#### 1. Klonování Repozitáře
```bash
git clone <repository-url>
cd prototyp-na-patek
```

#### 2. Environment Setup
```bash
# Backend
cd backend
cp .env.example .env
# Editovat .env s API klíči

# Frontend
cd ../frontend
npm install
```

#### 3. Dependencies Installation

**Backend:**
```bash
cd backend
pip install -e .
```

**Frontend:**
```bash
cd frontend
npm install
```

#### 4. Spuštění Development Servers

**Společné spuštění:**
```bash
make dev
```

**Odděleně:**
```bash
# Backend (terminal 1)
cd backend
langgraph dev

# Frontend (terminal 2)
cd frontend
npm run dev
```

**Přístup:**
- Frontend: `http://localhost:5173/app`
- Backend API: `http://127.0.0.1:2024`
- LangGraph UI: `http://127.0.0.1:2024/docs`

### Production Build

#### 1. Docker Build
```bash
docker build -t gemini-fullstack-langgraph -f Dockerfile .
```

#### 2. Docker Compose
```bash
GEMINI_API_KEY=<key> LANGSMITH_API_KEY=<key> docker-compose up
```

**Přístup:**
- Aplikace: `http://localhost:8123/app/`
- API: `http://localhost:8123`

---

## ⚙️ Konfigurace

### Environment Variables

#### Backend `.env`
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional
LANGSMITH_API_KEY=your_langsmith_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_environment

# Database
REDIS_URI=redis://localhost:6379
POSTGRES_URI=postgres://user:pass@localhost:5432/db
```

#### Frontend Environment
```typescript
// vite.config.ts proxy configuration
server: {
  proxy: {
    "/api": {
      target: "http://127.0.0.1:2024",
      changeOrigin: true,
    },
  },
}
```

### Agent Configuration

#### `configuration.py`
```python
class Configuration(BaseModel):
    # Models
    query_generator_model: str = "gemini-2.0-flash"
    reflection_model: str = "gemini-2.0-flash"
    answer_model: str = "gemini-2.0-flash"
    
    # Search parameters
    number_of_initial_queries: int = 3
    max_research_loops: int = 2
    
    # Re-ranking
    enable_reranking: bool = True
    reranking_strategy: str = "hybrid"
    reranking_top_k: int = 5
```

---

## 🧪 Testování

### Backend Tests
```bash
cd backend

# Unit tests
python test_document_loader.py
python test_reranking.py
python test_async_operations.py

# Integration tests
python test_upload_api.py
```

### Frontend Tests
```bash
cd frontend

# Linting
npm run lint

# Type checking
npm run build
```

### End-to-End Testing

#### Test HTML Interfaces
- `backend/rag_test.html` - RAG funkcionalita
- `backend/enhanced_chat_test.html` - Chat interface
- `backend/test_upload.html` - File upload

#### Manual Testing Checklist
- [ ] Upload různých typů souborů
- [ ] Dotazování vektorové databáze
- [ ] Streamování odpovědí
- [ ] Re-ranking functionality
- [ ] Error handling

---

## 🚢 Deployment

### Docker Production

#### Multi-stage Build
```dockerfile
# Stage 1: React build
FROM node:20-alpine AS frontend-builder
# ... frontend build steps

# Stage 2: Python backend
FROM langchain/langgraph-api:3.11
# ... backend setup steps
```

#### Infrastructure Requirements
```yaml
# docker-compose.yml
services:
  langgraph-redis:
    image: redis:6
    
  langgraph-postgres:
    image: postgres:16
    
  langgraph-api:
    image: gemini-fullstack-langgraph
    depends_on: [redis, postgres]
```

### Cloud Deployment

#### Environment Setup
- **Redis**: Cloud Redis instance
- **PostgreSQL**: Managed database
- **File Storage**: Cloud storage pro documents
- **Load Balancer**: Pro high availability

#### Scaling Considerations
- **Horizontal scaling**: Multiple API instances
- **Vector DB**: Pinecone auto-scales
- **Redis**: Redis Cluster pro large datasets
- **PostgreSQL**: Read replicas

---

## 🔧 Troubleshooting

### Časté Problémy

#### 1. Import Errors
```python
# Chyba: ModuleNotFoundError
# Řešení: Zkontrolovat Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

#### 2. CORS Issues
```javascript
// Chyba: CORS policy error
// Řešení: Zkontrolovat CORS middleware v app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 3. Environment Variables
```bash
# Chyba: API key not found
# Řešení: Zkontrolovat .env soubor
cat backend/.env | grep GEMINI_API_KEY
```

#### 4. Docker Build Issues
```bash
# Chyba: Frontend build not found
# Řešení: Zkontrolovat build path
ls -la frontend/dist/
```

#### 5. Vector Store Connection
```python
# Chyba: Pinecone connection failed
# Řešení: Zkontrolovat API key a index
pinecone.list_indexes()
```

### Debug Nástroje

#### Backend Debugging
```python
# Logging configuration
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug vector store
python -c "from agent.pinecone_connector import *; asyncio.run(pinecone_connector_start())"
```

#### Frontend Debugging
```bash
# Development console
npm run dev -- --debug

# Network requests
# Browser DevTools -> Network tab
```

### Monitoring

#### Health Checks
```bash
# Backend health
curl http://localhost:2024/health

# Vector store status
curl http://localhost:2024/vector-store/status

# Redis connection
redis-cli ping
```

#### Logs Analysis
```bash
# Docker logs
docker-compose logs -f langgraph-api

# Application logs
tail -f logs/application.log
```

---

## 📚 Další Dokumentace

- [RAG_README.md](RAG_README.md) - RAG specifická dokumentace
- [RERANKING_README.md](RERANKING_README.md) - Re-ranking funkcionality
- [DOCUMENT_FORMATS.md](DOCUMENT_FORMATS.md) - Podporované formáty dokumentů
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Pinecone Documentation](https://docs.pinecone.io/)

---

## 📞 Podpora

Pro problémy s:
- **AI Agent**: Zkontrolovat LangGraph konfiguraci
- **Vector Search**: Pinecone connection a indexy  
- **Document Processing**: Podporované formáty a dependencies
- **Frontend**: React/Vite setup a proxy konfigurace
- **Deployment**: Docker a environment setup

---

*Dokumentace aktualizována: 21.8.2025*
*Verze systému: 0.0.1*
