"""
Compatibility Calculator for Unified Bidirectional Clinical Trial Matching

This module calculates compatibility scores and provides advanced scoring algorithms
for bidirectional evaluation results.
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from loguru import logger


class CompatibilityCalculator:
    """
    Calculates compatibility scores and provides advanced scoring algorithms.
    
    This class provides various methods for calculating compatibility scores
    between patients and clinical trials based on bidirectional evaluations.
    """
    
    def __init__(self):
        """Initialize the compatibility calculator."""
        # Scoring weights for different factors
        self.weights = {
            "eligibility_weight": 0.4,      # Patient eligibility for trial
            "suitability_weight": 0.3,      # Trial suitability for patient
            "confidence_weight": 0.2,       # Confidence in evaluation
            "priority_weight": 0.1         # Priority score
        }
        
        # Status mappings for scoring
        self.eligibility_scores = {
            "ELIGIBLE": 100,
            "NEED_MORE_INFO": 60,
            "NOT_ELIGIBLE": 0
        }
        
        self.suitability_scores = {
            "HIGHLY_SUITABLE": 100,
            "SUITABLE": 80,
            "POTENTIALLY_SUITABLE": 60,
            "NEED_MORE_INFO": 40,
            "NOT_SUITABLE": 0
        }
        
        self.match_quality_thresholds = {
            "EXCELLENT": 85,
            "GOOD": 70,
            "FAIR": 55,
            "POOR": 0
        }
        
        logger.info("CompatibilityCalculator initialized successfully")
    
    def calculate_compatibility_score(self, p2t_evaluation: Dict[str, Any], 
                                    t2p_evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive compatibility score.
        
        Args:
            p2t_evaluation: Patient-to-trial evaluation results
            t2p_evaluation: Trial-to-patient evaluation results
            
        Returns:
            Dictionary containing compatibility metrics
        """
        try:
            # Extract basic scores
            eligibility_status = p2t_evaluation.get("eligibility_status", "UNKNOWN")
            suitability_status = t2p_evaluation.get("suitability_status", "UNKNOWN")
            confidence_score = p2t_evaluation.get("confidence_score", 0)
            priority_score = t2p_evaluation.get("priority_score", 0)
            
            # Calculate weighted score
            weighted_score = self._calculate_weighted_score(
                eligibility_status, suitability_status, confidence_score, priority_score
            )
            
            # Calculate individual component scores
            eligibility_score = self.eligibility_scores.get(eligibility_status, 0)
            suitability_score = self.suitability_scores.get(suitability_status, 0)
            
            # Calculate harmonic mean for balanced scoring
            harmonic_mean = self._calculate_harmonic_mean(eligibility_score, suitability_score)
            
            # Calculate geometric mean for multiplicative scoring
            geometric_mean = self._calculate_geometric_mean(eligibility_score, suitability_score)
            
            # Determine match quality
            match_quality = self._determine_match_quality(weighted_score)
            
            # Calculate enrollment probability
            enrollment_probability = self._calculate_enrollment_probability(
                eligibility_status, suitability_status, weighted_score
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                eligibility_status, suitability_status, weighted_score
            )
            
            return {
                "weighted_score": round(weighted_score, 2),
                "eligibility_score": eligibility_score,
                "suitability_score": suitability_score,
                "harmonic_mean": round(harmonic_mean, 2),
                "geometric_mean": round(geometric_mean, 2),
                "match_quality": match_quality,
                "enrollment_probability": enrollment_probability,
                "recommendation": recommendation,
                "confidence_level": self._calculate_confidence_level(confidence_score, priority_score),
                "risk_assessment": self._assess_risk(eligibility_status, suitability_status)
            }
            
        except Exception as e:
            logger.error(f"Error calculating compatibility score: {e}")
            return self._create_default_score()
    
    def calculate_batch_compatibility(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate compatibility metrics for a batch of evaluations.
        
        Args:
            evaluations: List of evaluation results
            
        Returns:
            Dictionary containing batch compatibility metrics
        """
        try:
            if not evaluations:
                return {"error": "No evaluations provided"}
            
            # Extract scores
            weighted_scores = []
            eligibility_scores = []
            suitability_scores = []
            match_qualities = []
            
            for evaluation in evaluations:
                p2t_eval = evaluation.get("patient_to_trial_evaluation", {})
                t2p_eval = evaluation.get("trial_to_patient_evaluation", {})
                
                compatibility = self.calculate_compatibility_score(p2t_eval, t2p_eval)
                
                weighted_scores.append(compatibility["weighted_score"])
                eligibility_scores.append(compatibility["eligibility_score"])
                suitability_scores.append(compatibility["suitability_score"])
                match_qualities.append(compatibility["match_quality"])
            
            # Calculate statistics
            stats = {
                "total_evaluations": len(evaluations),
                "average_weighted_score": round(np.mean(weighted_scores), 2),
                "average_eligibility_score": round(np.mean(eligibility_scores), 2),
                "average_suitability_score": round(np.mean(suitability_scores), 2),
                "std_weighted_score": round(np.std(weighted_scores), 2),
                "min_score": round(np.min(weighted_scores), 2),
                "max_score": round(np.max(weighted_scores), 2),
                "median_score": round(np.median(weighted_scores), 2)
            }
            
            # Count by match quality
            quality_counts = {}
            for quality in ["EXCELLENT", "GOOD", "FAIR", "POOR"]:
                quality_counts[quality.lower()] = sum(1 for q in match_qualities if q == quality)
            
            stats["match_quality_distribution"] = quality_counts
            
            # Calculate percentiles
            stats["percentiles"] = {
                "25th": round(np.percentile(weighted_scores, 25), 2),
                "50th": round(np.percentile(weighted_scores, 50), 2),
                "75th": round(np.percentile(weighted_scores, 75), 2),
                "90th": round(np.percentile(weighted_scores, 90), 2),
                "95th": round(np.percentile(weighted_scores, 95), 2)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating batch compatibility: {e}")
            return {"error": str(e)}
    
    def calculate_ranking_score(self, evaluation: Dict[str, Any]) -> float:
        """
        Calculate ranking score for sorting evaluations.
        
        Args:
            evaluation: Single evaluation result
            
        Returns:
            Ranking score for sorting
        """
        try:
            p2t_eval = evaluation.get("patient_to_trial_evaluation", {})
            t2p_eval = evaluation.get("trial_to_patient_evaluation", {})
            
            # Base compatibility score
            compatibility = self.calculate_compatibility_score(p2t_eval, t2p_eval)
            base_score = compatibility["weighted_score"]
            
            # Bonus factors
            bonus = 0
            
            # Bonus for high confidence
            confidence_score = p2t_eval.get("confidence_score", 0)
            if confidence_score >= 90:
                bonus += 5
            elif confidence_score >= 80:
                bonus += 3
            elif confidence_score >= 70:
                bonus += 1
            
            # Bonus for high priority
            priority_score = t2p_eval.get("priority_score", 0)
            if priority_score >= 90:
                bonus += 5
            elif priority_score >= 80:
                bonus += 3
            elif priority_score >= 70:
                bonus += 1
            
            # Bonus for excellent match quality
            if compatibility["match_quality"] == "EXCELLENT":
                bonus += 10
            elif compatibility["match_quality"] == "GOOD":
                bonus += 5
            
            # Penalty for missing information
            missing_info = len(p2t_eval.get("missing_information", []))
            penalty = missing_info * 2
            
            final_score = base_score + bonus - penalty
            return max(0, min(100, final_score))  # Clamp between 0 and 100
            
        except Exception as e:
            logger.error(f"Error calculating ranking score: {e}")
            return 0.0
    
    def _calculate_weighted_score(self, eligibility_status: str, suitability_status: str,
                                confidence_score: int, priority_score: int) -> float:
        """Calculate weighted compatibility score."""
        try:
            eligibility_score = self.eligibility_scores.get(eligibility_status, 0)
            suitability_score = self.suitability_scores.get(suitability_status, 0)
            
            weighted_score = (
                eligibility_score * self.weights["eligibility_weight"] +
                suitability_score * self.weights["suitability_weight"] +
                confidence_score * self.weights["confidence_weight"] +
                priority_score * self.weights["priority_weight"]
            )
            
            return weighted_score
            
        except Exception as e:
            logger.error(f"Error calculating weighted score: {e}")
            return 0.0
    
    def _calculate_harmonic_mean(self, score1: float, score2: float) -> float:
        """Calculate harmonic mean of two scores."""
        try:
            if score1 == 0 or score2 == 0:
                return 0.0
            return 2 * (score1 * score2) / (score1 + score2)
        except ZeroDivisionError:
            return 0.0
    
    def _calculate_geometric_mean(self, score1: float, score2: float) -> float:
        """Calculate geometric mean of two scores."""
        try:
            return np.sqrt(score1 * score2)
        except Exception:
            return 0.0
    
    def _determine_match_quality(self, score: float) -> str:
        """Determine match quality based on score."""
        if score >= self.match_quality_thresholds["EXCELLENT"]:
            return "EXCELLENT"
        elif score >= self.match_quality_thresholds["GOOD"]:
            return "GOOD"
        elif score >= self.match_quality_thresholds["FAIR"]:
            return "FAIR"
        else:
            return "POOR"
    
    def _calculate_enrollment_probability(self, eligibility_status: str, 
                                        suitability_status: str, score: float) -> str:
        """Calculate enrollment probability."""
        try:
            # Base probability from status
            if eligibility_status == "ELIGIBLE" and suitability_status in ["HIGHLY_SUITABLE", "SUITABLE"]:
                base_prob = 85
            elif eligibility_status == "NEED_MORE_INFO" or suitability_status == "NEED_MORE_INFO":
                base_prob = 60
            elif eligibility_status == "NOT_ELIGIBLE" or suitability_status == "NOT_SUITABLE":
                base_prob = 15
            else:
                base_prob = 40
            
            # Adjust based on score
            score_adjustment = (score - 50) * 0.5  # Scale adjustment
            final_prob = max(0, min(100, base_prob + score_adjustment))
            
            if final_prob >= 80:
                return f"HIGH ({int(final_prob)}%)"
            elif final_prob >= 60:
                return f"MEDIUM ({int(final_prob)}%)"
            else:
                return f"LOW ({int(final_prob)}%)"
                
        except Exception as e:
            logger.error(f"Error calculating enrollment probability: {e}")
            return "UNKNOWN"
    
    def _generate_recommendation(self, eligibility_status: str, 
                               suitability_status: str, score: float) -> str:
        """Generate recommendation based on evaluation."""
        try:
            if eligibility_status == "ELIGIBLE" and suitability_status in ["HIGHLY_SUITABLE", "SUITABLE"]:
                if score >= 85:
                    return "PROCEED_WITH_ENROLLMENT"
                else:
                    return "PROCEED_WITH_CAUTION"
            elif eligibility_status == "NEED_MORE_INFO" or suitability_status == "NEED_MORE_INFO":
                return "AWAIT_MOLECULAR_TESTING"
            elif eligibility_status == "NOT_ELIGIBLE" or suitability_status == "NOT_SUITABLE":
                return "NOT_SUITABLE"
            else:
                return "REQUIRES_REVIEW"
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "REQUIRES_REVIEW"
    
    def _calculate_confidence_level(self, confidence_score: int, priority_score: int) -> str:
        """Calculate overall confidence level."""
        try:
            avg_score = (confidence_score + priority_score) / 2
            
            if avg_score >= 90:
                return "VERY_HIGH"
            elif avg_score >= 80:
                return "HIGH"
            elif avg_score >= 70:
                return "MEDIUM"
            elif avg_score >= 60:
                return "LOW"
            else:
                return "VERY_LOW"
                
        except Exception as e:
            logger.error(f"Error calculating confidence level: {e}")
            return "UNKNOWN"
    
    def _assess_risk(self, eligibility_status: str, suitability_status: str) -> str:
        """Assess risk level for the match."""
        try:
            if eligibility_status == "NOT_ELIGIBLE" or suitability_status == "NOT_SUITABLE":
                return "HIGH_RISK"
            elif eligibility_status == "NEED_MORE_INFO" or suitability_status == "NEED_MORE_INFO":
                return "MEDIUM_RISK"
            elif eligibility_status == "ELIGIBLE" and suitability_status in ["HIGHLY_SUITABLE", "SUITABLE"]:
                return "LOW_RISK"
            else:
                return "UNKNOWN_RISK"
                
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return "UNKNOWN_RISK"
    
    def _create_default_score(self) -> Dict[str, Any]:
        """Create default score structure."""
        return {
            "weighted_score": 0.0,
            "eligibility_score": 0,
            "suitability_score": 0,
            "harmonic_mean": 0.0,
            "geometric_mean": 0.0,
            "match_quality": "POOR",
            "enrollment_probability": "LOW (0%)",
            "recommendation": "REQUIRES_REVIEW",
            "confidence_level": "VERY_LOW",
            "risk_assessment": "HIGH_RISK"
        }
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Update scoring weights.
        
        Args:
            new_weights: Dictionary with new weight values
        """
        try:
            for key, value in new_weights.items():
                if key in self.weights:
                    self.weights[key] = value
            
            logger.info(f"Updated scoring weights: {self.weights}")
            
        except Exception as e:
            logger.error(f"Error updating weights: {e}")
    
    def get_weights(self) -> Dict[str, float]:
        """Get current scoring weights."""
        return self.weights.copy()
    
    def validate_weights(self, weights: Dict[str, float]) -> bool:
        """
        Validate that weights sum to 1.0.
        
        Args:
            weights: Dictionary of weights to validate
            
        Returns:
            True if weights are valid, False otherwise
        """
        try:
            total = sum(weights.values())
            return abs(total - 1.0) < 0.001  # Allow small floating point errors
            
        except Exception as e:
            logger.error(f"Error validating weights: {e}")
            return False
