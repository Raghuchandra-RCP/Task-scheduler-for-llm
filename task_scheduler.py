"""
Task Scheduler for LLM Processing
Handles scheduled tasks for processing patient-trial matching using LLM
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy import text

from config import (
    SCHEDULER_INTERVAL_MINUTES,
    MAX_CONCURRENT_TASKS,
    TASK_TIMEOUT_SECONDS,
    USE_LLM_PROCESSING,
    USE_DATABASE,
    AUTOMATION_ENABLED
)

# Import our services
from database.patient_db import PatientDB
from database.trial_database_service import TrialDatabaseService
from services.automation_service import AutomationService

class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor(max_workers=MAX_CONCURRENT_TASKS)},
            job_defaults={'coalesce': True, 'max_instances': 1}
        )
        self.running = False
        
        # Initialize services
        self.patient_db = None
        self.trial_db = None
        self.automation_service = None
        
    async def initialize(self):
        """Initialize all services and database connections"""
        logger.info("Initializing Task Scheduler services...")
        
        try:
            # Initialize database services
            if USE_DATABASE:
                self.patient_db = PatientDB()
                self.trial_db = TrialDatabaseService()
                await self.patient_db.initialize()
                await self.trial_db.initialize()
                logger.info("Database services initialized")
            
            # Initialize LLM services
            if USE_LLM_PROCESSING:
                logger.info("LLM processing enabled - using modular pipeline services")
            
            # Initialize automation service
            if AUTOMATION_ENABLED:
                self.automation_service = AutomationService()
                logger.info("Automation service initialized")
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
            
    async def start(self):
        """Start the task scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        logger.info("Starting task scheduler...")
        
        # Add scheduled jobs
        self._add_scheduled_jobs()
        
        # Start the scheduler
        self.scheduler.start()
        self.running = True
        
        logger.info(f"Task scheduler started with {len(self.scheduler.get_jobs())} jobs")
        
        # Keep the scheduler running
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
            
    async def stop(self):
        """Stop the task scheduler"""
        if not self.running:
            return
            
        logger.info("Stopping task scheduler...")
        self.running = False
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            
        logger.info("Task scheduler stopped")
        
    def _add_scheduled_jobs(self):
        """Add all scheduled jobs to the scheduler"""
        
        # Process pending patient-trial matches every 30 minutes
        self.scheduler.add_job(
            self.process_patient_trial_matches,
            trigger=IntervalTrigger(minutes=SCHEDULER_INTERVAL_MINUTES),
            id='process_patient_trial_matches',
            name='Process Patient-Trial Matches',
            replace_existing=True
        )
        
        # Process pending trial-patient matches every 30 minutes
        self.scheduler.add_job(
            self.process_trial_patient_matches,
            trigger=IntervalTrigger(minutes=SCHEDULER_INTERVAL_MINUTES),
            id='process_trial_patient_matches',
            name='Process Trial-Patient Matches',
            replace_existing=True
        )
        
        # Update trial eligibility assessments every hour
        self.scheduler.add_job(
            self.update_trial_eligibility,
            trigger=CronTrigger(minute=0),  # Every hour at minute 0
            id='update_trial_eligibility',
            name='Update Trial Eligibility Assessments',
            replace_existing=True
        )
        
        # Clean up old results every day at 2 AM
        self.scheduler.add_job(
            self.cleanup_old_results,
            trigger=CronTrigger(hour=2, minute=0),  # Daily at 2 AM
            id='cleanup_old_results',
            name='Cleanup Old Results',
            replace_existing=True
        )
        
        logger.info(f"Added {len(self.scheduler.get_jobs())} scheduled jobs")
        
    async def process_patient_trial_matches(self):
        """Process pending patient-to-trial matching tasks"""
        logger.info("Starting patient-trial matching task...")
        
        try:
            if AUTOMATION_ENABLED and self.automation_service:
                # Run full automation if enabled
                logger.info("Running full automation for patient-trial matching...")
                results = await self.automation_service.run_full_automation()
                logger.info(f"Automation completed with status: {results['status']}")
            else:
                # Manual processing mode - process only new patients
                logger.info("Running manual patient-trial matching...")
                await self._process_new_patients_only()
                    
            logger.info("Patient-trial matching task completed")
            
        except Exception as e:
            logger.error(f"Error in patient-trial matching task: {e}")
            
    async def process_trial_patient_matches(self):
        """Process pending trial-to-patient matching tasks"""
        logger.info("Starting trial-patient matching task...")
        
        try:
            if AUTOMATION_ENABLED and self.automation_service:
                # In automation mode, this is handled by the full automation process
                logger.info("Trial-patient matching handled by automation service")
            else:
                # Manual processing mode - process only new trials
                logger.info("Running manual trial-patient matching...")
                await self._process_new_trials_only()
                    
            logger.info("Trial-patient matching task completed")
            
        except Exception as e:
            logger.error(f"Error in trial-patient matching task: {e}")
            
    async def update_trial_eligibility(self):
        """Update trial eligibility assessments"""
        logger.info("Starting trial eligibility update task...")
        
        try:
            if not self.trial_db:
                logger.warning("Required database services not initialized")
                return
                
            # Get trials that need eligibility updates
            trials_to_update = await self._get_trials_needing_eligibility_update()
            
            if not trials_to_update:
                logger.info("No trials need eligibility updates")
                return
                
            logger.info(f"Updating eligibility for {len(trials_to_update)} trials")
            
            # Process each trial
            for trial_id in trials_to_update:
                try:
                    await self._update_single_trial_eligibility(trial_id)
                except Exception as e:
                    logger.error(f"Failed to update trial {trial_id} eligibility: {e}")
                    continue
                    
            logger.info("Trial eligibility update task completed")
            
        except Exception as e:
            logger.error(f"Error in trial eligibility update task: {e}")
            
    async def cleanup_old_results(self):
        """Clean up old results and temporary data"""
        logger.info("Starting cleanup task...")
        
        try:
            # Clean up results older than 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            cleaned_count = await self._cleanup_old_data(cutoff_date)
            
            logger.info(f"Cleanup completed: {cleaned_count} old records removed")
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            
    # Helper methods for manual processing (when automation is disabled)
    async def _process_new_patients_only(self):
        """Process only new patients that haven't been processed yet"""
        try:
            from services.shared.database_utils import DatabaseUtils
            db_utils = DatabaseUtils()
            
            # Get patients that need embeddings
            patients_needing_embeddings = db_utils.get_patients_needing_embeddings()
            
            if patients_needing_embeddings:
                logger.info(f"Found {len(patients_needing_embeddings)} patients needing embeddings")
                
                # Process a small batch for manual mode
                batch_size = min(10, len(patients_needing_embeddings))
                batch = patients_needing_embeddings[:batch_size]
                
                for patient in batch:
                    try:
                        # Generate embedding
                        from services.patient_to_trial.patient_embedding import PatientEmbeddingGenerator
                        embedding_gen = PatientEmbeddingGenerator()
                        result = embedding_gen.generate_patient_embedding(
                            patient["patient_id"], 
                            patient["combined_text"]
                        )
                        
                        if result:
                            db_utils.update_patient_processing_status(
                                patient["patient_id"], 
                                embedding_generated=True
                            )
                            logger.info(f"Generated embedding for patient {patient['patient_id']}")
                        
                    except Exception as e:
                        logger.error(f"Error processing patient {patient['patient_id']}: {e}")
                        db_utils.update_patient_processing_status(
                            patient["patient_id"], 
                            error_message=str(e)
                        )
            else:
                logger.info("No patients need embedding generation")
                
        except Exception as e:
            logger.error(f"Error in manual patient processing: {e}")
    
    async def _process_new_trials_only(self):
        """Process only new trials that haven't been processed yet"""
        try:
            from services.shared.database_utils import DatabaseUtils
            db_utils = DatabaseUtils()
            
            # Get trials that need embeddings
            trials_needing_embeddings = db_utils.get_trials_needing_embeddings()
            
            if trials_needing_embeddings:
                logger.info(f"Found {len(trials_needing_embeddings)} trials needing embeddings")
                
                # Process a small batch for manual mode
                batch_size = min(10, len(trials_needing_embeddings))
                batch = trials_needing_embeddings[:batch_size]
                
                for trial in batch:
                    try:
                        # Generate embedding
                        from services.trial_to_patient.trial_embedding import TrialEmbeddingGenerator
                        embedding_gen = TrialEmbeddingGenerator()
                        result = embedding_gen.generate_trial_embedding(
                            trial["trial_id"], 
                            trial["combined_trial_text"]
                        )
                        
                        if result:
                            db_utils.update_trial_processing_status(
                                trial["trial_id"], 
                                embedding_generated=True
                            )
                            logger.info(f"Generated embedding for trial {trial['trial_id']}")
                        
                    except Exception as e:
                        logger.error(f"Error processing trial {trial['trial_id']}: {e}")
                        db_utils.update_trial_processing_status(
                            trial["trial_id"], 
                            error_message=str(e)
                        )
            else:
                logger.info("No trials need embedding generation")
                
        except Exception as e:
            logger.error(f"Error in manual trial processing: {e}")
    
    async def _get_trials_needing_eligibility_update(self) -> List[str]:
        """Get list of trial IDs that need eligibility updates"""
        try:
            from services.shared.database_utils import DatabaseUtils
            db_utils = DatabaseUtils()
            
            # Get trials that haven't been processed recently
            with db_utils.get_connection() as connection:
                query = text("""
                    SELECT trial_id 
                    FROM insightsedge.trial_processing_status 
                    WHERE embedding_generated = TRUE 
                    AND last_embedding_update < NOW() - INTERVAL '7 days'
                    LIMIT 50
                """)
                result = connection.execute(query)
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting trials needing eligibility update: {e}")
            return []
        
    async def _update_single_trial_eligibility(self, trial_id: str):
        """Update eligibility for a single trial"""
        logger.info(f"Updating eligibility for trial {trial_id}")
        
        try:
            # This would trigger a re-evaluation of the trial's eligibility criteria
            # For now, just update the timestamp
            from services.shared.database_utils import DatabaseUtils
            db_utils = DatabaseUtils()
            db_utils.update_trial_processing_status(trial_id, embedding_generated=True)
            
        except Exception as e:
            logger.error(f"Error updating trial eligibility for {trial_id}: {e}")
        
    async def _cleanup_old_data(self, cutoff_date: datetime) -> int:
        """Clean up old data older than cutoff_date"""
        try:
            from services.shared.database_utils import DatabaseUtils
            db_utils = DatabaseUtils()
            
            cleaned_count = 0
            
            with db_utils.get_connection() as connection:
                # Clean up old processing logs
                query = text("""
                    DELETE FROM insightsedge.automation_processing_log 
                    WHERE started_at < :cutoff_date
                """)
                result = connection.execute(query, {"cutoff_date": cutoff_date})
                cleaned_count += result.rowcount
                
                # Clean up old matching results (keep only recent ones)
                query = text("""
                    DELETE FROM insightsedge.patient_trial_matches 
                    WHERE created_at < :cutoff_date
                """)
                result = connection.execute(query, {"cutoff_date": cutoff_date})
                cleaned_count += result.rowcount
                
                query = text("""
                    DELETE FROM insightsedge.trial_patient_matches 
                    WHERE created_at < :cutoff_date
                """)
                result = connection.execute(query, {"cutoff_date": cutoff_date})
                cleaned_count += result.rowcount
                
                connection.commit()
            
            logger.info(f"Cleaned up {cleaned_count} old records")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
        
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        status = {
            "running": self.running,
            "automation_enabled": AUTOMATION_ENABLED,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                for job in self.scheduler.get_jobs()
            ],
            "services_initialized": {
                "patient_db": self.patient_db is not None,
                "trial_db": self.trial_db is not None,
                "automation_service": self.automation_service is not None
            }
        }
        
        # Add automation status if available
        if self.automation_service:
            try:
                automation_status = self.automation_service.get_automation_status()
                status["automation_status"] = automation_status
            except Exception as e:
                status["automation_status"] = {"error": str(e)}
        
        return status
