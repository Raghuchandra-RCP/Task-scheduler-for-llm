"""
Unified Bidirectional Pipeline Orchestrator

This module provides the main pipeline for unified bidirectional clinical trial matching.
It orchestrates the complete workflow from data retrieval to result processing.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from loguru import logger

from services.unified_matching.bidirectional_evaluator import UnifiedBidirectionalEvaluator
from services.shared.database_utils import DatabaseUtils, safe_json_dump


class UnifiedBidirectionalPipeline:
    """
    Main pipeline orchestrator for unified bidirectional clinical trial matching.
    
    This class provides high-level methods to run complete evaluation workflows
    for both patient-to-trial and trial-to-patient matching using a single LLM call.
    """
    
    def __init__(self):
        """Initialize the unified bidirectional pipeline."""
        self.evaluator = UnifiedBidirectionalEvaluator()
        self.db_utils = DatabaseUtils()
        
        # Results directory for JSON persistence
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        self.pipeline_results_dir = self.results_dir / "unified_pipelines"
        self.pipeline_results_dir.mkdir(exist_ok=True)
        
        logger.info("UnifiedBidirectionalPipeline initialized successfully")
    
    def run_patient_evaluation(self, patient_id: int, trial_ids: List[str] = None,
                             max_trials: int = 20, save_results: bool = True) -> Dict[str, Any]:
        """
        Run complete bidirectional evaluation for a patient against multiple trials.
        
        Args:
            patient_id: ID of the patient to evaluate
            trial_ids: List of specific trial IDs to evaluate (optional)
            max_trials: Maximum number of trials to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing complete evaluation results
        """
        logger.info(f"Starting unified patient evaluation for patient {patient_id}")
        
        try:
            # Step 1: Perform unified bidirectional evaluation
            evaluation_results = self.evaluator.evaluate_patient_trials(
                patient_id=patient_id,
                trial_ids=trial_ids,
                max_trials=max_trials
            )
            
            if "error" in evaluation_results:
                logger.error(f"Evaluation failed: {evaluation_results['error']}")
                return evaluation_results
            
            # Step 2: Add pipeline metadata
            pipeline_metadata = {
                "pipeline_type": "unified_patient_evaluation",
                "patient_id": patient_id,
                "trial_ids": trial_ids,
                "max_trials": max_trials,
                "total_trials_evaluated": len(evaluation_results.get("bidirectional_results", [])),
                "pipeline_start_time": datetime.now().isoformat(),
                "pipeline_end_time": datetime.now().isoformat(),
                "pipeline_duration_seconds": 0  # Will be calculated if needed
            }
            
            evaluation_results["pipeline_metadata"] = pipeline_metadata
            
            # Step 3: Save results if requested
            if save_results:
                self._save_pipeline_results(evaluation_results, "patient_evaluation")
            
            # Step 4: Generate summary report
            summary_report = self._generate_patient_summary_report(evaluation_results)
            evaluation_results["summary_report"] = summary_report
            
            logger.info(f"Unified patient evaluation completed for patient {patient_id}")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error in unified patient evaluation: {e}")
            return self._create_error_result(f"Pipeline failed: {str(e)}")
    
    def run_trial_evaluation(self, trial_id: str, patient_ids: List[int] = None,
                           max_patients: int = 20, save_results: bool = True) -> Dict[str, Any]:
        """
        Run complete bidirectional evaluation for a trial against multiple patients.
        
        Args:
            trial_id: ID of the trial to evaluate
            patient_ids: List of specific patient IDs to evaluate (optional)
            max_patients: Maximum number of patients to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing complete evaluation results
        """
        logger.info(f"Starting unified trial evaluation for trial {trial_id}")
        
        try:
            # Step 1: Perform unified bidirectional evaluation
            evaluation_results = self.evaluator.evaluate_trial_patients(
                trial_id=trial_id,
                patient_ids=patient_ids,
                max_patients=max_patients
            )
            
            if "error" in evaluation_results:
                logger.error(f"Evaluation failed: {evaluation_results['error']}")
                return evaluation_results
            
            # Step 2: Add pipeline metadata
            pipeline_metadata = {
                "pipeline_type": "unified_trial_evaluation",
                "trial_id": trial_id,
                "patient_ids": patient_ids,
                "max_patients": max_patients,
                "total_patients_evaluated": len(evaluation_results.get("bidirectional_results", [])),
                "pipeline_start_time": datetime.now().isoformat(),
                "pipeline_end_time": datetime.now().isoformat(),
                "pipeline_duration_seconds": 0
            }
            
            evaluation_results["pipeline_metadata"] = pipeline_metadata
            
            # Step 3: Save results if requested
            if save_results:
                self._save_pipeline_results(evaluation_results, "trial_evaluation")
            
            # Step 4: Generate summary report
            summary_report = self._generate_trial_summary_report(evaluation_results)
            evaluation_results["summary_report"] = summary_report
            
            logger.info(f"Unified trial evaluation completed for trial {trial_id}")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error in unified trial evaluation: {e}")
            return self._create_error_result(f"Pipeline failed: {str(e)}")
    
    def run_batch_evaluation(self, patient_ids: List[int], trial_ids: List[str],
                           save_results: bool = True) -> Dict[str, Any]:
        """
        Run batch bidirectional evaluation for multiple patients and trials.
        
        Args:
            patient_ids: List of patient IDs to evaluate
            trial_ids: List of trial IDs to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing batch evaluation results
        """
        logger.info(f"Starting batch evaluation for {len(patient_ids)} patients and {len(trial_ids)} trials")
        
        try:
            # Step 1: Perform batch evaluation
            batch_results = self.evaluator.batch_evaluate(patient_ids, trial_ids)
            
            if "error" in batch_results:
                logger.error(f"Batch evaluation failed: {batch_results['error']}")
                return batch_results
            
            # Step 2: Add pipeline metadata
            pipeline_metadata = {
                "pipeline_type": "batch_evaluation",
                "patient_ids": patient_ids,
                "trial_ids": trial_ids,
                "total_patients": len(patient_ids),
                "total_trials": len(trial_ids),
                "total_evaluations": len(batch_results.get("evaluations", [])),
                "pipeline_start_time": datetime.now().isoformat(),
                "pipeline_end_time": datetime.now().isoformat(),
                "pipeline_duration_seconds": 0
            }
            
            batch_results["pipeline_metadata"] = pipeline_metadata
            
            # Step 3: Save results if requested
            if save_results:
                self._save_pipeline_results(batch_results, "batch_evaluation")
            
            # Step 4: Generate batch summary report
            summary_report = self._generate_batch_summary_report(batch_results)
            batch_results["summary_report"] = summary_report
            
            logger.info("Batch evaluation completed successfully")
            return batch_results
            
        except Exception as e:
            logger.error(f"Error in batch evaluation: {e}")
            return self._create_error_result(f"Batch pipeline failed: {str(e)}")
    
    def run_comprehensive_evaluation(self, patient_ids: List[int], trial_ids: List[str],
                                   save_results: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive evaluation combining individual and batch evaluations.
        
        Args:
            patient_ids: List of patient IDs to evaluate
            trial_ids: List of trial IDs to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing comprehensive evaluation results
        """
        logger.info(f"Starting comprehensive evaluation for {len(patient_ids)} patients and {len(trial_ids)} trials")
        
        try:
            comprehensive_results = {
                "evaluation_id": f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "patient_evaluations": [],
                "trial_evaluations": [],
                "batch_evaluation": {},
                "comprehensive_summary": {},
                "generated_at": datetime.now().isoformat()
            }
            
            # Step 1: Individual patient evaluations
            logger.info("Running individual patient evaluations...")
            for patient_id in patient_ids:
                patient_result = self.run_patient_evaluation(
                    patient_id=patient_id,
                    trial_ids=trial_ids,
                    save_results=False
                )
                comprehensive_results["patient_evaluations"].append(patient_result)
            
            # Step 2: Individual trial evaluations
            logger.info("Running individual trial evaluations...")
            for trial_id in trial_ids:
                trial_result = self.run_trial_evaluation(
                    trial_id=trial_id,
                    patient_ids=patient_ids,
                    save_results=False
                )
                comprehensive_results["trial_evaluations"].append(trial_result)
            
            # Step 3: Batch evaluation
            logger.info("Running batch evaluation...")
            batch_result = self.run_batch_evaluation(
                patient_ids=patient_ids,
                trial_ids=trial_ids,
                save_results=False
            )
            comprehensive_results["batch_evaluation"] = batch_result
            
            # Step 4: Generate comprehensive summary
            comprehensive_summary = self._generate_comprehensive_summary(comprehensive_results)
            comprehensive_results["comprehensive_summary"] = comprehensive_summary
            
            # Step 5: Save results if requested
            if save_results:
                self._save_pipeline_results(comprehensive_results, "comprehensive_evaluation")
            
            logger.info("Comprehensive evaluation completed successfully")
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            return self._create_error_result(f"Comprehensive pipeline failed: {str(e)}")
    
    def _save_pipeline_results(self, results: Dict[str, Any], evaluation_type: str) -> str:
        """Save pipeline results to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unified_{evaluation_type}_{timestamp}.json"
            filepath = self.pipeline_results_dir / filename
            
            safe_json_dump(results, filepath, indent=2, ensure_ascii=False)
            
            logger.info(f"Pipeline results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving pipeline results: {e}")
            return ""
    
    def _generate_patient_summary_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report for patient evaluation."""
        try:
            bidirectional_results = evaluation_results.get("bidirectional_results", [])
            summary = evaluation_results.get("summary", {})
            
            # Extract top recommendations
            top_recommendations = []
            for result in bidirectional_results:
                compatibility = result.get("overall_compatibility", {})
                trial_info = result.get("trial_info", {})
                
                if compatibility.get("match_quality") in ["EXCELLENT", "GOOD"]:
                    top_recommendations.append({
                        "trial_id": trial_info.get("trial_id"),
                        "title": trial_info.get("title"),
                        "match_quality": compatibility.get("match_quality"),
                        "combined_score": compatibility.get("combined_score"),
                        "recommendation": compatibility.get("final_recommendation")
                    })
            
            # Sort by combined score
            top_recommendations.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
            
            return {
                "patient_id": evaluation_results.get("patient_info", {}).get("patient_id"),
                "total_trials_evaluated": len(bidirectional_results),
                "top_recommendations": top_recommendations[:5],  # Top 5
                "summary_statistics": summary,
                "action_items": self._generate_patient_action_items(bidirectional_results),
                "next_steps": self._generate_patient_next_steps(bidirectional_results)
            }
            
        except Exception as e:
            logger.error(f"Error generating patient summary report: {e}")
            return {"error": str(e)}
    
    def _generate_trial_summary_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report for trial evaluation."""
        try:
            bidirectional_results = evaluation_results.get("bidirectional_results", [])
            summary = evaluation_results.get("summary", {})
            
            # Extract top candidates
            top_candidates = []
            for result in bidirectional_results:
                compatibility = result.get("overall_compatibility", {})
                patient_info = result.get("patient_info", {})
                
                if compatibility.get("match_quality") in ["EXCELLENT", "GOOD"]:
                    top_candidates.append({
                        "patient_id": patient_info.get("patient_id"),
                        "mrn": patient_info.get("mrn"),
                        "age": patient_info.get("age"),
                        "gender": patient_info.get("gender"),
                        "match_quality": compatibility.get("match_quality"),
                        "combined_score": compatibility.get("combined_score"),
                        "recommendation": compatibility.get("final_recommendation")
                    })
            
            # Sort by combined score
            top_candidates.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
            
            return {
                "trial_id": evaluation_results.get("trial_info", {}).get("trial_id"),
                "total_patients_evaluated": len(bidirectional_results),
                "top_candidates": top_candidates[:5],  # Top 5
                "summary_statistics": summary,
                "action_items": self._generate_trial_action_items(bidirectional_results),
                "next_steps": self._generate_trial_next_steps(bidirectional_results)
            }
            
        except Exception as e:
            logger.error(f"Error generating trial summary report: {e}")
            return {"error": str(e)}
    
    def _generate_batch_summary_report(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report for batch evaluation."""
        try:
            evaluations = batch_results.get("evaluations", [])
            batch_summary = batch_results.get("summary", {})
            
            # Extract top matches
            top_matches = []
            for evaluation in evaluations:
                compatibility = evaluation.get("overall_compatibility", {})
                
                if compatibility.get("match_quality") in ["EXCELLENT", "GOOD"]:
                    top_matches.append({
                        "patient_id": evaluation.get("patient_id"),
                        "trial_id": evaluation.get("trial_id"),
                        "match_quality": compatibility.get("match_quality"),
                        "combined_score": compatibility.get("combined_score"),
                        "recommendation": compatibility.get("final_recommendation")
                    })
            
            # Sort by combined score
            top_matches.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
            
            return {
                "batch_id": batch_results.get("batch_id"),
                "total_evaluations": len(evaluations),
                "top_matches": top_matches[:10],  # Top 10
                "batch_statistics": batch_summary,
                "action_items": self._generate_batch_action_items(evaluations),
                "next_steps": self._generate_batch_next_steps(evaluations)
            }
            
        except Exception as e:
            logger.error(f"Error generating batch summary report: {e}")
            return {"error": str(e)}
    
    def _generate_comprehensive_summary(self, comprehensive_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary for all evaluations."""
        try:
            patient_evaluations = comprehensive_results.get("patient_evaluations", [])
            trial_evaluations = comprehensive_results.get("trial_evaluations", [])
            batch_evaluation = comprehensive_results.get("batch_evaluation", {})
            
            # Calculate overall statistics
            total_patient_evaluations = sum(len(eval_result.get("bidirectional_results", [])) 
                                          for eval_result in patient_evaluations)
            total_trial_evaluations = sum(len(eval_result.get("bidirectional_results", [])) 
                                         for eval_result in trial_evaluations)
            total_batch_evaluations = len(batch_evaluation.get("evaluations", []))
            
            # Extract all top matches
            all_top_matches = []
            
            # From patient evaluations
            for patient_eval in patient_evaluations:
                for result in patient_eval.get("bidirectional_results", []):
                    compatibility = result.get("overall_compatibility", {})
                    if compatibility.get("match_quality") in ["EXCELLENT", "GOOD"]:
                        all_top_matches.append({
                            "patient_id": patient_eval.get("patient_info", {}).get("patient_id"),
                            "trial_id": result.get("trial_info", {}).get("trial_id"),
                            "match_quality": compatibility.get("match_quality"),
                            "combined_score": compatibility.get("combined_score"),
                            "source": "patient_evaluation"
                        })
            
            # From trial evaluations
            for trial_eval in trial_evaluations:
                for result in trial_eval.get("bidirectional_results", []):
                    compatibility = result.get("overall_compatibility", {})
                    if compatibility.get("match_quality") in ["EXCELLENT", "GOOD"]:
                        all_top_matches.append({
                            "patient_id": result.get("patient_info", {}).get("patient_id"),
                            "trial_id": trial_eval.get("trial_info", {}).get("trial_id"),
                            "match_quality": compatibility.get("match_quality"),
                            "combined_score": compatibility.get("combined_score"),
                            "source": "trial_evaluation"
                        })
            
            # Sort by combined score
            all_top_matches.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
            
            return {
                "total_patient_evaluations": total_patient_evaluations,
                "total_trial_evaluations": total_trial_evaluations,
                "total_batch_evaluations": total_batch_evaluations,
                "total_evaluations": total_patient_evaluations + total_trial_evaluations + total_batch_evaluations,
                "top_matches_overall": all_top_matches[:20],  # Top 20 overall
                "evaluation_summary": {
                    "patient_evaluations_count": len(patient_evaluations),
                    "trial_evaluations_count": len(trial_evaluations),
                    "batch_evaluation_completed": bool(batch_evaluation),
                    "comprehensive_evaluation_successful": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive summary: {e}")
            return {"error": str(e)}
    
    def _generate_patient_action_items(self, bidirectional_results: List[Dict[str, Any]]) -> List[str]:
        """Generate action items for patient evaluation."""
        action_items = []
        
        for result in bidirectional_results:
            compatibility = result.get("overall_compatibility", {})
            trial_info = result.get("trial_info", {})
            
            if compatibility.get("final_recommendation") == "PROCEED_WITH_ENROLLMENT":
                action_items.append(f"Schedule screening for {trial_info.get('trial_id')}")
            elif compatibility.get("final_recommendation") == "AWAIT_MOLECULAR_TESTING":
                action_items.append(f"Order molecular testing for {trial_info.get('trial_id')}")
        
        return list(set(action_items))  # Remove duplicates
    
    def _generate_trial_action_items(self, bidirectional_results: List[Dict[str, Any]]) -> List[str]:
        """Generate action items for trial evaluation."""
        action_items = []
        
        for result in bidirectional_results:
            compatibility = result.get("overall_compatibility", {})
            patient_info = result.get("patient_info", {})
            
            if compatibility.get("final_recommendation") == "PROCEED_WITH_ENROLLMENT":
                action_items.append(f"Contact patient {patient_info.get('mrn')} for enrollment")
            elif compatibility.get("final_recommendation") == "AWAIT_MOLECULAR_TESTING":
                action_items.append(f"Request additional testing for patient {patient_info.get('mrn')}")
        
        return list(set(action_items))  # Remove duplicates
    
    def _generate_batch_action_items(self, evaluations: List[Dict[str, Any]]) -> List[str]:
        """Generate action items for batch evaluation."""
        action_items = []
        
        for evaluation in evaluations:
            compatibility = evaluation.get("overall_compatibility", {})
            
            if compatibility.get("final_recommendation") == "PROCEED_WITH_ENROLLMENT":
                action_items.append(f"Schedule screening for patient {evaluation.get('patient_id')} - trial {evaluation.get('trial_id')}")
        
        return list(set(action_items))  # Remove duplicates
    
    def _generate_patient_next_steps(self, bidirectional_results: List[Dict[str, Any]]) -> List[str]:
        """Generate next steps for patient evaluation."""
        next_steps = [
            "Review all trial recommendations with the patient",
            "Discuss enrollment options and preferences",
            "Schedule necessary screenings and tests",
            "Coordinate with trial sites for enrollment"
        ]
        return next_steps
    
    def _generate_trial_next_steps(self, bidirectional_results: List[Dict[str, Any]]) -> List[str]:
        """Generate next steps for trial evaluation."""
        next_steps = [
            "Contact top candidate patients",
            "Schedule screening appointments",
            "Coordinate with patient oncologists",
            "Prepare enrollment documentation"
        ]
        return next_steps
    
    def _generate_batch_next_steps(self, evaluations: List[Dict[str, Any]]) -> List[str]:
        """Generate next steps for batch evaluation."""
        next_steps = [
            "Review all patient-trial matches",
            "Prioritize matches by compatibility score",
            "Contact patients and trial coordinators",
            "Schedule screening appointments"
        ]
        return next_steps
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "error": error_message,
            "success": False,
            "generated_at": datetime.now().isoformat(),
            "pipeline_type": "unified_bidirectional"
        }
