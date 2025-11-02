"""
Script to regenerate trial embeddings from current database (47 trials)
This will:
1. Backup existing embeddings (optional)
2. Clear old embeddings (932 trials)
3. Regenerate embeddings for current trials in database (47 trials)
4. Recreate FAISS index with only current trials
"""

import shutil
from pathlib import Path
from datetime import datetime
from services.trial_to_patient.trial_embedding import TrialEmbeddingGenerator
from services.shared.embedding_utils import EmbeddingUtils

def backup_existing_embeddings(trials_dir: Path, backup_name: str = None):
    """Backup existing trial embeddings before clearing"""
    if backup_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"trials_backup_{timestamp}"
    
    backup_dir = trials_dir.parent / backup_name
    
    if trials_dir.exists():
        print(f"📦 Creating backup: {backup_dir}")
        shutil.copytree(trials_dir, backup_dir)
        print(f"✅ Backup created: {backup_dir}")
        return backup_dir
    else:
        print("⚠️  No existing embeddings to backup")
        return None

def clear_old_embeddings(trials_dir: Path):
    """Clear all old trial embeddings"""
    print(f"\n🗑️  Clearing old embeddings from: {trials_dir}")
    
    if not trials_dir.exists():
        print("⚠️  Embeddings directory doesn't exist")
        return
    
    # Count files before deletion
    trial_files = list(trials_dir.glob("trial_*.npy"))
    other_files = [
        trials_dir / "faiss_index.pkl",
        trials_dir / "metadata.json",
        trials_dir / "trial_embeddings_matrix.npy"
    ]
    
    total_files = len(trial_files) + len([f for f in other_files if f.exists()])
    
    if total_files == 0:
        print("✅ No files to clear - directory is already empty")
        return
    
    print(f"   Found {len(trial_files)} trial embedding files")
    print(f"   Found {len([f for f in other_files if f.exists()])} index/metadata files")
    
    # Delete individual trial embeddings
    deleted_count = 0
    for trial_file in trial_files:
        try:
            trial_file.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"   ⚠️  Error deleting {trial_file.name}: {e}")
    
    # Delete index and metadata files
    for file_path in other_files:
        if file_path.exists():
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️  Error deleting {file_path.name}: {e}")
    
    print(f"✅ Cleared {deleted_count} files")
    print(f"   Old embeddings removed: {len(trial_files)} trial files")
    print(f"   Index files removed: {len([f for f in other_files if f.exists()])}")

def regenerate_embeddings():
    """Regenerate embeddings for current trials in database (force regenerate all)"""
    print("\n" + "=" * 80)
    print("REGENERATING TRIAL EMBEDDINGS FROM CURRENT DATABASE")
    print("=" * 80)
    
    from services.shared.database_utils import DatabaseUtils
    from services.shared.embedding_utils import EmbeddingUtils
    import numpy as np
    
    db_utils = DatabaseUtils()
    embedding_utils = EmbeddingUtils()
    trials_dir = embedding_utils.trials_dir
    
    # Get current trials from database
    print("📊 Getting current trials from database...")
    trials = db_utils.get_detailed_trial_data()
    
    if not trials:
        print("❌ No trial data found in database!")
        return False
    
    print(f"✅ Found {len(trials)} trials in database")
    
    # Generate embeddings for ALL trials (force regenerate)
    print(f"\n🔄 Generating embeddings for {len(trials)} trials...")
    trial_embeddings = []
    trial_metadata = {}
    
    for i, trial in enumerate(trials, 1):
        trial_id = trial['trial_id']
        print(f"   Processing trial {i}/{len(trials)}: {trial_id}")
        
        # Build combined trial text
        combined_text = trial.get('combined_trial_text', '')
        
        # Generate embedding
        embedding = embedding_utils.generate_embedding(
            combined_text,
            task_type="retrieval_document"
        )
        trial_embeddings.append(embedding)
        
        # Store metadata
        trial_metadata[trial_id] = {
            "title": trial.get('title', ''),
            "condition": trial.get('condition', ''),
            "phase": trial.get('phase', ''),
            "status": trial.get('status', ''),
            "investigator": trial.get('investigator', ''),
            "created_date": trial.get('created_date', ''),
            "patients_matched": trial.get('patients_matched', 0),
            "matching_status": trial.get('matching_status', 'pending'),
            "embedding_index": i - 1
        }
        
        # Save individual trial embedding
        trial_file = trials_dir / f"trial_{trial_id}.npy"
        np.save(trial_file, embedding)
    
    # Save embeddings matrix
    print(f"\n💾 Saving embeddings matrix...")
    matrix_file = embedding_utils.save_embeddings_matrix(
        trial_embeddings, trials_dir, "trial_embeddings_matrix.npy"
    )
    
    # Save metadata - need to structure it for FAISS index matching
    # FAISS uses embedding_index (0, 1, 2...) as keys, not trial_id
    print(f"💾 Saving metadata...")
    import json
    metadata_file = trials_dir / "metadata.json"
    
    # Create metadata dict with trial_id as key (this is what the matcher expects)
    # Each entry should have embedding_index for FAISS matching
    final_metadata = {}
    for trial_id, meta in trial_metadata.items():
        final_metadata[trial_id] = meta
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(final_metadata, f, indent=2, ensure_ascii=False)
    
    # Create and save FAISS index
    print(f"💾 Creating FAISS index...")
    trial_index = embedding_utils.create_faiss_index(trial_embeddings, "cosine")
    index_file = embedding_utils.save_faiss_index(
        trial_index, trials_dir, "faiss_index.pkl"
    )
    
    print("\n" + "=" * 80)
    print("✅ EMBEDDING REGENERATION COMPLETE!")
    print("=" * 80)
    print(f"Total trials processed: {len(trials)}")
    print(f"FAISS index size: {trial_index.ntotal if trial_index else 0}")
    print(f"Embedding dimension: {embedding_utils.dimension}")
    print(f"Matrix shape: {np.vstack(trial_embeddings).shape}")
    print(f"Files saved to: {trials_dir}")
    print(f"  - FAISS index: {index_file}")
    print(f"  - Metadata: {metadata_file}")
    print(f"  - Matrix: {matrix_file}")
    
    return True

def main():
    """Main function"""
    print("=" * 80)
    print("TRIAL EMBEDDING REGENERATION SCRIPT")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Backup existing embeddings (optional)")
    print("  2. Clear old embeddings (932 trials)")
    print("  3. Regenerate embeddings for current trials in database (47 trials)")
    print("  4. Recreate FAISS index with only current trials")
    print("\n⚠️  WARNING: This will remove all existing trial embeddings!")
    
    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return
    
    # Setup paths
    embedding_utils = EmbeddingUtils()
    trials_dir = embedding_utils.trials_dir
    
    print(f"\n📍 Embeddings directory: {trials_dir}")
    
    # Step 1: Backup (optional)
    backup_response = input("\nDo you want to backup existing embeddings? (yes/no): ").strip().lower()
    if backup_response in ['yes', 'y']:
        backup_dir = backup_existing_embeddings(trials_dir)
        if backup_dir:
            print(f"✅ Backup saved to: {backup_dir}")
    else:
        print("⏭️  Skipping backup")
    
    # Step 2: Clear old embeddings
    print("\n" + "=" * 80)
    print("STEP 1: CLEARING OLD EMBEDDINGS")
    print("=" * 80)
    clear_old_embeddings(trials_dir)
    
    # Step 3: Regenerate embeddings
    print("\n" + "=" * 80)
    print("STEP 2: REGENERATING EMBEDDINGS FROM CURRENT DATABASE")
    print("=" * 80)
    success = regenerate_embeddings()
    
    if success:
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! Trial embeddings have been regenerated!")
        print("=" * 80)
        print("\nNow when you run patient-to-trial matching:")
        print("  - FAISS will only contain current 47 trials from database")
        print("  - All shortlisted trials will exist in database")
        print("  - No more 'trial not found' errors!")
        print("\n✅ You can now run:")
        print("   python patient_to_trial_pipeline.py --patient-id 2")
    else:
        print("\n❌ Failed to regenerate embeddings. Please check the errors above.")

if __name__ == "__main__":
    main()

