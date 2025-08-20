# Re-ranking Feature for RAG System

This document describes the re-ranking functionality added to improve the relevance of retrieved documents in the RAG (Retrieval-Augmented Generation) system.

## Overview

Re-ranking is a technique used to improve the quality of document retrieval by applying a more sophisticated ranking model after the initial vector similarity search. This two-stage approach:

1. **First stage**: Fast vector similarity search to get candidate documents
2. **Second stage**: More sophisticated re-ranking to improve relevance

## Benefits

- **Improved Relevance**: Cross-encoder models can better understand query-document relationships
- **Better User Experience**: More relevant documents lead to better answers
- **Configurable**: Can be enabled/disabled and configured per use case

## Implementation

### Re-ranking Models

#### 1. CrossEncoderReranker
- Uses a cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2` by default)
- Processes query-document pairs jointly for better relevance scoring
- More accurate but slightly slower than embedding-based similarity

#### 2. HybridReranker
- Combines original similarity scores with cross-encoder scores
- Configurable weights for each scoring method
- Default: 30% similarity, 70% cross-encoder
- Balances accuracy with consideration of original retrieval scores

### Configuration Options

The re-ranking behavior can be controlled through the `Configuration` class:

```python
# Enable/disable re-ranking
enable_reranking: bool = True

# Choose re-ranking strategy ("cross_encoder" or "hybrid")
reranking_strategy: str = "hybrid"

# Number of documents to keep after re-ranking
reranking_top_k: int = 5
```

### Retrieval Pipeline Changes

#### Before Re-ranking
```
Query → Vector Search → Top K documents (k=3, threshold=0.4) → Results
```

#### After Re-ranking
```
Query → Vector Search → More documents (k=10, threshold=0.3) → Re-ranking → Top K relevant (k=5) → Results
```

### Performance Considerations

1. **Initial Retrieval**: Increased from k=3 to k=10 to provide more candidates for re-ranking
2. **Threshold Relaxed**: Lowered from 0.4 to 0.3 to capture more potential matches
3. **Model Loading**: Cross-encoder model is loaded once and reused
4. **Async Processing**: All operations are async to maintain responsiveness

## Usage Examples

### API Endpoint
The `/query/` endpoint now automatically applies re-ranking:

```json
{
  "query": "What is Python programming language?"
}
```

Response includes both original similarity scores and re-ranking scores:

```json
{
  "status": "success",
  "results": [
    {
      "id": 0,
      "content": "Python is a programming language...",
      "metadata": {...},
      "original_score": 0.75,
      "relevance_score": 0.95
    }
  ]
}
```

### LangGraph Integration
Re-ranking is automatically applied in the `rag_search` node:

```python
# Configuration controls re-ranking behavior
config = {
  "configurable": {
    "enable_reranking": True,
    "reranking_strategy": "hybrid",
    "reranking_top_k": 5
  }
}
```

## Testing

Run the test script to verify re-ranking functionality:

```bash
cd backend
python test_reranking.py
```

The test validates:
- Cross-encoder model loading and prediction
- Hybrid re-ranking with score combination
- Proper document ordering by relevance

## Model Information

### Default Cross-Encoder Model
- **Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Training**: Trained on MS MARCO dataset for passage ranking
- **Size**: ~91MB
- **Performance**: Good balance of accuracy and speed
- **License**: Apache 2.0

### Alternative Models
The system can be configured to use other cross-encoder models:

- `cross-encoder/ms-marco-MiniLM-L-12-v2` (larger, more accurate)
- `cross-encoder/ms-marco-TinyBERT-L-2` (smaller, faster)
- `cross-encoder/qnli-electra-base` (for question answering)

## Future Enhancements

1. **Model Caching**: Implement model caching for faster subsequent loads
2. **Batch Processing**: Process multiple queries simultaneously
3. **Custom Training**: Fine-tune models on domain-specific data
4. **A/B Testing**: Compare different re-ranking strategies
5. **Metrics**: Add re-ranking quality metrics and monitoring

## Dependencies

- `sentence-transformers>=2.2.0`: For cross-encoder models
- `torch`: Required by sentence-transformers
- `transformers`: Hugging Face transformers library

## Configuration Files

- `backend/src/agent/reranker.py`: Re-ranking implementation
- `backend/src/agent/configuration.py`: Configuration options
- `backend/src/agent/graph.py`: LangGraph integration
- `backend/src/agent/app.py`: API endpoint integration
