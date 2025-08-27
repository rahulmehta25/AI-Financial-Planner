"""
RAG (Retrieval-Augmented Generation) System for Financial Knowledge
Provides vector search and knowledge retrieval for financial domain expertise
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import hashlib
from pathlib import Path

import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant, Pinecone, Weaviate, Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader, 
    UnstructuredMarkdownLoader, JSONLoader
)
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.retrievers import (
    ContextualCompressionRetriever,
    EnsembleRetriever,
    MultiQueryRetriever
)
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI

import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
import redis
from sentence_transformers import SentenceTransformer
import faiss
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class KnowledgeSource(Enum):
    """Types of knowledge sources"""
    REGULATORY = "regulatory"
    TAX_CODE = "tax_code"
    MARKET_ANALYSIS = "market_analysis"
    INVESTMENT_STRATEGIES = "investment_strategies"
    FINANCIAL_PLANNING = "financial_planning"
    ECONOMIC_INDICATORS = "economic_indicators"
    COMPANY_FILINGS = "company_filings"
    RESEARCH_REPORTS = "research_reports"
    USER_DOCUMENTS = "user_documents"


class DocumentType(Enum):
    """Types of documents in knowledge base"""
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


@dataclass
class KnowledgeDocument:
    """Represents a document in the knowledge base"""
    id: str
    source: KnowledgeSource
    type: DocumentType
    title: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    chunks: List[str] = field(default_factory=list)
    chunk_embeddings: List[np.ndarray] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    relevance_score: float = 0.0


@dataclass
class RetrievalResult:
    """Result from knowledge retrieval"""
    documents: List[Document]
    scores: List[float]
    query: str
    total_results: int
    retrieval_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancialRAGSystem:
    """
    Advanced RAG system specialized for financial domain knowledge
    Combines vector search, hybrid retrieval, and domain-specific ranking
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embeddings = self._initialize_embeddings()
        self.vector_stores = self._initialize_vector_stores()
        self.text_splitters = self._initialize_text_splitters()
        self.retrievers = {}
        self.redis_client = redis.Redis.from_url(
            config.get('redis_url', 'redis://localhost:6379')
        )
        self.knowledge_sources = self._load_knowledge_sources()
        self.domain_vocabulary = self._load_financial_vocabulary()
        self.reranker = self._initialize_reranker()
        
    def _initialize_embeddings(self) -> Dict[str, Any]:
        """Initialize embedding models"""
        embeddings = {}
        
        # OpenAI embeddings for general use
        if self.config.get('openai_api_key'):
            embeddings['openai'] = OpenAIEmbeddings(
                openai_api_key=self.config['openai_api_key'],
                model="text-embedding-3-large"
            )
        
        # Sentence transformers for specialized domains
        embeddings['financial'] = SentenceTransformer(
            'sentence-transformers/all-mpnet-base-v2'
        )
        
        # Custom fine-tuned model for financial text
        if self.config.get('custom_model_path'):
            embeddings['custom'] = SentenceTransformer(
                self.config['custom_model_path']
            )
        
        return embeddings
    
    def _initialize_vector_stores(self) -> Dict[str, Any]:
        """Initialize vector databases"""
        stores = {}
        
        # Qdrant for primary storage
        if self.config.get('qdrant_url'):
            stores['qdrant'] = qdrant_client.QdrantClient(
                url=self.config['qdrant_url'],
                api_key=self.config.get('qdrant_api_key')
            )
            
        # Pinecone for cloud storage
        if self.config.get('pinecone_api_key'):
            import pinecone
            pinecone.init(
                api_key=self.config['pinecone_api_key'],
                environment=self.config.get('pinecone_env', 'us-east-1')
            )
            stores['pinecone'] = pinecone.Index('financial-knowledge')
        
        # Local Chroma for development
        stores['chroma'] = Chroma(
            embedding_function=self.embeddings.get('openai'),
            persist_directory="./chroma_db"
        )
        
        # FAISS for fast local search
        dimension = 1536  # OpenAI embedding dimension
        stores['faiss'] = faiss.IndexFlatL2(dimension)
        
        return stores
    
    def _initialize_text_splitters(self) -> Dict[str, Any]:
        """Initialize text splitting strategies"""
        splitters = {}
        
        # Recursive splitter for general documents
        splitters['recursive'] = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Token splitter for precise token control
        splitters['token'] = TokenTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        # Custom splitter for financial documents
        splitters['financial'] = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=[
                "\n## ",  # Section headers
                "\n### ",  # Subsection headers
                "\n\n",    # Paragraphs
                ".\n",     # Sentences with newlines
                ". ",      # Sentences
                "\n",      # Lines
                " ",       # Words
                ""         # Characters
            ]
        )
        
        return splitters
    
    def _initialize_reranker(self):
        """Initialize reranking model for result optimization"""
        # This would use a cross-encoder model for reranking
        # Simplified for demonstration
        return None
    
    def _load_knowledge_sources(self) -> Dict[KnowledgeSource, str]:
        """Load paths to knowledge source documents"""
        base_path = self.config.get('knowledge_base_path', './knowledge_base')
        
        return {
            KnowledgeSource.REGULATORY: f"{base_path}/regulatory",
            KnowledgeSource.TAX_CODE: f"{base_path}/tax",
            KnowledgeSource.MARKET_ANALYSIS: f"{base_path}/market",
            KnowledgeSource.INVESTMENT_STRATEGIES: f"{base_path}/strategies",
            KnowledgeSource.FINANCIAL_PLANNING: f"{base_path}/planning",
            KnowledgeSource.ECONOMIC_INDICATORS: f"{base_path}/economics",
            KnowledgeSource.COMPANY_FILINGS: f"{base_path}/filings",
            KnowledgeSource.RESEARCH_REPORTS: f"{base_path}/research",
            KnowledgeSource.USER_DOCUMENTS: f"{base_path}/users"
        }
    
    def _load_financial_vocabulary(self) -> Dict[str, List[str]]:
        """Load domain-specific financial vocabulary"""
        return {
            'tax_terms': [
                'deduction', 'credit', 'liability', 'withholding',
                'capital gains', 'ordinary income', 'AMT', 'FICA'
            ],
            'investment_terms': [
                'alpha', 'beta', 'sharpe ratio', 'volatility',
                'correlation', 'diversification', 'rebalancing'
            ],
            'regulatory_terms': [
                'SEC', 'FINRA', 'fiduciary', 'compliance',
                'suitability', 'best interest', 'disclosure'
            ],
            'retirement_terms': [
                '401k', 'IRA', 'Roth', 'RMD', 'vesting',
                'employer match', 'contribution limit'
            ]
        }
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        source: KnowledgeSource,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Index documents into vector stores"""
        
        indexed_count = 0
        failed_count = 0
        index_metadata = {
            'source': source.value,
            'timestamp': datetime.utcnow().isoformat(),
            'documents': []
        }
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Process each document
                processed_docs = await self._process_documents(batch, source)
                
                # Generate embeddings
                embeddings = await self._generate_embeddings(processed_docs)
                
                # Store in vector databases
                await self._store_in_vector_dbs(processed_docs, embeddings)
                
                # Update metadata
                indexed_count += len(batch)
                index_metadata['documents'].extend([
                    {'id': doc['id'], 'title': doc.get('title', 'Untitled')}
                    for doc in batch
                ])
                
            except Exception as e:
                logger.error(f"Failed to index batch: {e}")
                failed_count += len(batch)
        
        # Store indexing metadata
        await self._store_index_metadata(index_metadata)
        
        return {
            'indexed': indexed_count,
            'failed': failed_count,
            'total': len(documents),
            'source': source.value
        }
    
    async def _process_documents(
        self,
        documents: List[Dict[str, Any]],
        source: KnowledgeSource
    ) -> List[KnowledgeDocument]:
        """Process raw documents into knowledge documents"""
        
        processed = []
        
        for doc in documents:
            # Determine document type
            doc_type = self._detect_document_type(doc)
            
            # Extract content
            content = await self._extract_content(doc, doc_type)
            
            # Split into chunks
            splitter = self._select_splitter(doc_type, source)
            chunks = splitter.split_text(content)
            
            # Add metadata
            metadata = self._enrich_metadata(doc, source)
            
            # Create knowledge document
            knowledge_doc = KnowledgeDocument(
                id=doc.get('id', self._generate_doc_id(content)),
                source=source,
                type=doc_type,
                title=doc.get('title', 'Untitled'),
                content=content,
                metadata=metadata,
                chunks=chunks
            )
            
            processed.append(knowledge_doc)
        
        return processed
    
    async def _generate_embeddings(
        self,
        documents: List[KnowledgeDocument]
    ) -> List[List[np.ndarray]]:
        """Generate embeddings for documents and chunks"""
        
        all_embeddings = []
        embedding_model = self.embeddings.get('openai', self.embeddings['financial'])
        
        for doc in documents:
            # Embed full document
            if hasattr(embedding_model, 'embed_documents'):
                doc_embedding = embedding_model.embed_documents([doc.content])[0]
            else:
                doc_embedding = embedding_model.encode(doc.content)
            
            doc.embedding = doc_embedding
            
            # Embed chunks
            if doc.chunks:
                if hasattr(embedding_model, 'embed_documents'):
                    chunk_embeddings = embedding_model.embed_documents(doc.chunks)
                else:
                    chunk_embeddings = embedding_model.encode(doc.chunks)
                
                doc.chunk_embeddings = chunk_embeddings
                all_embeddings.append(chunk_embeddings)
            else:
                all_embeddings.append([doc_embedding])
        
        return all_embeddings
    
    async def _store_in_vector_dbs(
        self,
        documents: List[KnowledgeDocument],
        embeddings: List[List[np.ndarray]]
    ):
        """Store documents and embeddings in vector databases"""
        
        # Store in Qdrant
        if 'qdrant' in self.vector_stores:
            await self._store_in_qdrant(documents, embeddings)
        
        # Store in Chroma
        if 'chroma' in self.vector_stores:
            await self._store_in_chroma(documents, embeddings)
        
        # Store in FAISS
        if 'faiss' in self.vector_stores:
            await self._store_in_faiss(documents, embeddings)
        
        # Cache in Redis for fast access
        await self._cache_documents(documents)
    
    async def _store_in_qdrant(
        self,
        documents: List[KnowledgeDocument],
        embeddings: List[List[np.ndarray]]
    ):
        """Store in Qdrant vector database"""
        
        client = self.vector_stores['qdrant']
        collection_name = "financial_knowledge"
        
        # Create collection if not exists
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=len(embeddings[0][0]) if embeddings else 1536,
                    distance=Distance.COSINE
                )
            )
        except:
            pass  # Collection already exists
        
        # Prepare points
        points = []
        point_id = 0
        
        for doc, doc_embeddings in zip(documents, embeddings):
            for i, (chunk, embedding) in enumerate(zip(doc.chunks, doc_embeddings)):
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding.tolist(),
                        payload={
                            'doc_id': doc.id,
                            'source': doc.source.value,
                            'type': doc.type.value,
                            'title': doc.title,
                            'chunk_index': i,
                            'chunk_text': chunk,
                            'metadata': doc.metadata
                        }
                    )
                )
                point_id += 1
        
        # Upload points
        client.upsert(
            collection_name=collection_name,
            points=points
        )
    
    async def _store_in_chroma(
        self,
        documents: List[KnowledgeDocument],
        embeddings: List[List[np.ndarray]]
    ):
        """Store in Chroma vector database"""
        
        chroma_db = self.vector_stores['chroma']
        
        # Prepare documents for Chroma
        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            for i, chunk in enumerate(doc.chunks):
                texts.append(chunk)
                metadatas.append({
                    'doc_id': doc.id,
                    'source': doc.source.value,
                    'type': doc.type.value,
                    'title': doc.title,
                    'chunk_index': i,
                    **doc.metadata
                })
                ids.append(f"{doc.id}_chunk_{i}")
        
        # Add to Chroma
        if texts:
            chroma_db.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids
            )
    
    async def _store_in_faiss(
        self,
        documents: List[KnowledgeDocument],
        embeddings: List[List[np.ndarray]]
    ):
        """Store in FAISS index"""
        
        faiss_index = self.vector_stores['faiss']
        
        # Flatten embeddings
        all_embeddings = []
        for doc_embeddings in embeddings:
            all_embeddings.extend(doc_embeddings)
        
        if all_embeddings:
            # Convert to numpy array
            embedding_matrix = np.array(all_embeddings).astype('float32')
            
            # Add to FAISS index
            faiss_index.add(embedding_matrix)
            
            # Save index
            faiss.write_index(faiss_index, "financial_knowledge.index")
    
    async def retrieve(
        self,
        query: str,
        source_filter: Optional[List[KnowledgeSource]] = None,
        top_k: int = 10,
        hybrid_search: bool = True,
        rerank: bool = True
    ) -> RetrievalResult:
        """Retrieve relevant documents for a query"""
        
        start_time = datetime.utcnow()
        
        # Preprocess query
        processed_query = self._preprocess_query(query)
        
        # Generate query embedding
        query_embedding = await self._embed_query(processed_query)
        
        # Perform retrieval
        if hybrid_search:
            results = await self._hybrid_retrieve(
                processed_query,
                query_embedding,
                source_filter,
                top_k * 2  # Get more for reranking
            )
        else:
            results = await self._vector_retrieve(
                query_embedding,
                source_filter,
                top_k * 2
            )
        
        # Rerank results if requested
        if rerank and len(results) > 0:
            results = await self._rerank_results(
                query,
                results,
                top_k
            )
        else:
            results = results[:top_k]
        
        # Calculate retrieval time
        retrieval_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Format results
        documents = []
        scores = []
        
        for result in results:
            documents.append(Document(
                page_content=result['content'],
                metadata=result['metadata']
            ))
            scores.append(result['score'])
        
        return RetrievalResult(
            documents=documents,
            scores=scores,
            query=query,
            total_results=len(documents),
            retrieval_time=retrieval_time,
            metadata={
                'hybrid_search': hybrid_search,
                'reranked': rerank,
                'sources_filtered': source_filter is not None
            }
        )
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for better retrieval"""
        
        # Expand abbreviations
        abbreviations = {
            'roi': 'return on investment',
            'pe': 'price to earnings',
            'etf': 'exchange traded fund',
            'ira': 'individual retirement account',
            'rmd': 'required minimum distribution'
        }
        
        processed = query.lower()
        for abbr, expansion in abbreviations.items():
            if abbr in processed.split():
                processed = processed.replace(abbr, expansion)
        
        # Add domain context if needed
        if not any(term in processed for term in ['tax', 'invest', 'retire', 'portfolio']):
            processed = f"financial planning {processed}"
        
        return processed
    
    async def _embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for query"""
        
        embedding_model = self.embeddings.get('openai', self.embeddings['financial'])
        
        if hasattr(embedding_model, 'embed_query'):
            return embedding_model.embed_query(query)
        else:
            return embedding_model.encode(query)
    
    async def _hybrid_retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        source_filter: Optional[List[KnowledgeSource]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform hybrid retrieval (vector + keyword)"""
        
        # Vector search
        vector_results = await self._vector_retrieve(
            query_embedding,
            source_filter,
            top_k
        )
        
        # BM25 keyword search
        keyword_results = await self._keyword_retrieve(
            query,
            source_filter,
            top_k
        )
        
        # Combine results using reciprocal rank fusion
        combined = self._reciprocal_rank_fusion(
            [vector_results, keyword_results],
            weights=[0.7, 0.3]  # Weight vector search more heavily
        )
        
        return combined
    
    async def _vector_retrieve(
        self,
        query_embedding: np.ndarray,
        source_filter: Optional[List[KnowledgeSource]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        
        results = []
        
        # Search in Qdrant
        if 'qdrant' in self.vector_stores:
            qdrant_results = await self._search_qdrant(
                query_embedding,
                source_filter,
                top_k
            )
            results.extend(qdrant_results)
        
        # Search in Chroma
        if 'chroma' in self.vector_stores:
            chroma_results = await self._search_chroma(
                query_embedding,
                source_filter,
                top_k
            )
            results.extend(chroma_results)
        
        # Deduplicate and sort by score
        seen_ids = set()
        unique_results = []
        
        for result in sorted(results, key=lambda x: x['score'], reverse=True):
            if result['id'] not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result['id'])
        
        return unique_results[:top_k]
    
    async def _keyword_retrieve(
        self,
        query: str,
        source_filter: Optional[List[KnowledgeSource]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based retrieval using BM25"""
        
        # Get documents from cache
        all_docs = await self._get_cached_documents(source_filter)
        
        if not all_docs:
            return []
        
        # Tokenize documents and query
        tokenized_docs = [doc['content'].lower().split() for doc in all_docs]
        tokenized_query = query.lower().split()
        
        # Create BM25 index
        bm25 = BM25Okapi(tokenized_docs)
        
        # Get scores
        scores = bm25.get_scores(tokenized_query)
        
        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    'id': all_docs[idx]['id'],
                    'content': all_docs[idx]['content'],
                    'metadata': all_docs[idx].get('metadata', {}),
                    'score': float(scores[idx])
                })
        
        return results
    
    async def _search_qdrant(
        self,
        query_embedding: np.ndarray,
        source_filter: Optional[List[KnowledgeSource]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Search in Qdrant vector database"""
        
        client = self.vector_stores['qdrant']
        collection_name = "financial_knowledge"
        
        # Build filter
        filter_dict = None
        if source_filter:
            filter_dict = {
                "must": [
                    {
                        "key": "source",
                        "match": {"any": [s.value for s in source_filter]}
                    }
                ]
            }
        
        # Search
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k,
            query_filter=filter_dict
        )
        
        # Format results
        results = []
        for hit in search_result:
            results.append({
                'id': hit.payload['doc_id'],
                'content': hit.payload['chunk_text'],
                'metadata': hit.payload,
                'score': hit.score
            })
        
        return results
    
    async def _search_chroma(
        self,
        query_embedding: np.ndarray,
        source_filter: Optional[List[KnowledgeSource]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Search in Chroma vector database"""
        
        chroma_db = self.vector_stores['chroma']
        
        # Build filter
        where_clause = None
        if source_filter:
            where_clause = {
                "source": {"$in": [s.value for s in source_filter]}
            }
        
        # Search
        results = chroma_db.similarity_search_with_score(
            query=query_embedding,
            k=top_k,
            filter=where_clause
        )
        
        # Format results
        formatted = []
        for doc, score in results:
            formatted.append({
                'id': doc.metadata.get('doc_id', 'unknown'),
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score)
            })
        
        return formatted
    
    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Dict[str, Any]]],
        weights: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Combine multiple result lists using reciprocal rank fusion"""
        
        if not weights:
            weights = [1.0] * len(result_lists)
        
        # Calculate reciprocal rank scores
        doc_scores = {}
        
        for results, weight in zip(result_lists, weights):
            for rank, result in enumerate(results):
                doc_id = result['id']
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'score': 0,
                        'result': result
                    }
                
                # Reciprocal rank score
                doc_scores[doc_id]['score'] += weight / (rank + 1)
        
        # Sort by combined score
        sorted_results = sorted(
            doc_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [r['result'] for r in sorted_results]
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder or LLM"""
        
        if not self.reranker:
            # Simple relevance scoring based on keyword overlap
            reranked = []
            query_terms = set(query.lower().split())
            
            for result in results:
                content_terms = set(result['content'].lower().split())
                overlap = len(query_terms & content_terms)
                
                # Adjust score based on overlap
                adjusted_score = result['score'] * (1 + overlap * 0.1)
                result['score'] = adjusted_score
                reranked.append(result)
            
            # Sort by adjusted score
            reranked.sort(key=lambda x: x['score'], reverse=True)
            return reranked[:top_k]
        
        # Use reranker model if available
        # This would use a cross-encoder for more accurate reranking
        return results[:top_k]
    
    async def _cache_documents(self, documents: List[KnowledgeDocument]):
        """Cache documents in Redis for fast access"""
        
        for doc in documents:
            key = f"rag_doc:{doc.id}"
            value = json.dumps({
                'id': doc.id,
                'source': doc.source.value,
                'type': doc.type.value,
                'title': doc.title,
                'content': doc.content,
                'metadata': doc.metadata,
                'chunks': doc.chunks
            })
            
            self.redis_client.setex(key, 86400 * 7, value)  # 7 days cache
    
    async def _get_cached_documents(
        self,
        source_filter: Optional[List[KnowledgeSource]]
    ) -> List[Dict[str, Any]]:
        """Get cached documents from Redis"""
        
        pattern = "rag_doc:*"
        docs = []
        
        for key in self.redis_client.scan_iter(pattern):
            doc_data = self.redis_client.get(key)
            if doc_data:
                doc = json.loads(doc_data)
                
                # Apply source filter
                if source_filter:
                    if doc['source'] in [s.value for s in source_filter]:
                        docs.append(doc)
                else:
                    docs.append(doc)
        
        return docs
    
    async def _store_index_metadata(self, metadata: Dict[str, Any]):
        """Store indexing metadata"""
        
        key = f"rag_index_meta:{metadata['source']}:{datetime.utcnow().timestamp()}"
        self.redis_client.setex(
            key,
            86400 * 30,  # 30 days
            json.dumps(metadata)
        )
    
    def _detect_document_type(self, document: Dict[str, Any]) -> DocumentType:
        """Detect document type from content or metadata"""
        
        if 'type' in document:
            return DocumentType(document['type'])
        
        if 'path' in document:
            path = document['path'].lower()
            if path.endswith('.pdf'):
                return DocumentType.PDF
            elif path.endswith('.txt'):
                return DocumentType.TEXT
            elif path.endswith('.md'):
                return DocumentType.MARKDOWN
            elif path.endswith('.csv'):
                return DocumentType.CSV
            elif path.endswith('.json'):
                return DocumentType.JSON
        
        return DocumentType.TEXT
    
    async def _extract_content(
        self,
        document: Dict[str, Any],
        doc_type: DocumentType
    ) -> str:
        """Extract text content from document"""
        
        if 'content' in document:
            return document['content']
        
        if 'path' not in document:
            return ""
        
        path = document['path']
        
        if doc_type == DocumentType.PDF:
            loader = PyPDFLoader(path)
        elif doc_type == DocumentType.MARKDOWN:
            loader = UnstructuredMarkdownLoader(path)
        elif doc_type == DocumentType.CSV:
            loader = CSVLoader(path)
        elif doc_type == DocumentType.JSON:
            loader = JSONLoader(path)
        else:
            loader = TextLoader(path)
        
        try:
            documents = loader.load()
            return "\n".join([doc.page_content for doc in documents])
        except Exception as e:
            logger.error(f"Failed to extract content from {path}: {e}")
            return ""
    
    def _select_splitter(
        self,
        doc_type: DocumentType,
        source: KnowledgeSource
    ) -> Any:
        """Select appropriate text splitter based on document type and source"""
        
        if source in [KnowledgeSource.REGULATORY, KnowledgeSource.TAX_CODE]:
            return self.text_splitters['financial']
        elif doc_type == DocumentType.CSV:
            return self.text_splitters['token']
        else:
            return self.text_splitters['recursive']
    
    def _enrich_metadata(
        self,
        document: Dict[str, Any],
        source: KnowledgeSource
    ) -> Dict[str, Any]:
        """Enrich document metadata with additional information"""
        
        metadata = document.get('metadata', {})
        
        # Add source information
        metadata['source'] = source.value
        metadata['indexed_at'] = datetime.utcnow().isoformat()
        
        # Add domain-specific tags
        if source == KnowledgeSource.TAX_CODE:
            metadata['tags'] = ['tax', 'compliance', 'regulatory']
        elif source == KnowledgeSource.INVESTMENT_STRATEGIES:
            metadata['tags'] = ['investment', 'strategy', 'portfolio']
        
        # Add temporal information if available
        if 'date' in document:
            metadata['document_date'] = document['date']
            metadata['age_days'] = (datetime.utcnow() - datetime.fromisoformat(document['date'])).days
        
        return metadata
    
    def _generate_doc_id(self, content: str) -> str:
        """Generate unique ID for document"""
        
        return hashlib.md5(content.encode()).hexdigest()
    
    async def update_knowledge_base(
        self,
        source: KnowledgeSource,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update knowledge base with new documents"""
        
        # Index new documents
        result = await self.index_documents(documents, source)
        
        # Clear relevant caches
        pattern = f"rag_doc:*"
        for key in self.redis_client.scan_iter(pattern):
            self.redis_client.delete(key)
        
        # Log update
        logger.info(f"Updated knowledge base for {source.value}: {result}")
        
        return result
    
    async def get_relevant_context(
        self,
        query: str,
        context_type: str
    ) -> str:
        """Get relevant context for a specific query type"""
        
        # Map context types to knowledge sources
        source_mapping = {
            'tax': [KnowledgeSource.TAX_CODE],
            'regulation': [KnowledgeSource.REGULATORY],
            'investment': [KnowledgeSource.INVESTMENT_STRATEGIES, KnowledgeSource.MARKET_ANALYSIS],
            'planning': [KnowledgeSource.FINANCIAL_PLANNING],
            'market': [KnowledgeSource.MARKET_ANALYSIS, KnowledgeSource.ECONOMIC_INDICATORS]
        }
        
        sources = source_mapping.get(context_type, None)
        
        # Retrieve relevant documents
        result = await self.retrieve(
            query,
            source_filter=sources,
            top_k=5,
            hybrid_search=True
        )
        
        # Combine document contents
        context = "\n\n".join([
            f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
            for doc in result.documents
        ])
        
        return context