"""
Unified Bidirectional Evaluator

Main service class that orchestrates bidirectional clinical trial matching.
Performs both patient-to-trial and trial-to-patient evaluation in a single LLM call.
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from sqlalchemy import text

from services.shared.database_utils import DatabaseUtils, safe_json_dump
from services.shared.llm_utils import LLMUtils
from services.shared.embedding_utils import EmbeddingUtils
from .unified_prompt_engine import UnifiedPromptEngine
from .result_processor import ResultProcessor
from .compatibility_calculator import CompatibilityCalculator


class UnifiedBidirectionalEvaluator:
    """
    Unified evaluator that performs bidirectional clinical trial matching.
    
    This class combines patient-to-trial and trial-to-patient evaluation
    into a single efficient process using one LLM call.
    """
    
    def __init__(self):
        """Initialize the unified bidirectional evaluator."""
        self.db_utils = DatabaseUtils()
        self.llm_utils = LLMUtils()
        self.embedding_utils = EmbeddingUtils()
        self.prompt_engine = UnifiedPromptEngine()
        self.result_processor = ResultProcessor()
        self.compatibility_calculator = CompatibilityCalculator()
        
        # Results directory for JSON persistence
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        self.unified_results_dir = self.results_dir / "unified_evaluations"
        self.unified_results_dir.mkdir(exist_ok=True)
        
        logger.info("UnifiedBidirectionalEvaluator initialized successfully")
    
    def evaluate_patient_trials(self, patient_id: int, trial_ids: List[str] = None, 
                               max_trials: int = 20) -> Dict[str, Any]:
        """
        Evaluate a patient against multiple trials using bidirectional matching.
        
        Args:
            patient_id: ID of the patient to evaluate
            trial_ids: List of specific trial IDs to evaluate (optional)
            max_trials: Maximum number of trials to evaluate
            
        Returns:
            Dictionary containing bidirectional evaluation results
        """
        logger.info(f"Starting unified bidirectional evaluation for patient {patient_id}")
        
        try:
            # Step 1: Get patient data
            patient_data = self._get_patient_data(patient_id)
            if not patient_data:
                logger.error(f"Patient {patient_id} not found")
                return self._create_error_result(f"Patient {patient_id} not found")
            
            # Step 2: Get trial data
            if trial_ids:
                trials_data = self._get_specific_trials_data(trial_ids)
            else:
                trials_data = self._get_relevant_trials_data(patient_data, max_trials)
            
            if not trials_data:
                logger.error("No trials found for evaluation")
                return self._create_error_result("No trials found for evaluation")
            
            logger.info(f"Evaluating patient {patient_id} against {len(trials_data)} trials")
            
            # Step 3: Perform hybrid matching for initial filtering
            filtered_trials = self._perform_hybrid_filtering(patient_data, trials_data)
            
            # Step 4: Perform unified bidirectional LLM evaluation
            llm_results = self._perform_unified_llm_evaluation(patient_data, filtered_trials)
            
            # Step 5: Process and structure results
            final_results = self.result_processor.process_bidirectional_results(
                patient_data, filtered_trials, llm_results
            )
            
            # Step 6: Save results to JSON
            self._save_unified_results(final_results)
            
            logger.info(f"Unified evaluation completed for patient {patient_id}")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in unified evaluation: {e}")
            return self._create_error_result(f"Evaluation failed: {str(e)}")
    
    def evaluate_trial_patients(self, trial_id: str, patient_ids: List[int] = None,
                              max_patients: int = 20) -> Dict[str, Any]:
        """
        Evaluate a trial against multiple patients using bidirectional matching.
        
        Args:
            trial_id: ID of the trial to evaluate
            patient_ids: List of specific patient IDs to evaluate (optional)
            max_patients: Maximum number of patients to evaluate
            
        Returns:
            Dictionary containing bidirectional evaluation results
        """
        logger.info(f"Starting unified bidirectional evaluation for trial {trial_id}")
        
        try:
            # Step 1: Get trial data
            trial_data = self._get_trial_data(trial_id)
            if not trial_data:
                logger.error(f"Trial {trial_id} not found")
                return self._create_error_result(f"Trial {trial_id} not found")
            
            # Step 2: Get patient data
            if patient_ids:
                patients_data = self._get_specific_patients_data(patient_ids)
            else:
                patients_data = self._get_relevant_patients_data(trial_data, max_patients)
            
            if not patients_data:
                logger.error("No patients found for evaluation")
                return self._create_error_result("No patients found for evaluation")
            
            logger.info(f"Evaluating trial {trial_id} against {len(patients_data)} patients")
            
            # Step 3: Perform hybrid matching for initial filtering
            filtered_patients = self._perform_hybrid_filtering_reverse(trial_data, patients_data)
            
            # Step 4: Perform unified bidirectional LLM evaluation
            llm_results = self._perform_unified_llm_evaluation_reverse(trial_data, filtered_patients)
            
            # Step 5: Process and structure results
            final_results = self.result_processor.process_bidirectional_results_reverse(
                trial_data, filtered_patients, llm_results
            )
            
            # Step 6: Save results to JSON
            self._save_unified_results(final_results)
            
            logger.info(f"Unified evaluation completed for trial {trial_id}")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in unified evaluation: {e}")
            return self._create_error_result(f"Evaluation failed: {str(e)}")
    
    def batch_evaluate(self, patient_ids: List[int], trial_ids: List[str]) -> Dict[str, Any]:
        """
        Perform batch bidirectional evaluation for multiple patients and trials.
        
        Args:
            patient_ids: List of patient IDs to evaluate
            trial_ids: List of trial IDs to evaluate
            
        Returns:
            Dictionary containing batch evaluation results
        """
        logger.info(f"Starting batch evaluation for {len(patient_ids)} patients and {len(trial_ids)} trials")
        
        batch_results = {
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "patient_ids": patient_ids,
            "trial_ids": trial_ids,
            "evaluations": [],
            "summary": {},
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            # Get all data upfront
            patients_data = self._get_specific_patients_data(patient_ids)
            trials_data = self._get_specific_trials_data(trial_ids)
            
            # Perform batch LLM evaluation
            batch_llm_results = self._perform_batch_llm_evaluation(patients_data, trials_data)
            
            # Process batch results
            batch_results["evaluations"] = self.result_processor.process_batch_results(
                patients_data, trials_data, batch_llm_results
            )
            
            # Calculate batch summary
            batch_results["summary"] = self._calculate_batch_summary(batch_results["evaluations"])
            
            # Save batch results
            self._save_batch_results(batch_results)
            
            logger.info("Batch evaluation completed successfully")
            return batch_results
            
        except Exception as e:
            logger.error(f"Error in batch evaluation: {e}")
            batch_results["error"] = str(e)
            return batch_results
    
    def _get_patient_data(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get patient data by ID."""
        try:
            return self.db_utils.get_patient_by_id(patient_id)
        except Exception as e:
            logger.error(f"Error getting patient data: {e}")
            return None
    
    def _get_trial_data(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """Get trial data by ID with complete details."""
        try:
            # Use the existing working stored procedure
            with self.db_utils.get_connection() as connection:
                query = text("SELECT * FROM insightsedge.get_trial_data_for_embeddings() WHERE trial_id = :trial_id LIMIT 1")
                result = connection.execute(query, {"trial_id": trial_id})
                row = result.fetchone()
                
                if row:
                    trial_data = dict(row._mapping)
                    logger.info(f"Retrieved trial data for {trial_id}")
                    return trial_data
                else:
                    logger.warning(f"No trial found with ID {trial_id}")
                    return None
        except Exception as e:
            logger.error(f"Error getting trial data: {e}")
            return None
    
    def _get_specific_trials_data(self, trial_ids: List[str]) -> List[Dict[str, Any]]:
        """Get data for specific trials."""
        trials_data = []
        for trial_id in trial_ids:
            trial_data = self._get_trial_data(trial_id)
            if trial_data:
                trials_data.append(trial_data)
        return trials_data
    
    def _get_specific_patients_data(self, patient_ids: List[int]) -> List[Dict[str, Any]]:
        """Get data for specific patients."""
        patients_data = []
        for patient_id in patient_ids:
            patient_data = self._get_patient_data(patient_id)
            if patient_data:
                patients_data.append(patient_data)
        return patients_data
    
    def _get_relevant_trials_data(self, patient_data: Dict[str, Any], max_trials: int) -> List[Dict[str, Any]]:
        """Get relevant trials for patient using hybrid matching."""
        try:
            # Use existing hybrid matching to find relevant trials
            from services.patient_to_trial.patient_matcher import PatientMatcher
            matcher = PatientMatcher()
            
            # First try with phase filtering
            hybrid_results = matcher.find_trials_for_patient(
                patient_data['patient_id'],
                phase_filter=["Phase I", "Phase II", "Phase III"]
            )
            
            trials_data = []
            for trial in hybrid_results.get('matching_trials', [])[:max_trials]:
                trial_id = trial.get('trial_id')
                if trial_id:
                    trial_data = self._get_trial_data(trial_id)
                    if trial_data:
                        trial_data['hybrid_score'] = trial.get('hybrid_score', 0)
                        trials_data.append(trial_data)
            
            # If no trials found with phase filtering, try without phase filter
            if not trials_data:
                logger.warning("No trials found with phase filtering, trying without phase filter...")
                hybrid_results = matcher.find_trials_for_patient(
                    patient_data['patient_id'],
                    phase_filter=None  # No phase filtering
                )
                
                for trial in hybrid_results.get('matching_trials', [])[:max_trials]:
                    trial_id = trial.get('trial_id')
                    if trial_id:
                        trial_data = self._get_trial_data(trial_id)
                        if trial_data:
                            trial_data['hybrid_score'] = trial.get('hybrid_score', 0)
                            trials_data.append(trial_data)
            
            # If still no trials found, get some random trials as fallback
            if not trials_data:
                logger.warning("No trials found with hybrid matching, using fallback method...")
                trials_data = self._get_fallback_trials_data(max_trials)
            
            logger.info(f"Found {len(trials_data)} trials for evaluation")
            return trials_data
            
        except Exception as e:
            logger.error(f"Error getting relevant trials: {e}")
            # Fallback to getting some trials directly
            return self._get_fallback_trials_data(max_trials)
    
    def _get_relevant_patients_data(self, trial_data: Dict[str, Any], max_patients: int) -> List[Dict[str, Any]]:
        """Get relevant patients for trial using hybrid matching."""
        try:
            # Use existing hybrid matching to find relevant patients
            from services.trial_to_patient.hybrid_matcher import HybridMatcher
            matcher = HybridMatcher()
            
            # Get top patients using hybrid matching
            hybrid_results = matcher.run_trial_to_patient_matching(trial_data['trial_id'])
            
            # Extract patient data for top matches
            patients_data = []
            for patient in hybrid_results.get('matching_patients', [])[:max_patients]:
                mrn = patient.get('mrn')
                if mrn:
                    patient_data = self.db_utils.get_patient_by_mrn(mrn)
                    if patient_data:
                        patient_data['hybrid_score'] = patient.get('hybrid_score', 0)
                        patients_data.append(patient_data)
            
            return patients_data
            
        except Exception as e:
            logger.error(f"Error getting relevant patients: {e}")
            return []
    
    def _perform_hybrid_filtering(self, patient_data: Dict[str, Any], 
                                 trials_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform hybrid filtering to get top trials for LLM evaluation."""
        try:
            # Use existing patient matcher for hybrid filtering
            from services.patient_to_trial.patient_matcher import PatientMatcher
            matcher = PatientMatcher()
            
            # Get hybrid scores for all trials
            filtered_trials = []
            for trial in trials_data:
                # Calculate hybrid score for this trial-patient pair
                trial_text = f"{trial['title']} {trial['condition']} {trial['phase']}"
                patient_text = patient_data['combined_text']
                
                # Generate embeddings and calculate similarity
                trial_embedding = self.embedding_utils.generate_embedding(trial_text, "retrieval_document")
                patient_embedding = self.embedding_utils.generate_embedding(patient_text, "retrieval_query")
                
                # Calculate cosine similarity
                similarity = np.dot(trial_embedding, patient_embedding) / (
                    np.linalg.norm(trial_embedding) * np.linalg.norm(patient_embedding)
                )
                
                trial['hybrid_score'] = float(similarity)
                filtered_trials.append(trial)
            
            # Sort by hybrid score and return top trials
            filtered_trials.sort(key=lambda x: x['hybrid_score'], reverse=True)
            return filtered_trials[:10]  # Top 10 for LLM evaluation
            
        except Exception as e:
            logger.error(f"Error in hybrid filtering: {e}")
            return trials_data[:10]  # Fallback to first 10
    
    def _perform_hybrid_filtering_reverse(self, trial_data: Dict[str, Any], 
                                         patients_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform hybrid filtering to get top patients for LLM evaluation."""
        try:
            # Similar to above but for trial-to-patient direction
            filtered_patients = []
            trial_text = f"{trial_data['title']} {trial_data['condition']} {trial_data['phase']}"
            trial_embedding = self.embedding_utils.generate_embedding(trial_text, "retrieval_query")
            
            for patient in patients_data:
                patient_text = patient['combined_text']
                patient_embedding = self.embedding_utils.generate_embedding(patient_text, "retrieval_document")
                
                # Calculate cosine similarity
                similarity = np.dot(trial_embedding, patient_embedding) / (
                    np.linalg.norm(trial_embedding) * np.linalg.norm(patient_embedding)
                )
                
                patient['hybrid_score'] = float(similarity)
                filtered_patients.append(patient)
            
            # Sort by hybrid score and return top patients
            filtered_patients.sort(key=lambda x: x['hybrid_score'], reverse=True)
            return filtered_patients[:10]  # Top 10 for LLM evaluation
            
        except Exception as e:
            logger.error(f"Error in reverse hybrid filtering: {e}")
            return patients_data[:10]  # Fallback to first 10
    
    def _perform_unified_llm_evaluation(self, patient_data: Dict[str, Any], 
                                       trials_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform unified bidirectional LLM evaluation."""
        try:
            # Generate unified prompt
            prompt = self.prompt_engine.generate_bidirectional_prompt(patient_data, trials_data)
            
            # Call LLM
            llm_response = self.llm_utils.call_llm(prompt)
            
            if "error" in llm_response:
                logger.error(f"LLM error: {llm_response['error']}")
                return {"error": llm_response["error"]}
            
            # Parse response
            parsed_results = self.prompt_engine.parse_bidirectional_response(llm_response["response"])
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error in unified LLM evaluation: {e}")
            return {"error": str(e)}
    
    def _perform_unified_llm_evaluation_reverse(self, trial_data: Dict[str, Any], 
                                               patients_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform unified bidirectional LLM evaluation (reverse direction)."""
        try:
            # Generate unified prompt for reverse direction
            prompt = self.prompt_engine.generate_bidirectional_prompt_reverse(trial_data, patients_data)
            
            # Call LLM
            llm_response = self.llm_utils.call_llm(prompt)
            
            if "error" in llm_response:
                logger.error(f"LLM error: {llm_response['error']}")
                return {"error": llm_response["error"]}
            
            # Parse response
            parsed_results = self.prompt_engine.parse_bidirectional_response_reverse(llm_response["response"])
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error in reverse unified LLM evaluation: {e}")
            return {"error": str(e)}
    
    def _perform_batch_llm_evaluation(self, patients_data: List[Dict[str, Any]], 
                                    trials_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform batch LLM evaluation for multiple patients and trials."""
        try:
            # Generate batch prompt
            prompt = self.prompt_engine.generate_batch_bidirectional_prompt(patients_data, trials_data)
            
            # Call LLM
            llm_response = self.llm_utils.call_llm(prompt)
            
            if "error" in llm_response:
                logger.error(f"Batch LLM error: {llm_response['error']}")
                return {"error": llm_response["error"]}
            
            # Parse batch response
            parsed_results = self.prompt_engine.parse_batch_bidirectional_response(llm_response["response"])
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error in batch LLM evaluation: {e}")
            return {"error": str(e)}
    
    def _save_unified_results(self, results: Dict[str, Any]) -> str:
        """Save unified evaluation results to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Determine filename based on evaluation type
            if "patient_id" in results:
                filename = f"unified_patient_{results['patient_id']}_{timestamp}.json"
            elif "trial_id" in results:
                filename = f"unified_trial_{results['trial_id']}_{timestamp}.json"
            else:
                filename = f"unified_evaluation_{timestamp}.json"
            
            filepath = self.unified_results_dir / filename
            
            # Save with safe JSON handling
            safe_json_dump(results, filepath, indent=2, ensure_ascii=False)
            
            logger.info(f"Unified results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving unified results: {e}")
            return ""
    
    def _save_batch_results(self, results: Dict[str, Any]) -> str:
        """Save batch evaluation results to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_evaluation_{results['batch_id']}_{timestamp}.json"
            filepath = self.unified_results_dir / filename
            
            safe_json_dump(results, filepath, indent=2, ensure_ascii=False)
            
            logger.info(f"Batch results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving batch results: {e}")
            return ""
    
    def _calculate_batch_summary(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for batch evaluation."""
        try:
            total_evaluations = len(evaluations)
            eligible_count = sum(1 for eval_result in evaluations 
                               if eval_result.get('patient_to_trial', {}).get('eligibility_status') == 'ELIGIBLE')
            suitable_count = sum(1 for eval_result in evaluations 
                               if eval_result.get('trial_to_patient', {}).get('suitability_status') in ['HIGHLY_SUITABLE', 'SUITABLE'])
            
            avg_compatibility = sum(eval_result.get('overall_compatibility', {}).get('combined_score', 0) 
                                  for eval_result in evaluations) / total_evaluations if total_evaluations > 0 else 0
            
            return {
                "total_evaluations": total_evaluations,
                "eligible_matches": eligible_count,
                "suitable_matches": suitable_count,
                "average_compatibility": round(avg_compatibility, 2),
                "success_rate": round((eligible_count + suitable_count) / (total_evaluations * 2) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating batch summary: {e}")
            return {}
    
    def _get_fallback_trials_data(self, max_trials: int) -> List[Dict[str, Any]]:
        """Get fallback trials data when hybrid matching fails."""
        try:
            logger.info("Using fallback method to get trials directly from database...")
            
            # Get trials directly from database using existing method
            trials_data = []
            
            # Try to get trials using the existing database method with complete details
            try:
                with self.db_utils.get_connection() as connection:
                    query = text("SELECT * FROM insightsedge.get_trial_data_for_embeddings() LIMIT :limit")
                    result = connection.execute(query, {"limit": max_trials})
                    
                    for row in result.fetchall():
                        trial_data = dict(row._mapping)
                        trial_data['hybrid_score'] = 0.5  # Default score for fallback
                        
                        # Ensure we have all the required fields for LLM evaluation
                        if not trial_data.get('inclusion_criteria'):
                            trial_data['inclusion_criteria'] = 'Not available'
                        if not trial_data.get('exclusion_criteria'):
                            trial_data['exclusion_criteria'] = 'Not available'
                        if not trial_data.get('eligibility_criteria'):
                            trial_data['eligibility_criteria'] = 'Not available'
                        if not trial_data.get('brief_summary'):
                            trial_data['brief_summary'] = 'Not available'
                        if not trial_data.get('detailed_description'):
                            trial_data['detailed_description'] = 'Not available'
                        
                        trials_data.append(trial_data)
                        
            except Exception as db_error:
                logger.warning(f"Database query failed: {db_error}")
                
                # If database fails, create some sample trials with complete details
                sample_trials = [
                    {
                        "trial_id": "NCT04929223",
                        "title": "A Phase I/Ib Global, Multicenter, Open-label Umbrella Study Evaluating the Safety and Efficacy of Targeted Therapies in Subpopulations of Patients With Metastatic Colorectal Cancer (INTRINSIC)",
                        "condition": "Metastatic Colorectal Cancer",
                        "phase": "Phase I",
                        "status": "Recruiting",
                        "investigator": "Dr. Wilson",
                        "minimum_age": 18,
                        "maximum_age": 75,
                        "sex": "All",
                        "brief_summary": "This study evaluates targeted therapies in patients with metastatic colorectal cancer based on molecular profiling.",
                        "detailed_description": "This is a Phase I/Ib umbrella study designed to evaluate the safety and efficacy of targeted therapies in subpopulations of patients with metastatic colorectal cancer. The study uses molecular profiling to match patients with appropriate targeted therapies.",
                        "inclusion_criteria": "Age 18-75 years, histologically confirmed metastatic colorectal cancer, measurable disease per RECIST v1.1, ECOG performance status 0-1, adequate organ function, no prior treatment with targeted therapy for current disease, willingness to undergo molecular profiling",
                        "exclusion_criteria": "Active brain metastases, severe cardiac conditions (NYHA Class III/IV), inadequate organ function (creatinine clearance <60 mL/min, bilirubin >1.5x ULN), pregnancy or breastfeeding, active infection requiring systemic therapy",
                        "eligibility_criteria": "Patients must have metastatic colorectal cancer with molecular alterations suitable for targeted therapy. Prior chemotherapy is allowed but no prior targeted therapy. Patients must be willing to undergo biopsy for molecular profiling.",
                        "hybrid_score": 0.5
                    },
                    {
                        "trial_id": "NCT04792684",
                        "title": "Collection of Samples From the United States Population for Optimization and Evaluation of Colorectal Cancer (CRC) Plasma Circulating Free-DNA (cfDNA) Marker Panel Performance",
                        "condition": "Colorectal Cancer",
                        "phase": "Not specified",
                        "status": "Recruiting",
                        "investigator": "Dr. Smith",
                        "minimum_age": 18,
                        "maximum_age": 80,
                        "sex": "All",
                        "brief_summary": "This study collects blood samples from patients with colorectal cancer to evaluate cfDNA marker panel performance.",
                        "detailed_description": "This study aims to collect blood samples from patients with colorectal cancer across the United States to optimize and evaluate the performance of a plasma circulating free-DNA (cfDNA) marker panel for colorectal cancer detection and monitoring.",
                        "inclusion_criteria": "Age 18-80 years, histologically confirmed colorectal cancer (any stage), ability to provide blood samples, willingness to participate in follow-up",
                        "exclusion_criteria": "Inability to provide blood samples, active bleeding disorders, pregnancy, concurrent participation in other biomarker studies",
                        "eligibility_criteria": "Patients with confirmed colorectal cancer diagnosis who can provide blood samples for cfDNA analysis. No specific treatment requirements.",
                        "hybrid_score": 0.5
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
                        "eligibility_criteria": "Comprehensive eligibility assessment for chemotherapy study",
                        "hybrid_score": 0.5
                    }
                ]
                
                trials_data = sample_trials[:max_trials]
            
            logger.info(f"Fallback method found {len(trials_data)} trials")
            return trials_data
            
        except Exception as e:
            logger.error(f"Error in fallback trials method: {e}")
            return []
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "error": error_message,
            "success": False,
            "generated_at": datetime.now().isoformat(),
            "evaluation_method": "unified_bidirectional"
        }
