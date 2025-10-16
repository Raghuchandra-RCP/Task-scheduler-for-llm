"""
JSON-based Data Persistence for Unified Bidirectional Clinical Trial Matching

This module provides JSON-based data persistence without database operations.
All data is stored and retrieved from JSON files for testing and development.
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from loguru import logger

from services.shared.database_utils import safe_json_dump


class JSONDataPersistence:
    """
    JSON-based data persistence system for unified bidirectional matching.
    
    This class provides methods to store and retrieve evaluation results,
    patient data, trial data, and other information using JSON files
    instead of database operations.
    """
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize JSON data persistence.
        
        Args:
            base_dir: Base directory for storing JSON files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.patients_dir = self.base_dir / "patients"
        self.trials_dir = self.base_dir / "trials"
        self.evaluations_dir = self.base_dir / "evaluations"
        self.results_dir = self.base_dir / "results"
        
        for directory in [self.patients_dir, self.trials_dir, self.evaluations_dir, self.results_dir]:
            directory.mkdir(exist_ok=True)
        
        logger.info(f"JSONDataPersistence initialized with base directory: {self.base_dir}")
    
    def save_patient_data(self, patient_data: Dict[str, Any]) -> str:
        """
        Save patient data to JSON file.
        
        Args:
            patient_data: Patient information dictionary
            
        Returns:
            Path to saved file
        """
        try:
            patient_id = patient_data.get('patient_id', 'unknown')
            filename = f"patient_{patient_id}.json"
            filepath = self.patients_dir / filename
            
            # Add metadata
            patient_data_with_meta = {
                **patient_data,
                "saved_at": datetime.now().isoformat(),
                "data_type": "patient"
            }
            
            safe_json_dump(patient_data_with_meta, filepath, indent=2, ensure_ascii=False)
            
            logger.info(f"Patient data saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving patient data: {e}")
            return ""
    
    def load_patient_data(self, patient_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        Load patient data from JSON file.
        
        Args:
            patient_id: Patient ID to load
            
        Returns:
            Patient data dictionary or None if not found
        """
        try:
            filename = f"patient_{patient_id}.json"
            filepath = self.patients_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Patient data file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                patient_data = json.load(f)
            
            logger.info(f"Patient data loaded from: {filepath}")
            return patient_data
            
        except Exception as e:
            logger.error(f"Error loading patient data: {e}")
            return None
    
    def save_trial_data(self, trial_data: Dict[str, Any]) -> str:
        """
        Save trial data to JSON file.
        
        Args:
            trial_data: Trial information dictionary
            
        Returns:
            Path to saved file
        """
        try:
            trial_id = trial_data.get('trial_id', 'unknown')
            filename = f"trial_{trial_id}.json"
            filepath = self.trials_dir / filename
            
            # Add metadata
            trial_data_with_meta = {
                **trial_data,
                "saved_at": datetime.now().isoformat(),
                "data_type": "trial"
            }
            
            safe_json_dump(trial_data_with_meta, filepath, indent=2, ensure_ascii=False)
            
            logger.info(f"Trial data saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving trial data: {e}")
            return ""
    
    def load_trial_data(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """
        Load trial data from JSON file.
        
        Args:
            trial_id: Trial ID to load
            
        Returns:
            Trial data dictionary or None if not found
        """
        try:
            filename = f"trial_{trial_id}.json"
            filepath = self.trials_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Trial data file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                trial_data = json.load(f)
            
            logger.info(f"Trial data loaded from: {filepath}")
            return trial_data
            
        except Exception as e:
            logger.error(f"Error loading trial data: {e}")
            return None
    
    def save_evaluation_result(self, evaluation_result: Dict[str, Any], 
                             evaluation_type: str = "unified") -> str:
        """
        Save evaluation result to JSON file.
        
        Args:
            evaluation_result: Evaluation result dictionary
            evaluation_type: Type of evaluation (unified, patient, trial, batch)
            
        Returns:
            Path to saved file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Determine filename based on evaluation type
            if evaluation_type == "patient" and "patient_id" in evaluation_result:
                filename = f"patient_evaluation_{evaluation_result['patient_id']}_{timestamp}.json"
            elif evaluation_type == "trial" and "trial_id" in evaluation_result:
                filename = f"trial_evaluation_{evaluation_result['trial_id']}_{timestamp}.json"
            elif evaluation_type == "batch" and "batch_id" in evaluation_result:
                filename = f"batch_evaluation_{evaluation_result['batch_id']}_{timestamp}.json"
            else:
                filename = f"{evaluation_type}_evaluation_{timestamp}.json"
            
            filepath = self.evaluations_dir / filename
            
            # Add metadata
            evaluation_result_with_meta = {
                **evaluation_result,
                "saved_at": datetime.now().isoformat(),
                "evaluation_type": evaluation_type
            }
            
            safe_json_dump(evaluation_result_with_meta, filepath, indent=2, ensure_ascii=False)
            
            logger.info(f"Evaluation result saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving evaluation result: {e}")
            return ""
    
    def load_evaluation_result(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load evaluation result from JSON file.
        
        Args:
            filename: Name of the evaluation file to load
            
        Returns:
            Evaluation result dictionary or None if not found
        """
        try:
            filepath = self.evaluations_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Evaluation file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                evaluation_result = json.load(f)
            
            logger.info(f"Evaluation result loaded from: {filepath}")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error loading evaluation result: {e}")
            return None
    
    def save_pipeline_result(self, pipeline_result: Dict[str, Any], 
                           pipeline_type: str = "unified") -> str:
        """
        Save pipeline result to JSON file.
        
        Args:
            pipeline_result: Pipeline result dictionary
            pipeline_type: Type of pipeline (unified, patient, trial, batch, comprehensive)
            
        Returns:
            Path to saved file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{pipeline_type}_pipeline_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Add metadata
            pipeline_result_with_meta = {
                **pipeline_result,
                "saved_at": datetime.now().isoformat(),
                "pipeline_type": pipeline_type
            }
            
            safe_json_dump(pipeline_result_with_meta, filepath, indent=2, ensure_ascii=False)
            
            logger.info(f"Pipeline result saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving pipeline result: {e}")
            return ""
    
    def load_pipeline_result(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load pipeline result from JSON file.
        
        Args:
            filename: Name of the pipeline file to load
            
        Returns:
            Pipeline result dictionary or None if not found
        """
        try:
            filepath = self.results_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Pipeline file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                pipeline_result = json.load(f)
            
            logger.info(f"Pipeline result loaded from: {filepath}")
            return pipeline_result
            
        except Exception as e:
            logger.error(f"Error loading pipeline result: {e}")
            return None
    
    def list_patients(self) -> List[str]:
        """
        List all available patient files.
        
        Returns:
            List of patient filenames
        """
        try:
            patient_files = [f.name for f in self.patients_dir.glob("patient_*.json")]
            logger.info(f"Found {len(patient_files)} patient files")
            return patient_files
            
        except Exception as e:
            logger.error(f"Error listing patients: {e}")
            return []
    
    def list_trials(self) -> List[str]:
        """
        List all available trial files.
        
        Returns:
            List of trial filenames
        """
        try:
            trial_files = [f.name for f in self.trials_dir.glob("trial_*.json")]
            logger.info(f"Found {len(trial_files)} trial files")
            return trial_files
            
        except Exception as e:
            logger.error(f"Error listing trials: {e}")
            return []
    
    def list_evaluations(self) -> List[str]:
        """
        List all available evaluation files.
        
        Returns:
            List of evaluation filenames
        """
        try:
            evaluation_files = [f.name for f in self.evaluations_dir.glob("*_evaluation_*.json")]
            logger.info(f"Found {len(evaluation_files)} evaluation files")
            return evaluation_files
            
        except Exception as e:
            logger.error(f"Error listing evaluations: {e}")
            return []
    
    def list_pipeline_results(self) -> List[str]:
        """
        List all available pipeline result files.
        
        Returns:
            List of pipeline result filenames
        """
        try:
            pipeline_files = [f.name for f in self.results_dir.glob("*_pipeline_*.json")]
            logger.info(f"Found {len(pipeline_files)} pipeline result files")
            return pipeline_files
            
        except Exception as e:
            logger.error(f"Error listing pipeline results: {e}")
            return []
    
    def get_patient_ids(self) -> List[int]:
        """
        Get list of all patient IDs from saved files.
        
        Returns:
            List of patient IDs
        """
        try:
            patient_files = self.list_patients()
            patient_ids = []
            
            for filename in patient_files:
                # Extract patient ID from filename
                if filename.startswith("patient_") and filename.endswith(".json"):
                    patient_id_str = filename[8:-5]  # Remove "patient_" and ".json"
                    try:
                        patient_id = int(patient_id_str)
                        patient_ids.append(patient_id)
                    except ValueError:
                        continue
            
            logger.info(f"Found {len(patient_ids)} patient IDs")
            return sorted(patient_ids)
            
        except Exception as e:
            logger.error(f"Error getting patient IDs: {e}")
            return []
    
    def get_trial_ids(self) -> List[str]:
        """
        Get list of all trial IDs from saved files.
        
        Returns:
            List of trial IDs
        """
        try:
            trial_files = self.list_trials()
            trial_ids = []
            
            for filename in trial_files:
                # Extract trial ID from filename
                if filename.startswith("trial_") and filename.endswith(".json"):
                    trial_id = filename[6:-5]  # Remove "trial_" and ".json"
                    trial_ids.append(trial_id)
            
            logger.info(f"Found {len(trial_ids)} trial IDs")
            return sorted(trial_ids)
            
        except Exception as e:
            logger.error(f"Error getting trial IDs: {e}")
            return []
    
    def create_sample_data(self) -> Dict[str, Any]:
        """
        Create sample patient and trial data for testing.
        
        Returns:
            Dictionary containing sample data information
        """
        try:
            # Sample patient data
            sample_patients = [
                {
                    "patient_id": 1,
                    "mrn": "MRN001",
                    "age": 65,
                    "gender": "Male",
                    "oncologist": "Dr. Smith",
                    "date_of_visit": "2025-01-15",
                    "combined_text": "65-year-old male with non-small cell lung cancer, Stage IIIB. ECOG performance status 1. No prior immunotherapy. Adequate organ function. No brain metastases."
                },
                {
                    "patient_id": 2,
                    "mrn": "MRN002", 
                    "age": 58,
                    "gender": "Female",
                    "oncologist": "Dr. Johnson",
                    "date_of_visit": "2025-01-14",
                    "combined_text": "58-year-old female with breast cancer, Stage II. ECOG performance status 0. Prior chemotherapy completed 6 months ago. Good cardiac function."
                },
                {
                    "patient_id": 3,
                    "mrn": "MRN003",
                    "age": 72,
                    "gender": "Male", 
                    "oncologist": "Dr. Brown",
                    "date_of_visit": "2025-01-13",
                    "combined_text": "72-year-old male with prostate cancer, Stage IV. ECOG performance status 2. Multiple comorbidities including diabetes and hypertension."
                }
            ]
            
            # Sample trial data
            sample_trials = [
                {
                    "trial_id": "NCT04929223",
                    "title": "Immunotherapy Study for Advanced NSCLC",
                    "condition": "Non-small cell lung cancer",
                    "phase": "Phase II",
                    "status": "Recruiting",
                    "investigator": "Dr. Wilson",
                    "minimum_age": 18,
                    "maximum_age": 75,
                    "sex": "All",
                    "brief_summary": "Study of immunotherapy in advanced NSCLC patients",
                    "detailed_description": "This study evaluates the efficacy and safety of immunotherapy in patients with advanced non-small cell lung cancer.",
                    "inclusion_criteria": "Age 18-75, confirmed NSCLC, Stage IIIB or IV, ECOG 0-1, no prior immunotherapy",
                    "exclusion_criteria": "Active brain metastases, severe cardiac conditions, inadequate organ function",
                    "eligibility_criteria": "Comprehensive eligibility assessment for immunotherapy study"
                },
                {
                    "trial_id": "NCT05123456",
                    "title": "Targeted Therapy for EGFR Mutations",
                    "condition": "Non-small cell lung cancer",
                    "phase": "Phase III",
                    "status": "Recruiting",
                    "investigator": "Dr. Davis",
                    "minimum_age": 18,
                    "maximum_age": 80,
                    "sex": "All",
                    "brief_summary": "Targeted therapy study for EGFR-positive NSCLC",
                    "detailed_description": "This study evaluates targeted therapy in patients with EGFR-mutated non-small cell lung cancer.",
                    "inclusion_criteria": "Age 18-80, confirmed EGFR mutation, NSCLC diagnosis, adequate performance status",
                    "exclusion_criteria": "Prior targeted therapy, severe comorbidities, inadequate organ function",
                    "eligibility_criteria": "EGFR mutation testing required for eligibility"
                },
                {
                    "trial_id": "NCT05234567",
                    "title": "Chemotherapy Combination Study",
                    "condition": "Breast cancer",
                    "phase": "Phase I",
                    "status": "Recruiting",
                    "investigator": "Dr. Miller",
                    "minimum_age": 18,
                    "maximum_age": 70,
                    "sex": "Female",
                    "brief_summary": "Novel chemotherapy combination for breast cancer",
                    "detailed_description": "This study evaluates a novel chemotherapy combination in patients with breast cancer.",
                    "inclusion_criteria": "Age 18-70, female, breast cancer diagnosis, no prior chemotherapy within 6 months",
                    "exclusion_criteria": "Prior chemotherapy within 6 months, severe renal impairment, pregnancy",
                    "eligibility_criteria": "Comprehensive eligibility assessment for chemotherapy study"
                }
            ]
            
            # Save sample data
            saved_files = {
                "patients": [],
                "trials": []
            }
            
            for patient in sample_patients:
                filepath = self.save_patient_data(patient)
                if filepath:
                    saved_files["patients"].append(filepath)
            
            for trial in sample_trials:
                filepath = self.save_trial_data(trial)
                if filepath:
                    saved_files["trials"].append(filepath)
            
            logger.info(f"Created sample data: {len(saved_files['patients'])} patients, {len(saved_files['trials'])} trials")
            
            return {
                "success": True,
                "sample_patients_created": len(saved_files["patients"]),
                "sample_trials_created": len(saved_files["trials"]),
                "saved_files": saved_files,
                "patient_ids": [p["patient_id"] for p in sample_patients],
                "trial_ids": [t["trial_id"] for t in sample_trials]
            }
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_old_files(self, days_old: int = 30) -> Dict[str, int]:
        """
        Clean up old files older than specified days.
        
        Args:
            days_old: Number of days old files should be to be deleted
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleanup_stats = {
                "patients_deleted": 0,
                "trials_deleted": 0,
                "evaluations_deleted": 0,
                "results_deleted": 0
            }
            
            # Clean up old patient files
            for filepath in self.patients_dir.glob("*.json"):
                if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff_date:
                    filepath.unlink()
                    cleanup_stats["patients_deleted"] += 1
            
            # Clean up old trial files
            for filepath in self.trials_dir.glob("*.json"):
                if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff_date:
                    filepath.unlink()
                    cleanup_stats["trials_deleted"] += 1
            
            # Clean up old evaluation files
            for filepath in self.evaluations_dir.glob("*.json"):
                if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff_date:
                    filepath.unlink()
                    cleanup_stats["evaluations_deleted"] += 1
            
            # Clean up old result files
            for filepath in self.results_dir.glob("*.json"):
                if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff_date:
                    filepath.unlink()
                    cleanup_stats["results_deleted"] += 1
            
            total_deleted = sum(cleanup_stats.values())
            logger.info(f"Cleanup completed: {total_deleted} files deleted")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
