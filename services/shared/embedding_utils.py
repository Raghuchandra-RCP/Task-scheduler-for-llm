"""
Shared Embedding Utilities
Common embedding generation and persistence utilities for both patient-to-trial and trial-to-patient matching
Uses Clinical Longformer embeddings via Hugging Face
Supports up to 4096 tokens with automatic chunking for longer texts
"""

import json
import numpy as np
import pickle
import faiss
import torch
from pathlib import Path
from typing import List, Dict, Any, Tuple
from transformers import AutoModel, AutoTokenizer
from datetime import datetime

class EmbeddingUtils:
    def __init__(self):
        """
        Initialize embedding utilities using Clinical Longformer
        Supports up to 4096 tokens with automatic chunking for longer texts
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Model instance (lazy loaded)
        self.model = None
        self.tokenizer = None
        
        # Model configuration
        self.model_name = "yikuan8/Clinical-Longformer"
        
        # Token limits
        self.max_tokens = 4096
        self.chunk_overlap = 200  # Overlap tokens between chunks for context preservation
        
        # Directory structure
        self.persist_dir = Path("persist")
        self.embeddings_dir = self.persist_dir / "embeddings"
        self.trials_dir = self.embeddings_dir / "trials"
        self.patients_dir = self.embeddings_dir / "patients"
        
        # Create directories
        for dir_path in [self.persist_dir, self.embeddings_dir, self.trials_dir, self.patients_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Clinical Longformer uses 768-dimensional embeddings
        self.dimension = 768
        
        print(f"📌 Embedding Model: Clinical Longformer")
        print(f"   - Token limit: {self.max_tokens}")
        print(f"   - Embedding dimension: {self.dimension}")

    def load_model(self):
        """Load Clinical Longformer model"""
        if self.model is None:
            print(f"Loading Clinical Longformer model: {self.model_name}")
            print("This may take a few minutes on first run (downloading model)...")
            try:
                self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model.eval()
                print(f"✅ Clinical Longformer loaded successfully")
                print(f"   - Max token length: {self.max_tokens}")
                print(f"   - Embedding dimension: {self.dimension}")
            except Exception as e:
                print(f"❌ Error loading Clinical Longformer: {e}")
                raise
        return self.model, self.tokenizer

    def _chunk_text(self, text: str, tokenizer, max_chunk_length: int, overlap: int) -> List[str]:
        """
        Split long text into overlapping chunks to preserve information
        Uses token-level chunking to ensure accurate token counts
        """
        # Tokenize the entire text first (without special tokens for accurate count)
        tokens = tokenizer.encode(text, add_special_tokens=False, max_length=None)
        
        # If text fits in one chunk, return as is
        if len(tokens) <= max_chunk_length:
            return [text]
        
        # Split into chunks with overlap
        chunks = []
        step_size = max_chunk_length - overlap
        
        for i in range(0, len(tokens), step_size):
            chunk_tokens = tokens[i:i + max_chunk_length]
            # Decode chunk tokens back to text
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append(chunk_text)
        
        return chunks

    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> np.ndarray:
        """
        Generate embedding using Clinical Longformer
        
        Args:
            text: Input text to embed
            task_type: Kept for compatibility (not used - single model for both queries and documents)
        
        Returns:
            numpy array of embedding (768 dimensions)
        """
        try:
            # Load model (single model for both queries and documents)
            model, tokenizer = self.load_model()
            
            # Check token count
            encoded = tokenizer.encode(text, add_special_tokens=False)
            token_count = len(encoded)
            
            # Direct processing if within token limit
            if token_count <= self.max_tokens:
                inputs = tokenizer(
                    text, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=self.max_tokens, 
                    padding=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model(**inputs)
                    embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy().flatten()
                
                return embedding.astype(np.float32)
            
            # Chunking for texts exceeding 4096 tokens (preserves all information)
            print(f"⚠️  Text exceeds {self.max_tokens} tokens ({token_count:,} tokens). Using chunking to preserve all information...")
            chunks = self._chunk_text(
                text, 
                tokenizer, 
                max_chunk_length=self.max_tokens - 50,  # Leave room for special tokens
                overlap=self.chunk_overlap
            )
            print(f"   Split into {len(chunks)} overlapping chunks")
            
            chunk_embeddings = []
            for chunk in chunks:
                inputs = tokenizer(
                    chunk, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=self.max_tokens, 
                    padding=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model(**inputs)
                    chunk_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy().flatten()
                    chunk_embeddings.append(chunk_emb)
            
            # Mean pooling to combine chunk embeddings
            if chunk_embeddings:
                final_embedding = np.mean(chunk_embeddings, axis=0)
                print(f"   ✅ Generated embedding from {len(chunk_embeddings)} chunks (mean pooling)")
                return final_embedding.astype(np.float32)
            else:
                raise ValueError("No chunks generated")
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(self.dimension, dtype=np.float32)

    def save_embeddings_matrix(self, embeddings: List[np.ndarray], target_dir: Path, filename: str) -> str:
        """Save embeddings matrix to file"""
        try:
            embeddings_matrix = np.vstack(embeddings)
            matrix_file = target_dir / filename
            np.save(matrix_file, embeddings_matrix)
            return str(matrix_file)
        except Exception as e:
            print(f"Error saving embeddings matrix: {e}")
            return ""

    def save_individual_embeddings(self, embeddings: List[np.ndarray], metadata: Dict[str, Any], 
                                 target_dir: Path, prefix: str) -> Dict[str, str]:
        """Save individual embeddings and metadata"""
        try:
            saved_files = {}
            
            # Save individual embeddings
            for i, embedding in enumerate(embeddings):
                entity_id = list(metadata.keys())[i] if i < len(metadata) else f"{prefix}_{i}"
                embedding_file = target_dir / f"{prefix}_{entity_id}.npy"
                np.save(embedding_file, embedding)
                saved_files[entity_id] = str(embedding_file)
            
            # Save metadata
            metadata_file = target_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            saved_files['metadata'] = str(metadata_file)
            
            return saved_files
        except Exception as e:
            print(f"Error saving individual embeddings: {e}")
            return {}

    def create_faiss_index(self, embeddings: List[np.ndarray], index_type: str = "cosine") -> faiss.Index:
        """Create FAISS index for embeddings"""
        try:
            embeddings_matrix = np.vstack(embeddings)
            
            if index_type == "cosine":
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings_matrix)
                index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            else:
                index = faiss.IndexFlatL2(self.dimension)  # L2 distance
            
            index.add(embeddings_matrix)
            return index
        except Exception as e:
            print(f"Error creating FAISS index: {e}")
            return None

    def save_faiss_index(self, index: faiss.Index, target_dir: Path, filename: str) -> str:
        """Save FAISS index to file"""
        try:
            index_file = target_dir / filename
            with open(index_file, 'wb') as f:
                pickle.dump(index, f)
            return str(index_file)
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
            return ""

    def load_faiss_index(self, index_file: Path) -> faiss.Index:
        """Load FAISS index from file"""
        try:
            with open(index_file, 'rb') as f:
                index = pickle.load(f)
            return index
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            return None

    def load_metadata(self, metadata_file: Path) -> Dict[str, Any]:
        """Load metadata from file"""
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {}

    def search_similar(self, query_embedding: np.ndarray, index: faiss.Index, 
                      metadata: Dict[str, Any], k: int = 20) -> List[Dict[str, Any]]:
        """Search for similar embeddings using FAISS index"""
        try:
            scores, indices = index.search(query_embedding.reshape(1, -1), k=min(k, index.ntotal))
            
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if str(idx) in metadata:
                    result = metadata[str(idx)].copy()
                    result['index'] = int(idx)
                    result['similarity_score'] = float(score)
                    results.append(result)
            
            return results
        except Exception as e:
            print(f"Error searching similar embeddings: {e}")
            return []

    def create_global_cache_index(self, trial_info: Dict, patient_info: Dict) -> str:
        """Create global cache index for all embeddings"""
        try:
            global_index = {
                "created_at": datetime.now().isoformat(),
                "trials": trial_info,
                "patients": patient_info
            }
            
            cache_index_file = self.embeddings_dir / "cache_index.json"
            with open(cache_index_file, 'w') as f:
                json.dump(global_index, f, indent=2)
            
            return str(cache_index_file)
        except Exception as e:
            print(f"Error creating global cache index: {e}")
            return ""
