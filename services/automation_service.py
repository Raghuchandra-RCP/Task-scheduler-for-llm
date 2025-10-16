"""
Automation Service for Clinical Trial Matching System
Handles batch processing of all patients and trials when automation is enabled
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from config import (
    AUTOMATION_ENABLED, 
    AUTOMATION_PATIENT_BATCH_SIZE, 
    AUTOMATION_TRIAL_BATCH_SIZE,
    USE_LLM_PROCESSING
)
from services.shared.database_utils import DatabaseUtils
from services.patient_to_trial.patient_embedding import PatientEmbeddingGenerator
from services.patient_to_trial.keyword_generator import PatientKeywordGenerator
from services.patient_to_trial.patient_matcher import PatientMatcher
from services.trial_to_patient.trial_embedding import TrialEmbeddingGenerator
from services.trial_to_patient.trial_matcher import TrialMatcher
from services.trial_to_patient.hybrid_matcher import HybridMatcher

class AutomationService:
    def __init__(self):
        self.db_utils = DatabaseUtils()
        self.patient_embedding_generator = PatientEmbeddingGenerator()
        self.patient_keyword_generator = PatientKeywordGenerator()
        self.patient_matcher = PatientMatcher()
        self.trial_embedding_generator = TrialEmbeddingGenerator()
        self.trial_matcher = TrialMatcher()
        self.hybrid_matcher = HybridMatcher()
        
        # Results directory
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
    async def run_full_automation(self) -> Dict[str, Any]:
        """Run complete automation process for all patients and trials"""
        if not AUTOMATION_ENABLED:
            logger.warning("Automation is disabled. Set AUTOMATION_ENABLED=true to run.")
            return {"status": "disabled", "message": "Automation is disabled"}
        
        logger.info("Starting full automation process...")
        automation_start = datetime.now()
        batch_id = f"automation_{automation_start.strftime('%Y%m%d_%H%M%S')}"
        
        results = {
            "batch_id": batch_id,
            "started_at": automation_start.isoformat(),
            "steps": {},
            "status": "running"
        }
        
        try:
            # Step 1: Process all patient embeddings
            logger.info("Step 1: Processing patient embeddings...")
            patient_embedding_results = await self.process_all_patient_embeddings(batch_id)
            results["steps"]["patient_embeddings"] = patient_embedding_results
            
            # Step 2: Process all trial embeddings
            logger.info("Step 2: Processing trial embeddings...")
            trial_embedding_results = await self.process_all_trial_embeddings(batch_id)
            results["steps"]["trial_embeddings"] = trial_embedding_results
            
            # Step 3: Generate keywords for all patients
            if USE_LLM_PROCESSING:
                logger.info("Step 3: Generating keywords for all patients...")
                keyword_results = await self.process_all_patient_keywords(batch_id)
                results["steps"]["patient_keywords"] = keyword_results
            
            # Step 4: Patient-to-Trial matching for all patients
            logger.info("Step 4: Patient-to-Trial matching...")
            patient_trial_results = await self.process_all_patient_trial_matches(batch_id)
            results["steps"]["patient_trial_matches"] = patient_trial_results
            
            # Step 5: Trial-to-Patient matching for all trials
            logger.info("Step 5: Trial-to-Patient matching...")
            trial_patient_results = await self.process_all_trial_patient_matches(batch_id)
            results["steps"]["trial_patient_matches"] = trial_patient_results
            
            # Mark automation as completed
            results["status"] = "completed"
            results["completed_at"] = datetime.now().isoformat()
            results["duration_minutes"] = (datetime.now() - automation_start).total_seconds() / 60
            
            logger.info(f"Automation completed successfully in {results['duration_minutes']:.2f} minutes")
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            results["failed_at"] = datetime.now().isoformat()
            
        # Save results
        self.save_automation_results(results)
        return results
    
    async def process_all_patient_embeddings(self, batch_id: str) -> Dict[str, Any]:
        """Process embeddings for all patients that need them"""
        logger.info("Processing patient embeddings...")
        
        # Get patients needing embeddings
        patients = self.db_utils.get_patients_needing_embeddings()
        
        if not patients:
            logger.info("No patients need embedding generation")
            return {"status": "completed", "message": "No patients need embeddings", "processed": 0}
        
        # Create batch log
        self.db_utils.create_processing_batch(
            batch_id, 
            "patient_embedding", 
            len(patients),
            {"batch_size": AUTOMATION_PATIENT_BATCH_SIZE}
        )
        
        processed = 0
        failed = 0
        
        # Process in batches
        for i in range(0, len(patients), AUTOMATION_PATIENT_BATCH_SIZE):
            batch = patients[i:i + AUTOMATION_PATIENT_BATCH_SIZE]
            logger.info(f"Processing patient embedding batch {i//AUTOMATION_PATIENT_BATCH_SIZE + 1}/{(len(patients)-1)//AUTOMATION_PATIENT_BATCH_SIZE + 1}")
            
            for patient in batch:
                try:
                    # Generate embedding
                    embedding_result = self.patient_embedding_generator.generate_patient_embedding(
                        patient["patient_id"], 
                        patient["combined_text"]
                    )
                    
                    if embedding_result:
                        # Update status
                        self.db_utils.update_patient_processing_status(
                            patient["patient_id"], 
                            embedding_generated=True
                        )
                        processed += 1
                    else:
                        failed += 1
                        self.db_utils.update_patient_processing_status(
                            patient["patient_id"], 
                            error_message="Failed to generate embedding"
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing patient {patient['patient_id']}: {e}")
                    failed += 1
                    self.db_utils.update_patient_processing_status(
                        patient["patient_id"], 
                        error_message=str(e)
                    )
            
            # Update batch progress
            self.db_utils.update_processing_batch(
                batch_id, 
                "patient_embedding", 
                processed_items=processed,
                failed_items=failed
            )
        
        # Mark batch as completed
        self.db_utils.update_processing_batch(
            batch_id, 
            "patient_embedding", 
            status="completed"
        )
        
        logger.info(f"Patient embedding processing completed: {processed} processed, {failed} failed")
        return {
            "status": "completed",
            "processed": processed,
            "failed": failed,
            "total": len(patients)
        }
    
    async def process_all_trial_embeddings(self, batch_id: str) -> Dict[str, Any]:
        """Process embeddings for all trials that need them"""
        logger.info("Processing trial embeddings...")
        
        # Get trials needing embeddings
        trials = self.db_utils.get_trials_needing_embeddings()
        
        if not trials:
            logger.info("No trials need embedding generation")
            return {"status": "completed", "message": "No trials need embeddings", "processed": 0}
        
        # Create batch log
        self.db_utils.create_processing_batch(
            batch_id, 
            "trial_embedding", 
            len(trials),
            {"batch_size": AUTOMATION_TRIAL_BATCH_SIZE}
        )
        
        processed = 0
        failed = 0
        
        # Process in batches
        for i in range(0, len(trials), AUTOMATION_TRIAL_BATCH_SIZE):
            batch = trials[i:i + AUTOMATION_TRIAL_BATCH_SIZE]
            logger.info(f"Processing trial embedding batch {i//AUTOMATION_TRIAL_BATCH_SIZE + 1}/{(len(trials)-1)//AUTOMATION_TRIAL_BATCH_SIZE + 1}")
            
            for trial in batch:
                try:
                    # Generate embedding
                    embedding_result = self.trial_embedding_generator.generate_trial_embedding(
                        trial["trial_id"], 
                        trial["combined_trial_text"]
                    )
                    
                    if embedding_result:
                        # Update status
                        self.db_utils.update_trial_processing_status(
                            trial["trial_id"], 
                            embedding_generated=True
                        )
                        processed += 1
                    else:
                        failed += 1
                        self.db_utils.update_trial_processing_status(
                            trial["trial_id"], 
                            error_message="Failed to generate embedding"
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing trial {trial['trial_id']}: {e}")
                    failed += 1
                    self.db_utils.update_trial_processing_status(
                        trial["trial_id"], 
                        error_message=str(e)
                    )
            
            # Update batch progress
            self.db_utils.update_processing_batch(
                batch_id, 
                "trial_embedding", 
                processed_items=processed,
                failed_items=failed
            )
        
        # Mark batch as completed
        self.db_utils.update_processing_batch(
            batch_id, 
            "trial_embedding", 
            status="completed"
        )
        
        logger.info(f"Trial embedding processing completed: {processed} processed, {failed} failed")
        return {
            "status": "completed",
            "processed": processed,
            "failed": failed,
            "total": len(trials)
        }
    
    async def process_all_patient_keywords(self, batch_id: str) -> Dict[str, Any]:
        """Generate keywords for all patients"""
        logger.info("Processing patient keywords...")
        
        # Get all patients
        patients = self.db_utils.get_all_patients_for_automation()
        
        if not patients:
            logger.info("No patients found for keyword generation")
            return {"status": "completed", "message": "No patients found", "processed": 0}
        
        # Create batch log
        self.db_utils.create_processing_batch(
            batch_id, 
            "patient_keywords", 
            len(patients)
        )
        
        processed = 0
        failed = 0
        
        # Process in batches
        for i in range(0, len(patients), AUTOMATION_PATIENT_BATCH_SIZE):
            batch = patients[i:i + AUTOMATION_PATIENT_BATCH_SIZE]
            logger.info(f"Processing patient keyword batch {i//AUTOMATION_PATIENT_BATCH_SIZE + 1}/{(len(patients)-1)//AUTOMATION_PATIENT_BATCH_SIZE + 1}")
            
            for patient in batch:
                try:
                    # Generate keywords
                    keyword_result = self.patient_keyword_generator.generate_keywords_for_patient(
                        patient["patient_id"], 
                        patient["combined_text"]
                    )
                    
                    if keyword_result:
                        # Update status
                        self.db_utils.update_patient_processing_status(
                            patient["patient_id"], 
                            keywords_generated=True
                        )
                        processed += 1
                    else:
                        failed += 1
                        self.db_utils.update_patient_processing_status(
                            patient["patient_id"], 
                            error_message="Failed to generate keywords"
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing patient keywords {patient['patient_id']}: {e}")
                    failed += 1
                    self.db_utils.update_patient_processing_status(
                        patient["patient_id"], 
                        error_message=str(e)
                    )
            
            # Update batch progress
            self.db_utils.update_processing_batch(
                batch_id, 
                "patient_keywords", 
                processed_items=processed,
                failed_items=failed
            )
        
        # Mark batch as completed
        self.db_utils.update_processing_batch(
            batch_id, 
            "patient_keywords", 
            status="completed"
        )
        
        logger.info(f"Patient keyword processing completed: {processed} processed, {failed} failed")
        return {
            "status": "completed",
            "processed": processed,
            "failed": failed,
            "total": len(patients)
        }
    
    async def process_all_patient_trial_matches(self, batch_id: str) -> Dict[str, Any]:
        """Process patient-to-trial matching for all patients"""
        logger.info("Processing patient-to-trial matches...")
        
        # Get all patients
        patients = self.db_utils.get_all_patients_for_automation()
        
        if not patients:
            logger.info("No patients found for matching")
            return {"status": "completed", "message": "No patients found", "processed": 0}
        
        # Create batch log
        self.db_utils.create_processing_batch(
            batch_id, 
            "patient_trial_matching", 
            len(patients)
        )
        
        processed = 0
        failed = 0
        total_matches = 0
        
        # Process each patient
        for i, patient in enumerate(patients):
            try:
                logger.info(f"Processing patient {i+1}/{len(patients)}: {patient['patient_id']}")
                
                # Find matches for this patient
                matches = self.patient_matcher.find_trial_matches_for_patient(
                    patient["patient_id"], 
                    patient["combined_text"],
                    top_k=50  # Get top 50 matches
                )
                
                # Store matches in database
                for rank, match in enumerate(matches, 1):
                    self.db_utils.store_patient_trial_match(
                        patient_id=patient["patient_id"],
                        patient_mrn=patient["mrn"],
                        trial_id=match["trial_id"],
                        hybrid_score=match["hybrid_score"],
                        embedding_score=match["embedding_score"],
                        bm25_score=match["bm25_score"],
                        match_rank=rank,
                        batch_id=batch_id
                    )
                    total_matches += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing patient {patient['patient_id']}: {e}")
                failed += 1
            
            # Update batch progress every 10 patients
            if (i + 1) % 10 == 0:
                self.db_utils.update_processing_batch(
                    batch_id, 
                    "patient_trial_matching", 
                    processed_items=processed,
                    failed_items=failed
                )
        
        # Mark batch as completed
        self.db_utils.update_processing_batch(
            batch_id, 
            "patient_trial_matching", 
            status="completed"
        )
        
        logger.info(f"Patient-to-trial matching completed: {processed} processed, {failed} failed, {total_matches} total matches")
        return {
            "status": "completed",
            "processed": processed,
            "failed": failed,
            "total_matches": total_matches,
            "total": len(patients)
        }
    
    async def process_all_trial_patient_matches(self, batch_id: str) -> Dict[str, Any]:
        """Process trial-to-patient matching for all trials"""
        logger.info("Processing trial-to-patient matches...")
        
        # Get all trials
        trials = self.db_utils.get_all_trials_for_automation()
        
        if not trials:
            logger.info("No trials found for matching")
            return {"status": "completed", "message": "No trials found", "processed": 0}
        
        # Create batch log
        self.db_utils.create_processing_batch(
            batch_id, 
            "trial_patient_matching", 
            len(trials)
        )
        
        processed = 0
        failed = 0
        total_matches = 0
        
        # Process each trial
        for i, trial in enumerate(trials):
            try:
                logger.info(f"Processing trial {i+1}/{len(trials)}: {trial['trial_id']}")
                
                # Find matches for this trial
                matches = self.trial_matcher.find_patient_matches_for_trial(
                    trial["trial_id"], 
                    trial["combined_trial_text"],
                    top_k=50  # Get top 50 matches
                )
                
                # Store matches in database
                for rank, match in enumerate(matches, 1):
                    self.db_utils.store_trial_patient_match(
                        trial_id=trial["trial_id"],
                        patient_id=match["patient_id"],
                        patient_mrn=match["mrn"],
                        hybrid_score=match["hybrid_score"],
                        embedding_score=match["embedding_score"],
                        bm25_score=match["bm25_score"],
                        match_rank=rank,
                        batch_id=batch_id
                    )
                    total_matches += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing trial {trial['trial_id']}: {e}")
                failed += 1
            
            # Update batch progress every 10 trials
            if (i + 1) % 10 == 0:
                self.db_utils.update_processing_batch(
                    batch_id, 
                    "trial_patient_matching", 
                    processed_items=processed,
                    failed_items=failed
                )
        
        # Mark batch as completed
        self.db_utils.update_processing_batch(
            batch_id, 
            "trial_patient_matching", 
            status="completed"
        )
        
        logger.info(f"Trial-to-patient matching completed: {processed} processed, {failed} failed, {total_matches} total matches")
        return {
            "status": "completed",
            "processed": processed,
            "failed": failed,
            "total_matches": total_matches,
            "total": len(trials)
        }
    
    def save_automation_results(self, results: Dict[str, Any]):
        """Save automation results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"automation_results_{timestamp}.json"
            filepath = self.results_dir / filename
            
            from services.shared.database_utils import safe_json_dump
            safe_json_dump(results, filepath, indent=2)
            logger.info(f"Automation results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving automation results: {e}")
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        try:
            # Get recent processing batches
            with self.db_utils.get_connection() as connection:
                query = text("""
                    SELECT batch_id, processing_type, status, total_items, processed_items, failed_items, started_at, completed_at
                    FROM insightsedge.automation_processing_log
                    ORDER BY started_at DESC
                    LIMIT 10
                """)
                result = connection.execute(query)
                
                batches = []
                for row in result:
                    batches.append({
                        "batch_id": row[0],
                        "processing_type": row[1],
                        "status": row[2],
                        "total_items": row[3],
                        "processed_items": row[4],
                        "failed_items": row[5],
                        "started_at": row[6].isoformat() if row[6] else None,
                        "completed_at": row[7].isoformat() if row[7] else None
                    })
            
            return {
                "automation_enabled": AUTOMATION_ENABLED,
                "recent_batches": batches,
                "status": "active" if AUTOMATION_ENABLED else "disabled"
            }
            
        except Exception as e:
            logger.error(f"Error getting automation status: {e}")
            return {
                "automation_enabled": AUTOMATION_ENABLED,
                "error": str(e),
                "status": "error"
            }
