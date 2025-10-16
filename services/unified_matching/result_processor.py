"""
Result Processor for Unified Bidirectional Clinical Trial Matching

This module processes and structures the results from bidirectional LLM evaluations,
providing comprehensive analysis and recommendations.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger


class ResultProcessor:
    """
    Processes bidirectional evaluation results from LLM responses.
    
    This class takes raw LLM responses and structures them into
    comprehensive evaluation results with scoring and recommendations.
    """
    
    def __init__(self):
        """Initialize the result processor."""
        logger.info("ResultProcessor initialized successfully")
    
    def process_bidirectional_results(self, patient_data: Dict[str, Any], 
                                    trials_data: List[Dict[str, Any]], 
                                    llm_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bidirectional results for patient-to-trials evaluation.
        
        Args:
            patient_data: Patient information
            trials_data: List of trial information
            llm_results: Raw LLM response data
            
        Returns:
            Structured evaluation results
        """
        try:
            if "error" in llm_results:
                logger.error(f"LLM results contain error: {llm_results['error']}")
                return self._create_error_result(llm_results["error"])
            
            # Extract evaluations from LLM results
            evaluations = llm_results.get("bidirectional_evaluations", [])
            summary = llm_results.get("summary", {})
            metadata = llm_results.get("evaluation_metadata", {})
            
            # Process each evaluation
            processed_evaluations = []
            for i, evaluation in enumerate(evaluations):
                processed_eval = self._process_single_evaluation(evaluation, trials_data[i] if i < len(trials_data) else {})
                processed_evaluations.append(processed_eval)
            
            # Create final result structure
            final_result = {
                "evaluation_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "patient_info": {
                    "patient_id": patient_data.get('patient_id'),
                    "mrn": patient_data.get('mrn'),
                    "age": patient_data.get('age'),
                    "gender": patient_data.get('gender'),
                    "condition": self._extract_condition_from_text(patient_data.get('combined_text', '')),
                    "oncologist": patient_data.get('oncologist')
                },
                "bidirectional_results": processed_evaluations,
                "summary": self._calculate_summary(processed_evaluations),
                "llm_summary": summary,
                "processing_metadata": {
                    "evaluation_method": "unified_bidirectional",
                    "total_trials_evaluated": len(processed_evaluations),
                    "processing_timestamp": datetime.now().isoformat(),
                    "llm_metadata": metadata
                },
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Processed bidirectional results for {len(processed_evaluations)} trials")
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing bidirectional results: {e}")
            return self._create_error_result(f"Processing failed: {str(e)}")
    
    def process_bidirectional_results_reverse(self, trial_data: Dict[str, Any], 
                                             patients_data: List[Dict[str, Any]], 
                                             llm_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bidirectional results for trial-to-patients evaluation.
        
        Args:
            trial_data: Trial information
            patients_data: List of patient information
            llm_results: Raw LLM response data
            
        Returns:
            Structured evaluation results
        """
        try:
            if "error" in llm_results:
                logger.error(f"LLM results contain error: {llm_results['error']}")
                return self._create_error_result(llm_results["error"])
            
            # Extract evaluations from LLM results
            evaluations = llm_results.get("bidirectional_evaluations", [])
            summary = llm_results.get("summary", {})
            metadata = llm_results.get("evaluation_metadata", {})
            
            # Process each evaluation
            processed_evaluations = []
            for i, evaluation in enumerate(evaluations):
                processed_eval = self._process_single_evaluation_reverse(evaluation, patients_data[i] if i < len(patients_data) else {})
                processed_evaluations.append(processed_eval)
            
            # Create final result structure
            final_result = {
                "evaluation_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "trial_info": {
                    "trial_id": trial_data.get('trial_id'),
                    "title": trial_data.get('title'),
                    "condition": trial_data.get('condition'),
                    "phase": trial_data.get('phase'),
                    "status": trial_data.get('status'),
                    "investigator": trial_data.get('investigator')
                },
                "bidirectional_results": processed_evaluations,
                "summary": self._calculate_summary_reverse(processed_evaluations),
                "llm_summary": summary,
                "processing_metadata": {
                    "evaluation_method": "unified_bidirectional_reverse",
                    "total_patients_evaluated": len(processed_evaluations),
                    "processing_timestamp": datetime.now().isoformat(),
                    "llm_metadata": metadata
                },
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Processed reverse bidirectional results for {len(processed_evaluations)} patients")
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing reverse bidirectional results: {e}")
            return self._create_error_result(f"Processing failed: {str(e)}")
    
    def process_batch_results(self, patients_data: List[Dict[str, Any]], 
                            trials_data: List[Dict[str, Any]], 
                            llm_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process batch evaluation results.
        
        Args:
            patients_data: List of patient information
            trials_data: List of trial information
            llm_results: Raw LLM response data
            
        Returns:
            List of processed evaluation results
        """
        try:
            if "error" in llm_results:
                logger.error(f"LLM results contain error: {llm_results['error']}")
                return []
            
            # Extract batch evaluations from LLM results
            batch_evaluations = llm_results.get("batch_evaluations", [])
            
            # Process each batch evaluation
            processed_results = []
            for evaluation in batch_evaluations:
                processed_eval = self._process_batch_evaluation(evaluation)
                processed_results.append(processed_eval)
            
            logger.info(f"Processed {len(processed_results)} batch evaluations")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error processing batch results: {e}")
            return []
    
    def _process_single_evaluation(self, evaluation: Dict[str, Any], 
                                 trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single bidirectional evaluation."""
        try:
            # Extract trial information
            trial_info = {
                "trial_id": evaluation.get("trial_id", trial_data.get('trial_id', 'Unknown')),
                "title": evaluation.get("trial_title", trial_data.get('title', 'Unknown')),
                "phase": evaluation.get("trial_phase", trial_data.get('phase', 'Unknown')),
                "status": evaluation.get("trial_status", trial_data.get('status', 'Unknown')),
                "hybrid_score": trial_data.get('hybrid_score', 0)
            }
            
            # Process patient-to-trial evaluation
            p2t_eval = evaluation.get("patient_to_trial_evaluation", {})
            processed_p2t = self._process_patient_to_trial_evaluation(p2t_eval)
            
            # Process trial-to-patient evaluation
            t2p_eval = evaluation.get("trial_to_patient_evaluation", {})
            processed_t2p = self._process_trial_to_patient_evaluation(t2p_eval)
            
            # Calculate overall compatibility
            overall_compatibility = self._calculate_overall_compatibility(processed_p2t, processed_t2p)
            
            return {
                "trial_info": trial_info,
                "patient_to_trial_evaluation": processed_p2t,
                "trial_to_patient_evaluation": processed_t2p,
                "overall_compatibility": overall_compatibility
            }
            
        except Exception as e:
            logger.error(f"Error processing single evaluation: {e}")
            return self._create_empty_evaluation()
    
    def _process_single_evaluation_reverse(self, evaluation: Dict[str, Any], 
                                         patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single bidirectional evaluation (reverse direction)."""
        try:
            # Extract patient information
            patient_info = {
                "patient_id": evaluation.get("patient_id", patient_data.get('patient_id', 'Unknown')),
                "mrn": evaluation.get("patient_mrn", patient_data.get('mrn', 'Unknown')),
                "age": evaluation.get("patient_age", patient_data.get('age', 'Unknown')),
                "gender": evaluation.get("patient_gender", patient_data.get('gender', 'Unknown')),
                "hybrid_score": patient_data.get('hybrid_score', 0)
            }
            
            # Process patient-to-trial evaluation
            p2t_eval = evaluation.get("patient_to_trial_evaluation", {})
            processed_p2t = self._process_patient_to_trial_evaluation(p2t_eval)
            
            # Process trial-to-patient evaluation
            t2p_eval = evaluation.get("trial_to_patient_evaluation", {})
            processed_t2p = self._process_trial_to_patient_evaluation(t2p_eval)
            
            # Calculate overall compatibility
            overall_compatibility = self._calculate_overall_compatibility(processed_p2t, processed_t2p)
            
            return {
                "patient_info": patient_info,
                "patient_to_trial_evaluation": processed_p2t,
                "trial_to_patient_evaluation": processed_t2p,
                "overall_compatibility": overall_compatibility
            }
            
        except Exception as e:
            logger.error(f"Error processing single evaluation reverse: {e}")
            return self._create_empty_evaluation()
    
    def _process_batch_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single batch evaluation."""
        try:
            # Extract basic information
            patient_id = evaluation.get("patient_id", "Unknown")
            trial_id = evaluation.get("trial_id", "Unknown")
            
            # Process evaluations
            p2t_eval = evaluation.get("patient_to_trial_evaluation", {})
            processed_p2t = self._process_patient_to_trial_evaluation(p2t_eval)
            
            t2p_eval = evaluation.get("trial_to_patient_evaluation", {})
            processed_t2p = self._process_trial_to_patient_evaluation(t2p_eval)
            
            # Calculate overall compatibility
            overall_compatibility = self._calculate_overall_compatibility(processed_p2t, processed_t2p)
            
            return {
                "patient_id": patient_id,
                "trial_id": trial_id,
                "patient_to_trial_evaluation": processed_p2t,
                "trial_to_patient_evaluation": processed_t2p,
                "overall_compatibility": overall_compatibility
            }
            
        except Exception as e:
            logger.error(f"Error processing batch evaluation: {e}")
            return self._create_empty_evaluation()
    
    def _process_patient_to_trial_evaluation(self, p2t_eval: Dict[str, Any]) -> Dict[str, Any]:
        """Process patient-to-trial evaluation data."""
        return {
            "eligibility_status": p2t_eval.get("eligibility_status", "UNKNOWN"),
            "confidence_score": self._safe_int(p2t_eval.get("confidence_score", 0)),
            "reasoning": p2t_eval.get("reasoning", "No reasoning provided"),
            "inclusion_criteria_met": p2t_eval.get("inclusion_criteria_met", []),
            "exclusion_criteria_status": p2t_eval.get("exclusion_criteria_status", []),
            "missing_information": p2t_eval.get("missing_information", []),
            "next_steps": p2t_eval.get("next_steps", "No next steps provided")
        }
    
    def _process_trial_to_patient_evaluation(self, t2p_eval: Dict[str, Any]) -> Dict[str, Any]:
        """Process trial-to-patient evaluation data."""
        return {
            "suitability_status": t2p_eval.get("suitability_status", "UNKNOWN"),
            "priority_score": self._safe_int(t2p_eval.get("priority_score", 0)),
            "reasoning": t2p_eval.get("reasoning", "No reasoning provided"),
            "strengths": t2p_eval.get("strengths", []),
            "concerns": t2p_eval.get("concerns", []),
            "enrollment_recommendation": t2p_eval.get("enrollment_recommendation", "UNKNOWN")
        }
    
    def _calculate_overall_compatibility(self, p2t_eval: Dict[str, Any], 
                                       t2p_eval: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall compatibility score."""
        try:
            # Extract scores
            p2t_score = p2t_eval.get("confidence_score", 0)
            t2p_score = t2p_eval.get("priority_score", 0)
            
            # Calculate combined score (weighted average)
            combined_score = (p2t_score * 0.6) + (t2p_score * 0.4)
            
            # Determine match quality
            if combined_score >= 85:
                match_quality = "EXCELLENT"
            elif combined_score >= 70:
                match_quality = "GOOD"
            elif combined_score >= 55:
                match_quality = "FAIR"
            else:
                match_quality = "POOR"
            
            # Determine final recommendation
            p2t_status = p2t_eval.get("eligibility_status", "UNKNOWN")
            t2p_status = t2p_eval.get("suitability_status", "UNKNOWN")
            
            if p2t_status == "ELIGIBLE" and t2p_status in ["HIGHLY_SUITABLE", "SUITABLE"]:
                final_recommendation = "PROCEED_WITH_ENROLLMENT"
                enrollment_probability = f"HIGH ({int(combined_score)}%)"
            elif p2t_status == "NEED_MORE_INFO" or t2p_status == "NEED_MORE_INFO":
                final_recommendation = "AWAIT_MOLECULAR_TESTING"
                enrollment_probability = f"MEDIUM ({int(combined_score * 0.8)}%)"
            elif p2t_status == "NOT_ELIGIBLE" or t2p_status == "NOT_SUITABLE":
                final_recommendation = "NOT_SUITABLE"
                enrollment_probability = f"LOW ({int(combined_score * 0.3)}%)"
            else:
                final_recommendation = "REQUIRES_REVIEW"
                enrollment_probability = f"MEDIUM ({int(combined_score * 0.6)}%)"
            
            return {
                "match_quality": match_quality,
                "combined_score": round(combined_score, 2),
                "final_recommendation": final_recommendation,
                "enrollment_probability": enrollment_probability,
                "p2t_score": p2t_score,
                "t2p_score": t2p_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall compatibility: {e}")
            return {
                "match_quality": "UNKNOWN",
                "combined_score": 0.0,
                "final_recommendation": "REQUIRES_REVIEW",
                "enrollment_probability": "UNKNOWN",
                "p2t_score": 0,
                "t2p_score": 0
            }
    
    def _calculate_summary(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for patient-to-trials evaluation."""
        try:
            total_trials = len(evaluations)
            if total_trials == 0:
                return {"total_trials": 0}
            
            # Count by eligibility status
            eligible_count = sum(1 for eval_result in evaluations 
                               if eval_result.get("patient_to_trial_evaluation", {}).get("eligibility_status") == "ELIGIBLE")
            not_eligible_count = sum(1 for eval_result in evaluations 
                                   if eval_result.get("patient_to_trial_evaluation", {}).get("eligibility_status") == "NOT_ELIGIBLE")
            need_more_info_count = sum(1 for eval_result in evaluations 
                                     if eval_result.get("patient_to_trial_evaluation", {}).get("eligibility_status") == "NEED_MORE_INFO")
            
            # Count by suitability status
            highly_suitable_count = sum(1 for eval_result in evaluations 
                                      if eval_result.get("trial_to_patient_evaluation", {}).get("suitability_status") == "HIGHLY_SUITABLE")
            suitable_count = sum(1 for eval_result in evaluations 
                               if eval_result.get("trial_to_patient_evaluation", {}).get("suitability_status") == "SUITABLE")
            not_suitable_count = sum(1 for eval_result in evaluations 
                                   if eval_result.get("trial_to_patient_evaluation", {}).get("suitability_status") == "NOT_SUITABLE")
            
            # Calculate average scores
            avg_confidence = sum(eval_result.get("patient_to_trial_evaluation", {}).get("confidence_score", 0) 
                                for eval_result in evaluations) / total_trials
            avg_priority = sum(eval_result.get("trial_to_patient_evaluation", {}).get("priority_score", 0) 
                             for eval_result in evaluations) / total_trials
            avg_compatibility = sum(eval_result.get("overall_compatibility", {}).get("combined_score", 0) 
                                  for eval_result in evaluations) / total_trials
            
            return {
                "total_trials_evaluated": total_trials,
                "eligible_trials": eligible_count,
                "not_eligible_trials": not_eligible_count,
                "need_more_info_trials": need_more_info_count,
                "highly_suitable_trials": highly_suitable_count,
                "suitable_trials": suitable_count,
                "not_suitable_trials": not_suitable_count,
                "average_confidence_score": round(avg_confidence, 2),
                "average_priority_score": round(avg_priority, 2),
                "average_compatibility_score": round(avg_compatibility, 2),
                "success_rate": round((eligible_count + suitable_count) / (total_trials * 2) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating summary: {e}")
            return {"error": str(e)}
    
    def _calculate_summary_reverse(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for trial-to-patients evaluation."""
        try:
            total_patients = len(evaluations)
            if total_patients == 0:
                return {"total_patients": 0}
            
            # Count by eligibility status
            eligible_count = sum(1 for eval_result in evaluations 
                               if eval_result.get("patient_to_trial_evaluation", {}).get("eligibility_status") == "ELIGIBLE")
            not_eligible_count = sum(1 for eval_result in evaluations 
                                   if eval_result.get("patient_to_trial_evaluation", {}).get("eligibility_status") == "NOT_ELIGIBLE")
            need_more_info_count = sum(1 for eval_result in evaluations 
                                     if eval_result.get("patient_to_trial_evaluation", {}).get("eligibility_status") == "NEED_MORE_INFO")
            
            # Count by suitability status
            highly_suitable_count = sum(1 for eval_result in evaluations 
                                      if eval_result.get("trial_to_patient_evaluation", {}).get("suitability_status") == "HIGHLY_SUITABLE")
            suitable_count = sum(1 for eval_result in evaluations 
                               if eval_result.get("trial_to_patient_evaluation", {}).get("suitability_status") == "SUITABLE")
            not_suitable_count = sum(1 for eval_result in evaluations 
                                   if eval_result.get("trial_to_patient_evaluation", {}).get("suitability_status") == "NOT_SUITABLE")
            
            # Calculate average scores
            avg_confidence = sum(eval_result.get("patient_to_trial_evaluation", {}).get("confidence_score", 0) 
                                for eval_result in evaluations) / total_patients
            avg_priority = sum(eval_result.get("trial_to_patient_evaluation", {}).get("priority_score", 0) 
                             for eval_result in evaluations) / total_patients
            avg_compatibility = sum(eval_result.get("overall_compatibility", {}).get("combined_score", 0) 
                                  for eval_result in evaluations) / total_patients
            
            return {
                "total_patients_evaluated": total_patients,
                "eligible_patients": eligible_count,
                "not_eligible_patients": not_eligible_count,
                "need_more_info_patients": need_more_info_count,
                "highly_suitable_patients": highly_suitable_count,
                "suitable_patients": suitable_count,
                "not_suitable_patients": not_suitable_count,
                "average_confidence_score": round(avg_confidence, 2),
                "average_priority_score": round(avg_priority, 2),
                "average_compatibility_score": round(avg_compatibility, 2),
                "success_rate": round((eligible_count + suitable_count) / (total_patients * 2) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating reverse summary: {e}")
            return {"error": str(e)}
    
    def _extract_condition_from_text(self, text: str) -> str:
        """Extract primary condition from patient text."""
        try:
            # Simple extraction - look for common cancer types
            text_lower = text.lower()
            conditions = [
                "lung cancer", "breast cancer", "prostate cancer", "colorectal cancer",
                "pancreatic cancer", "ovarian cancer", "leukemia", "lymphoma",
                "melanoma", "brain cancer", "liver cancer", "kidney cancer"
            ]
            
            for condition in conditions:
                if condition in text_lower:
                    return condition.title()
            
            return "Cancer (unspecified)"
            
        except Exception:
            return "Unknown condition"
    
    def _safe_int(self, value: Any) -> int:
        """Safely convert value to integer."""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                return int(float(value))
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _create_empty_evaluation(self) -> Dict[str, Any]:
        """Create empty evaluation structure."""
        return {
            "patient_to_trial_evaluation": {
                "eligibility_status": "UNKNOWN",
                "confidence_score": 0,
                "reasoning": "Evaluation failed",
                "inclusion_criteria_met": [],
                "exclusion_criteria_status": [],
                "missing_information": [],
                "next_steps": "Manual review required"
            },
            "trial_to_patient_evaluation": {
                "suitability_status": "UNKNOWN",
                "priority_score": 0,
                "reasoning": "Evaluation failed",
                "strengths": [],
                "concerns": [],
                "enrollment_recommendation": "REQUIRES_REVIEW"
            },
            "overall_compatibility": {
                "match_quality": "UNKNOWN",
                "combined_score": 0.0,
                "final_recommendation": "REQUIRES_REVIEW",
                "enrollment_probability": "UNKNOWN",
                "p2t_score": 0,
                "t2p_score": 0
            }
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "error": error_message,
            "success": False,
            "generated_at": datetime.now().isoformat(),
            "evaluation_method": "unified_bidirectional"
        }
