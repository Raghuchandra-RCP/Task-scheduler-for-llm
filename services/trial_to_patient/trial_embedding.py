"""
Trial-to-Patient Embedding Generator
Generates and persists embeddings for clinical trials to enable patient matching
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from services.shared.database_utils import DatabaseUtils
from services.shared.embedding_utils import EmbeddingUtils

class TrialEmbeddingGenerator:
    def __init__(self):
        self.db_utils = DatabaseUtils()
        self.embedding_utils = EmbeddingUtils()
        
        # Trial-specific directories
        self.trials_dir = self.embedding_utils.trials_dir

    def _check_trial_embedding_exists(self, trial_id: str) -> bool:
        """Check if trial embedding already exists"""
        try:
            embedding_file = self.trials_dir / f"trial_{trial_id}.npy"
            return embedding_file.exists()
        except Exception as e:
            print(f"Error checking embedding for trial {trial_id}: {e}")
            return False

    def generate_trial_embeddings(self, trials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate embeddings for multiple trials (only new trials)"""
        print(f"📊 Trial Embedding Generation Summary:")
        print(f"   Total trials: {len(trials)}")
        
        # Separate new trials from existing ones
        new_trials = []
        existing_trials = []
        
        for trial in trials:
            trial_id = trial['trial_id']
            if self._check_trial_embedding_exists(trial_id):
                existing_trials.append(trial)
                print(f"✅ Trial {trial_id} already has embeddings - skipping")
            else:
                new_trials.append(trial)
        
        print(f"   Existing trials (skipped): {len(existing_trials)}")
        print(f"   New trials (to process): {len(new_trials)}")
        
        if not new_trials:
            print("🎉 All trials already have embeddings - no new generation needed!")
            return {
                "embeddings": [],
                "metadata": {},
                "total_trials": len(trials),
                "new_trials": 0,
                "existing_trials": len(existing_trials),
                "status": "all_existing"
            }
        
        print(f"🆕 Generating embeddings for {len(new_trials)} NEW trials...")
        
        trial_embeddings = []
        trial_metadata = {}
        
        for i, trial in enumerate(new_trials):
            print(f"Processing trial {i+1}/{len(new_trials)}: {trial['trial_id']}")
            
            # Generate embedding for trial text
            embedding = self.embedding_utils.generate_embedding(
                trial['combined_trial_text'], 
                task_type="retrieval_document"
            )
            trial_embeddings.append(embedding)
            
            # Store metadata
            trial_metadata[trial['trial_id']] = {
                "title": trial['title'],
                "condition": trial['condition'],
                "phase": trial['phase'],
                "status": trial['status'],
                "investigator": trial['investigator'],
                "created_date": trial['created_date'],
                "patients_matched": trial['patients_matched'],
                "matching_status": trial['matching_status'],
                "embedding_index": i
            }
            
            # Save individual trial embedding
            trial_file = self.trials_dir / f"trial_{trial['trial_id']}.npy"
            np.save(trial_file, embedding)
        
        return {
            "embeddings": trial_embeddings,
            "metadata": trial_metadata,
            "total_trials": len(trials),
            "new_trials": len(new_trials),
            "existing_trials": len(existing_trials),
            "status": "new_generated"
        }

    def _load_existing_embeddings_and_metadata(self):
        """Load existing embeddings and metadata from disk"""
        try:
            existing_embeddings = []
            existing_metadata = {}
            
            # Load existing metadata
            metadata_file = self.trials_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
            
            # Load existing embeddings in order
            if existing_metadata:
                # Sort by embedding_index to maintain order
                sorted_trials = sorted(existing_metadata.items(), key=lambda x: x[1].get('embedding_index', 999999))
                
                for trial_id, meta in sorted_trials:
                    embedding_file = self.trials_dir / f"trial_{trial_id}.npy"
                    if embedding_file.exists():
                        embedding = np.load(embedding_file)
                        existing_embeddings.append(embedding)
            
            return existing_embeddings, existing_metadata
        except Exception as e:
            print(f"Error loading existing embeddings: {e}")
            return [], {}

    def save_trial_embeddings(self, embedding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save trial embeddings and create FAISS index (combines existing + new)"""
        try:
            new_embeddings = embedding_data.get("embeddings", [])
            new_metadata = embedding_data.get("metadata", {})
            
            # If no new embeddings were generated, return existing info
            if not new_embeddings:
                print("No new embeddings to save - using existing embeddings")
                # Load existing to get counts
                existing_embeddings, existing_metadata = self._load_existing_embeddings_and_metadata()
                return {
                    "total_trials": embedding_data["total_trials"],
                    "new_trials": embedding_data.get("new_trials", 0),
                    "existing_trials": embedding_data.get("existing_trials", 0),
                    "total_with_existing": len(existing_metadata),
                    "status": embedding_data.get("status", "no_new_embeddings"),
                    "message": "All trials already have embeddings"
                }
            
            print(f"📦 Loading existing embeddings and metadata...")
            # Load existing embeddings and metadata
            existing_embeddings, existing_metadata = self._load_existing_embeddings_and_metadata()
            
            print(f"   Existing trials: {len(existing_embeddings)}")
            print(f"   New trials: {len(new_embeddings)}")
            
            # Combine existing + new embeddings
            all_embeddings = existing_embeddings + new_embeddings
            
            # Update embedding_index for new trials (continue from existing count)
            next_index = len(existing_embeddings)
            for trial_id, meta in new_metadata.items():
                meta['embedding_index'] = next_index
                next_index += 1
            
            # Merge metadata (existing + new)
            all_metadata = {**existing_metadata, **new_metadata}
            
            print(f"   Total combined: {len(all_embeddings)} trials")
            
            # Save embeddings matrix (all trials)
            matrix_file = self.embedding_utils.save_embeddings_matrix(
                all_embeddings, self.trials_dir, "trial_embeddings_matrix.npy"
            )
            
            # Save individual embeddings (already saved per trial, but update metadata)
            # Save metadata.json with ALL trials
            metadata_file = self.trials_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(all_metadata, f, indent=2, ensure_ascii=False)
            
            # Create FAISS index with ALL embeddings (existing + new)
            print(f"🔄 Rebuilding FAISS index with {len(all_embeddings)} trials...")
            trial_index = self.embedding_utils.create_faiss_index(all_embeddings, "cosine")
            
            # Save FAISS index
            index_file = self.embedding_utils.save_faiss_index(
                trial_index, self.trials_dir, "faiss_index.pkl"
            )
            
            print(f"✅ Trial embeddings saved to: {self.trials_dir}")
            print(f"   FAISS index now contains: {trial_index.ntotal if trial_index else 0} trials")
            
            return {
                "total_trials": embedding_data["total_trials"],
                "total_with_existing": len(all_metadata),
                "new_trials": embedding_data.get("new_trials", 0),
                "existing_trials": embedding_data.get("existing_trials", 0),
                "embedding_dimension": self.embedding_utils.dimension,
                "matrix_shape": np.vstack(all_embeddings).shape,
                "metadata_file": str(metadata_file),
                "matrix_file": matrix_file,
                "faiss_index_file": index_file,
                "index_size": trial_index.ntotal if trial_index else 0,
                "status": embedding_data.get("status", "completed")
            }
            
        except Exception as e:
            print(f"Error saving trial embeddings: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def run_trial_embedding_generation(self) -> Dict[str, Any]:
        """Main method to run trial embedding generation"""
        print("Starting trial embedding generation for patient matching...")
        
        # Get trial data
        trials = self.db_utils.get_detailed_trial_data()
        if not trials:
            print("No trial data found!")
            return {}
        
        print(f"Found {len(trials)} trials")
        
        # Generate embeddings
        embedding_data = self.generate_trial_embeddings(trials)
        
        # Save embeddings
        save_info = self.save_trial_embeddings(embedding_data)
        
        if save_info:
            print(f"\nTrial Embedding Generation Summary:")
            print(f"Total trials: {save_info['total_trials']}")
            print(f"New trials processed: {save_info.get('new_trials', 0)}")
            print(f"Existing trials (skipped): {save_info.get('existing_trials', 0)}")
            
            if save_info.get('status') == 'all_existing':
                print(f"Status: All trials already have embeddings - no new generation needed!")
            else:
                print(f"Embedding dimension: {save_info.get('embedding_dimension', 'N/A')}")
                print(f"Matrix shape: {save_info.get('matrix_shape', 'N/A')}")
                print(f"FAISS index size: {save_info.get('index_size', 'N/A')}")
            
            print(f"Files saved to: {self.trials_dir}")
        
        return save_info

def main():
    """Main function to run trial embedding generation"""
    generator = TrialEmbeddingGenerator()
    results = generator.run_trial_embedding_generation()
    
    if results:
        print("\nTrial embedding generation completed successfully!")
    else:
        print("\nTrial embedding generation failed!")

if __name__ == "__main__":
    main()
