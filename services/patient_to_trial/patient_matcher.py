"""
Patient-to-Trial Matcher
Finds suitable clinical trials for a specific patient using hybrid matching
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from services.shared.database_utils import DatabaseUtils
from services.shared.embedding_utils import EmbeddingUtils
from rank_bm25 import BM25Okapi
import re

class PatientMatcher:
    def __init__(self):
        self.db_utils = DatabaseUtils()
        self.embedding_utils = EmbeddingUtils()
        
        # Load existing embeddings and indices
        self.trial_index = None
        self.trial_metadata = {}
        self.trial_texts = []
        self.bm25_trials = None
        
        self.load_trial_data()

    def load_trial_data(self):
        """Load trial embeddings and metadata"""
        try:
            # Load trial FAISS index
            trial_faiss_file = self.embedding_utils.trials_dir / "faiss_index.pkl"
            if trial_faiss_file.exists():
                self.trial_index = self.embedding_utils.load_faiss_index(trial_faiss_file)
                print(f"Loaded trial FAISS index with {self.trial_index.ntotal} vectors")
            
            # Load trial metadata
            trial_metadata_file = self.embedding_utils.trials_dir / "metadata.json"
            if trial_metadata_file.exists():
                self.trial_metadata = self.embedding_utils.load_metadata(trial_metadata_file)
                print(f"Loaded metadata for {len(self.trial_metadata)} trials")
            
            # Load trial texts for BM25
            self.load_trial_texts()
            
        except Exception as e:
            print(f"Error loading trial data: {e}")

    def load_trial_texts(self):
        """Load trial texts for BM25 indexing"""
        try:
            trials = self.db_utils.get_detailed_trial_data()
            
            self.trial_texts = []
            for trial in trials:
                trial_text = f"{trial['title']} {trial['condition']} {trial['phase']} {trial['status']} {trial['investigator']}"
                self.trial_texts.append(self.tokenize_text(trial_text))
            
            # Create BM25 index for trials
            if self.trial_texts:
                self.bm25_trials = BM25Okapi(self.trial_texts)
                print(f"Created BM25 index for {len(self.trial_texts)} trials")
            
        except Exception as e:
            print(f"Error loading trial texts: {e}")

    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25"""
        if not text:
            return []
        
        # Simple tokenization - can be improved with medical tokenizer
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text.split()
        
        # Filter out very short tokens
        tokens = [token for token in tokens if len(token) > 2]
        
        return tokens

    def get_embedding_similarity(self, query_embedding: np.ndarray) -> List[Tuple[int, float]]:
        """Get similarity scores using FAISS index"""
        try:
            if self.trial_index:
                scores, indices = self.trial_index.search(query_embedding.reshape(1, -1), k=min(50, self.trial_index.ntotal))
                return list(zip(indices[0], scores[0]))
            else:
                return []
        except Exception as e:
            print(f"Error getting embedding similarity: {e}")
            return []

    def get_bm25_similarity(self, query_text: str) -> List[Tuple[int, float]]:
        """Get similarity scores using BM25"""
        try:
            query_tokens = self.tokenize_text(query_text)
            
            if self.bm25_trials:
                scores = self.bm25_trials.get_scores(query_tokens)
                indexed_scores = [(i, score) for i, score in enumerate(scores)]
                indexed_scores.sort(key=lambda x: x[1], reverse=True)
                return indexed_scores[:50]
            else:
                return []
        except Exception as e:
            print(f"Error getting BM25 similarity: {e}")
            return []

    def hybrid_search_trials_for_patient(self, patient_data: Dict[str, Any], alpha: float = 0.7) -> List[Dict[str, Any]]:
        """Find suitable trials for a patient using hybrid matching"""
        try:
            print(f"Finding trials for patient MRN: {patient_data['mrn']}")
            
            # Use complete patient data for better accuracy (contains full medical context)
            combined_text = patient_data.get('combined_text', '')
            
            if not combined_text:
                print(f"❌ No combined_text found for patient {patient_data['patient_id']}")
                return []
            
            # Generate embedding for complete patient data (full medical record)
            patient_embedding = self.embedding_utils.generate_embedding(
                combined_text, 
                task_type="retrieval_query"
            )
            
            # Get embedding similarity
            embedding_scores = self.get_embedding_similarity(patient_embedding)
            
            # Get BM25 similarity (using complete patient data)
            bm25_scores = self.get_bm25_similarity(combined_text)
            
            # Normalize scores
            embedding_scores_dict = {idx: score for idx, score in embedding_scores}
            bm25_scores_dict = {idx: score for idx, score in bm25_scores}
            
            # Combine scores
            combined_scores = {}
            all_indices = set(embedding_scores_dict.keys()) | set(bm25_scores_dict.keys())
            
            for idx in all_indices:
                embedding_score = embedding_scores_dict.get(idx, 0.0)
                bm25_score = bm25_scores_dict.get(idx, 0.0)
                
                # Normalize BM25 score (assuming max BM25 score is around 10)
                normalized_bm25 = min(bm25_score / 10.0, 1.0)
                
                # Weighted combination
                combined_score = alpha * embedding_score + (1 - alpha) * normalized_bm25
                combined_scores[idx] = combined_score
            
            # Sort by combined score
            sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Get metadata for top results
            results = []
            for idx, score in sorted_results[:20]:  # Top 20 trials
                # Find trial with matching embedding_index
                trial_id = None
                for tid, metadata in self.trial_metadata.items():
                    if metadata.get('embedding_index') == idx:
                        trial_id = tid
                        break
                
                if trial_id:
                    result = self.trial_metadata[trial_id].copy()
                    result['trial_id'] = trial_id
                    result['index'] = idx
                    result['hybrid_score'] = score
                    result['embedding_score'] = embedding_scores_dict.get(idx, 0.0)
                    result['bm25_score'] = bm25_scores_dict.get(idx, 0.0)
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            return []

    def find_trials_for_patient(self, patient_id: int, age_range: Tuple[int, int] = None, 
                              gender: str = None, phase_filter: List[str] = None) -> Dict[str, Any]:
        """Find suitable trials for a specific patient"""
        try:
            # Get patient information
            patient_data = self.db_utils.get_patient_by_id(patient_id)
            if not patient_data:
                print(f"Patient {patient_id} not found")
                return {}
            
            print(f"Finding trials for patient: MRN {patient_data['mrn']}")
            print(f"Age: {patient_data['age']}, Gender: {patient_data['gender']}")
            
            # Perform hybrid search
            matching_trials = self.hybrid_search_trials_for_patient(patient_data)
            
            # Apply filters
            filtered_trials = []
            for trial in matching_trials:
                # Check phase filter
                if phase_filter:
                    trial_phase = trial.get('phase', '')
                    if trial_phase and trial_phase not in phase_filter:
                        continue
                
                filtered_trials.append(trial)
            
            print(f"Found {len(matching_trials)} trials before filtering")
            print(f"Found {len(filtered_trials)} trials after phase filtering")
            
            return {
                "patient_id": patient_id,
                "patient_info": patient_data,
                "matching_trials": filtered_trials[:20],  # Top 20 trials
                "total_matches": len(filtered_trials),
                "filters_applied": {
                    "age_range": age_range,
                    "gender": gender,
                    "phase_filter": phase_filter
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error finding trials for patient: {e}")
            return {}

def main():
    """Main function to test patient matching"""
    matcher = PatientMatcher()
    
    # Test with a specific patient
    patient_id = 64567  # Replace with actual patient ID
    results = matcher.find_trials_for_patient(
        patient_id=patient_id,
        phase_filter=["Phase I", "Phase II", "Phase III"]
    )
    
    print(f"\nPatient Trial Matching Results:")
    print(f"Patient: {results.get('patient_info', {}).get('mrn', 'Unknown')}")
    print(f"Total matches: {results.get('total_matches', 0)}")
    
    for i, trial in enumerate(results.get('matching_trials', [])[:5], 1):
        print(f"{i}. Trial: {trial.get('title', 'Unknown')}")
        print(f"   Condition: {trial.get('condition', 'Unknown')}")
        print(f"   Phase: {trial.get('phase', 'Unknown')}")
        print(f"   Hybrid Score: {trial.get('hybrid_score', 0):.4f}")
        print()

if __name__ == "__main__":
    main()
