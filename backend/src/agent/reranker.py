"""Re-ranking module for improving RAG retrieval relevance.

This module implements cross-encoder based re-ranking to improve the relevance
of retrieved documents after initial vector similarity search.
"""

import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional
from sentence_transformers import CrossEncoder
import numpy as np
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Cross-encoder based re-ranker for improving document relevance."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize the cross-encoder re-ranker.
        
        Args:
            model_name: Name of the cross-encoder model to use.
                       Default is a lightweight MS-MARCO trained model.
        """
        self.model_name = model_name
        self._model = None
        
    async def _load_model(self):
        """Load the cross-encoder model asynchronously."""
        if self._model is None:
            print(f"Loading cross-encoder model: {self.model_name}")
            
            def _load_model_sync():
                return CrossEncoder(self.model_name)
            
            self._model = await asyncio.to_thread(_load_model_sync)
            print(f"✅ Cross-encoder model loaded successfully")
    
    async def rerank_documents(
        self, 
        query: str, 
        documents: List[Document], 
        top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """Re-rank documents using cross-encoder.
        
        Args:
            query: The search query
            documents: List of documents to re-rank
            top_k: Number of top documents to return. If None, returns all.
            
        Returns:
            List of tuples (document, relevance_score) sorted by relevance
        """
        if not documents:
            return []
            
        # Load model if not already loaded
        await self._load_model()
        
        print(f"========== RE-RANKING DOCUMENTS ==========")
        print(f"Query: '{query}'")
        print(f"Documents to re-rank: {len(documents)}")
        print(f"Model: {self.model_name}")
        
        # Prepare query-document pairs for cross-encoder
        query_doc_pairs = []
        for doc in documents:
            # Truncate document content to avoid model limits (typically 512 tokens)
            content = doc.page_content[:2000]  # Rough character limit
            query_doc_pairs.append([query, content])
        
        # Compute relevance scores using cross-encoder
        def _predict_scores():
            return self._model.predict(query_doc_pairs)
        
        scores = await asyncio.to_thread(_predict_scores)
        
        # Combine documents with their relevance scores
        doc_score_pairs = list(zip(documents, scores))
        
        # Sort by relevance score (descending)
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Apply top_k filtering if specified
        if top_k is not None:
            doc_score_pairs = doc_score_pairs[:top_k]
        
        print(f"Re-ranking complete. Scores range: {min(scores):.4f} to {max(scores):.4f}")
        for i, (doc, score) in enumerate(doc_score_pairs[:5]):  # Log top 5
            print(f"  Rank {i+1}: Score {score:.4f} - {doc.page_content[:100]}...")
        print(f"========== END RE-RANKING ==========\n")
        
        return doc_score_pairs


class HybridReranker:
    """Hybrid re-ranker combining multiple ranking strategies."""
    
    def __init__(
        self, 
        cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        similarity_weight: float = 0.3,
        cross_encoder_weight: float = 0.7
    ):
        """Initialize hybrid re-ranker.
        
        Args:
            cross_encoder_model: Cross-encoder model name
            similarity_weight: Weight for original similarity scores
            cross_encoder_weight: Weight for cross-encoder scores
        """
        self.cross_encoder = CrossEncoderReranker(cross_encoder_model)
        self.similarity_weight = similarity_weight
        self.cross_encoder_weight = cross_encoder_weight
        
    async def rerank_documents(
        self, 
        query: str, 
        documents: List[Document], 
        top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """Re-rank documents using hybrid approach.
        
        Combines original similarity scores with cross-encoder scores.
        
        Args:
            query: The search query
            documents: List of documents to re-rank
            top_k: Number of top documents to return
            
        Returns:
            List of tuples (document, combined_score) sorted by relevance
        """
        if not documents:
            return []
            
        print(f"========== HYBRID RE-RANKING ==========")
        print(f"Similarity weight: {self.similarity_weight}")
        print(f"Cross-encoder weight: {self.cross_encoder_weight}")
        
        # Get cross-encoder scores
        cross_encoder_results = await self.cross_encoder.rerank_documents(
            query, documents, top_k=None
        )
        
        # Extract original similarity scores if available
        original_scores = []
        for doc in documents:
            score = getattr(doc, 'score', None)
            if score is not None:
                original_scores.append(score)
            else:
                # Default score if not available
                original_scores.append(0.5)
        
        # Normalize scores to [0, 1] range
        if original_scores:
            min_orig = min(original_scores)
            max_orig = max(original_scores)
            if max_orig > min_orig:
                normalized_orig = [(s - min_orig) / (max_orig - min_orig) for s in original_scores]
            else:
                normalized_orig = [0.5] * len(original_scores)
        else:
            normalized_orig = [0.5] * len(documents)
        
        # Get cross-encoder scores and normalize
        cross_scores = [score for _, score in cross_encoder_results]
        if cross_scores:
            min_cross = min(cross_scores)
            max_cross = max(cross_scores)
            if max_cross > min_cross:
                normalized_cross = [(s - min_cross) / (max_cross - min_cross) for s in cross_scores]
            else:
                normalized_cross = [0.5] * len(cross_scores)
        else:
            normalized_cross = [0.5] * len(documents)
        
        # Compute hybrid scores
        hybrid_results = []
        for i, doc in enumerate(documents):
            hybrid_score = (
                self.similarity_weight * normalized_orig[i] + 
                self.cross_encoder_weight * normalized_cross[i]
            )
            hybrid_results.append((doc, hybrid_score))
        
        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply top_k filtering
        if top_k is not None:
            hybrid_results = hybrid_results[:top_k]
        
        print(f"Hybrid re-ranking complete. Final scores:")
        for i, (doc, score) in enumerate(hybrid_results[:5]):
            print(f"  Rank {i+1}: Hybrid score {score:.4f} - {doc.page_content[:100]}...")
        print(f"========== END HYBRID RE-RANKING ==========\n")
        
        return hybrid_results


# Global re-ranker instance
_reranker = None

async def get_reranker(reranker_type: str = "cross_encoder") -> Any:
    """Get the global re-ranker instance.
    
    Args:
        reranker_type: Type of re-ranker ('cross_encoder' or 'hybrid')
        
    Returns:
        Re-ranker instance
    """
    global _reranker
    
    if _reranker is None:
        if reranker_type == "hybrid":
            _reranker = HybridReranker()
        else:
            _reranker = CrossEncoderReranker()
    
    return _reranker
