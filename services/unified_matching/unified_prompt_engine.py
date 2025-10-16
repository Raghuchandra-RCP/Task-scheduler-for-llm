"""
Unified Prompt Engine for Bidirectional Clinical Trial Matching

This module generates comprehensive prompts for bidirectional evaluation,
combining patient-to-trial and trial-to-patient analysis in a single LLM call.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger


class UnifiedPromptEngine:
    """
    Engine for generating unified prompts for bidirectional clinical trial matching.
    
    This class creates comprehensive prompts that allow the LLM to evaluate
    both patient eligibility for trials AND trial suitability for patients
    in a single API call.
    """
    
    def __init__(self):
        """Initialize the unified prompt engine."""
        self.prompt_templates = {
            "bidirectional_patient_trials": self._get_bidirectional_patient_trials_template(),
            "bidirectional_trial_patients": self._get_bidirectional_trial_patients_template(),
            "batch_bidirectional": self._get_batch_bidirectional_template()
        }
        logger.info("UnifiedPromptEngine initialized successfully")
    
    def generate_bidirectional_prompt(self, patient_data: Dict[str, Any], 
                                    trials_data: List[Dict[str, Any]]) -> str:
        """
        Generate unified prompt for patient-to-trials bidirectional evaluation.
        
        Args:
            patient_data: Patient information dictionary
            trials_data: List of trial information dictionaries
            
        Returns:
            Formatted prompt string for LLM
        """
        try:
            # Format patient information
            patient_text = self._format_patient_data(patient_data)
            
            # Format trials information
            trials_text = self._format_trials_data(trials_data)
            
            # Generate the complete prompt
            prompt = f"""
You are an expert clinical trial coordinator conducting a comprehensive bidirectional evaluation for clinical trial matching.

PATIENT PROFILE:
{patient_text}

CLINICAL TRIALS TO EVALUATE:
{trials_text}

EVALUATION TASK:
For EACH trial listed above, provide a comprehensive bidirectional analysis:

1. PATIENT → TRIAL EVALUATION:
   - Is this patient eligible for this trial?
   - What are the key inclusion/exclusion criteria met or missed?
   - What is the confidence level in this assessment?

2. TRIAL → PATIENT EVALUATION:
   - Is this patient suitable for this trial?
   - What are the patient's strengths and potential concerns?
   - What is the priority level for enrollment?

3. OVERALL COMPATIBILITY:
   - Combined assessment of the match quality
   - Final recommendation for next steps
   - Enrollment probability estimate

EVALUATION CRITERIA:
- Medical condition compatibility
- Age and gender requirements
- Disease stage and progression
- Prior treatments and contraindications
- Performance status and comorbidities
- Laboratory values and organ function
- Geographic and logistical factors
- Patient preferences and support system

Return ONLY a valid JSON object with this exact structure:
{{
    "bidirectional_evaluations": [
        {{
            "trial_id": "{trials_data[0].get('trial_id', 'Unknown') if trials_data else 'N/A'}",
            "trial_title": "{trials_data[0].get('title', 'Unknown') if trials_data else 'N/A'}",
            "trial_phase": "{trials_data[0].get('phase', 'Unknown') if trials_data else 'N/A'}",
            "trial_status": "{trials_data[0].get('status', 'Unknown') if trials_data else 'N/A'}",
            
            "patient_to_trial_evaluation": {{
                "eligibility_status": "ELIGIBLE|NOT_ELIGIBLE|NEED_MORE_INFO",
                "confidence_score": 85,
                "reasoning": "Detailed explanation of eligibility assessment",
                "inclusion_criteria_met": ["criteria1", "criteria2", "criteria3"],
                "exclusion_criteria_status": ["criteria1", "criteria2"],
                "missing_information": ["info1", "info2"],
                "next_steps": "Specific recommendations for this trial"
            }},
            
            "trial_to_patient_evaluation": {{
                "suitability_status": "HIGHLY_SUITABLE|SUITABLE|NOT_SUITABLE|NEED_MORE_INFO",
                "priority_score": 90,
                "reasoning": "Detailed explanation of suitability assessment",
                "strengths": ["strength1", "strength2", "strength3"],
                "concerns": ["concern1", "concern2"],
                "enrollment_recommendation": "HIGH_PRIORITY_ENROLLMENT|CONDITIONAL_ON_TESTING|NOT_RECOMMENDED"
            }},
            
            "overall_compatibility": {{
                "match_quality": "EXCELLENT|GOOD|FAIR|POOR",
                "combined_score": 87.5,
                "final_recommendation": "PROCEED_WITH_ENROLLMENT|AWAIT_MOLECULAR_TESTING|NOT_SUITABLE",
                "enrollment_probability": "HIGH (85%)|MEDIUM (60%)|LOW (15%)"
            }}
        }}
        // ... continue for all {len(trials_data)} trials
    ],
    "summary": {{
        "total_trials_evaluated": {len(trials_data)},
        "eligible_trials": 2,
        "need_more_info_trials": 1,
        "not_eligible_trials": 2,
        "highly_suitable_trials": 1,
        "average_compatibility": 78.5,
        "top_recommendations": [
            "Trial A - Proceed with enrollment (90% match)",
            "Trial B - Order molecular testing (67.5% potential match)"
        ],
        "action_items": [
            "Schedule screening for Trial A",
            "Order EGFR/PD-L1 testing for Trial B",
            "Consider alternative trials for chemotherapy options"
        ]
    }},
    "evaluation_metadata": {{
        "evaluation_type": "bidirectional_patient_trials",
        "patient_id": {patient_data.get('patient_id', 'Unknown')},
        "total_trials": {len(trials_data)},
        "generated_at": "{datetime.now().isoformat()}"
    }}
}}
"""
            
            logger.info(f"Generated bidirectional prompt for {len(trials_data)} trials")
            return prompt.strip()
            
        except Exception as e:
            logger.error(f"Error generating bidirectional prompt: {e}")
            return ""
    
    def generate_bidirectional_prompt_reverse(self, trial_data: Dict[str, Any], 
                                            patients_data: List[Dict[str, Any]]) -> str:
        """
        Generate unified prompt for trial-to-patients bidirectional evaluation.
        
        Args:
            trial_data: Trial information dictionary
            patients_data: List of patient information dictionaries
            
        Returns:
            Formatted prompt string for LLM
        """
        try:
            # Format trial information
            trial_text = self._format_trial_data(trial_data)
            
            # Format patients information
            patients_text = self._format_patients_data(patients_data)
            
            # Generate the complete prompt
            prompt = f"""
You are an expert clinical trial coordinator conducting a comprehensive bidirectional evaluation for clinical trial matching.

CLINICAL TRIAL PROFILE:
{trial_text}

PATIENTS TO EVALUATE:
{patients_text}

EVALUATION TASK:
For EACH patient listed above, provide a comprehensive bidirectional analysis:

1. PATIENT → TRIAL EVALUATION:
   - Is this patient eligible for this trial?
   - What are the key inclusion/exclusion criteria met or missed?
   - What is the confidence level in this assessment?

2. TRIAL → PATIENT EVALUATION:
   - Is this patient suitable for this trial?
   - What are the patient's strengths and potential concerns?
   - What is the priority level for enrollment?

3. OVERALL COMPATIBILITY:
   - Combined assessment of the match quality
   - Final recommendation for next steps
   - Enrollment probability estimate

EVALUATION CRITERIA:
- Medical condition compatibility
- Age and gender requirements
- Disease stage and progression
- Prior treatments and contraindications
- Performance status and comorbidities
- Laboratory values and organ function
- Geographic and logistical factors
- Patient preferences and support system

Return ONLY a valid JSON object with this exact structure:
{{
    "bidirectional_evaluations": [
        {{
            "patient_id": {patients_data[0].get('patient_id', 'Unknown') if patients_data else 'N/A'},
            "patient_mrn": "{patients_data[0].get('mrn', 'Unknown') if patients_data else 'N/A'}",
            "patient_age": {patients_data[0].get('age', 'Unknown') if patients_data else 'N/A'},
            "patient_gender": "{patients_data[0].get('gender', 'Unknown') if patients_data else 'N/A'}",
            
            "patient_to_trial_evaluation": {{
                "eligibility_status": "ELIGIBLE|NOT_ELIGIBLE|NEED_MORE_INFO",
                "confidence_score": 85,
                "reasoning": "Detailed explanation of eligibility assessment",
                "inclusion_criteria_met": ["criteria1", "criteria2", "criteria3"],
                "exclusion_criteria_status": ["criteria1", "criteria2"],
                "missing_information": ["info1", "info2"],
                "next_steps": "Specific recommendations for this trial"
            }},
            
            "trial_to_patient_evaluation": {{
                "suitability_status": "HIGHLY_SUITABLE|SUITABLE|NOT_SUITABLE|NEED_MORE_INFO",
                "priority_score": 90,
                "reasoning": "Detailed explanation of suitability assessment",
                "strengths": ["strength1", "strength2", "strength3"],
                "concerns": ["concern1", "concern2"],
                "enrollment_recommendation": "HIGH_PRIORITY_ENROLLMENT|CONDITIONAL_ON_TESTING|NOT_RECOMMENDED"
            }},
            
            "overall_compatibility": {{
                "match_quality": "EXCELLENT|GOOD|FAIR|POOR",
                "combined_score": 87.5,
                "final_recommendation": "PROCEED_WITH_ENROLLMENT|AWAIT_MOLECULAR_TESTING|NOT_SUITABLE",
                "enrollment_probability": "HIGH (85%)|MEDIUM (60%)|LOW (15%)"
            }}
        }}
        // ... continue for all {len(patients_data)} patients
    ],
    "summary": {{
        "total_patients_evaluated": {len(patients_data)},
        "eligible_patients": 3,
        "need_more_info_patients": 1,
        "not_eligible_patients": 1,
        "highly_suitable_patients": 2,
        "average_compatibility": 82.3,
        "top_recommendations": [
            "Patient A - Proceed with enrollment (92% match)",
            "Patient B - Good candidate (78% match)"
        ],
        "action_items": [
            "Schedule screening for top 3 patients",
            "Order additional testing for conditional patients",
            "Follow up with patients for enrollment"
        ]
    }},
    "evaluation_metadata": {{
        "evaluation_type": "bidirectional_trial_patients",
        "trial_id": "{trial_data.get('trial_id', 'Unknown')}",
        "total_patients": {len(patients_data)},
        "generated_at": "{datetime.now().isoformat()}"
    }}
}}
"""
            
            logger.info(f"Generated reverse bidirectional prompt for {len(patients_data)} patients")
            return prompt.strip()
            
        except Exception as e:
            logger.error(f"Error generating reverse bidirectional prompt: {e}")
            return ""
    
    def generate_batch_bidirectional_prompt(self, patients_data: List[Dict[str, Any]], 
                                          trials_data: List[Dict[str, Any]]) -> str:
        """
        Generate batch prompt for multiple patients and trials bidirectional evaluation.
        
        Args:
            patients_data: List of patient information dictionaries
            trials_data: List of trial information dictionaries
            
        Returns:
            Formatted prompt string for LLM
        """
        try:
            # Format all patients
            patients_text = ""
            for i, patient in enumerate(patients_data, 1):
                patients_text += f"\n{'='*60}\nPATIENT {i}:\n{'='*60}\n"
                patients_text += self._format_patient_data(patient)
            
            # Format all trials
            trials_text = ""
            for i, trial in enumerate(trials_data, 1):
                trials_text += f"\n{'='*60}\nTRIAL {i}:\n{'='*60}\n"
                trials_text += self._format_trial_data(trial)
            
            # Generate batch prompt
            prompt = f"""
You are an expert clinical trial coordinator conducting comprehensive bidirectional evaluations for clinical trial matching.

PATIENTS TO EVALUATE:
{patients_text}

CLINICAL TRIALS TO EVALUATE:
{trials_text}

EVALUATION TASK:
For EACH patient-trial combination, provide a comprehensive bidirectional analysis:

1. PATIENT → TRIAL EVALUATION:
   - Is this patient eligible for this trial?
   - Key inclusion/exclusion criteria assessment
   - Confidence level in the assessment

2. TRIAL → PATIENT EVALUATION:
   - Is this patient suitable for this trial?
   - Patient strengths and concerns
   - Enrollment priority level

3. OVERALL COMPATIBILITY:
   - Combined match quality assessment
   - Final recommendation
   - Enrollment probability

Return ONLY a valid JSON object with this structure:
{{
    "batch_evaluations": [
        {{
            "patient_id": {patients_data[0].get('patient_id', 'Unknown') if patients_data else 'N/A'},
            "trial_id": "{trials_data[0].get('trial_id', 'Unknown') if trials_data else 'N/A'}",
            "patient_to_trial_evaluation": {{
                "eligibility_status": "ELIGIBLE|NOT_ELIGIBLE|NEED_MORE_INFO",
                "confidence_score": 85,
                "reasoning": "Brief explanation",
                "key_criteria_met": ["criteria1", "criteria2"],
                "key_criteria_missed": ["criteria1"]
            }},
            "trial_to_patient_evaluation": {{
                "suitability_status": "HIGHLY_SUITABLE|SUITABLE|NOT_SUITABLE|NEED_MORE_INFO",
                "priority_score": 90,
                "reasoning": "Brief explanation",
                "strengths": ["strength1", "strength2"],
                "concerns": ["concern1"]
            }},
            "overall_compatibility": {{
                "match_quality": "EXCELLENT|GOOD|FAIR|POOR",
                "combined_score": 87.5,
                "final_recommendation": "PROCEED_WITH_ENROLLMENT|AWAIT_MOLECULAR_TESTING|NOT_SUITABLE"
            }}
        }}
        // ... continue for all combinations
    ],
    "batch_summary": {{
        "total_evaluations": {len(patients_data) * len(trials_data)},
        "eligible_matches": 5,
        "suitable_matches": 7,
        "average_compatibility": 78.5,
        "top_matches": [
            "Patient 1 - Trial A (92% match)",
            "Patient 2 - Trial B (88% match)"
        ]
    }},
    "evaluation_metadata": {{
        "evaluation_type": "batch_bidirectional",
        "total_patients": {len(patients_data)},
        "total_trials": {len(trials_data)},
        "generated_at": "{datetime.now().isoformat()}"
    }}
}}
"""
            
            logger.info(f"Generated batch prompt for {len(patients_data)} patients and {len(trials_data)} trials")
            return prompt.strip()
            
        except Exception as e:
            logger.error(f"Error generating batch prompt: {e}")
            return ""
    
    def parse_bidirectional_response(self, response: str) -> Dict[str, Any]:
        """
        Parse bidirectional response from LLM.
        
        Args:
            response: Raw response string from LLM
            
        Returns:
            Parsed dictionary with bidirectional results
        """
        try:
            # Clean the response
            cleaned_response = self._clean_llm_response(response)
            
            # Parse JSON
            parsed_data = json.loads(cleaned_response)
            
            # Validate structure
            if "bidirectional_evaluations" not in parsed_data:
                logger.error("Invalid response structure: missing bidirectional_evaluations")
                return {"error": "Invalid response structure"}
            
            logger.info(f"Successfully parsed bidirectional response with {len(parsed_data['bidirectional_evaluations'])} evaluations")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"error": f"Failed to parse JSON response: {str(e)}"}
        except Exception as e:
            logger.error(f"Error parsing bidirectional response: {e}")
            return {"error": f"Failed to parse response: {str(e)}"}
    
    def parse_bidirectional_response_reverse(self, response: str) -> Dict[str, Any]:
        """
        Parse reverse bidirectional response from LLM.
        
        Args:
            response: Raw response string from LLM
            
        Returns:
            Parsed dictionary with bidirectional results
        """
        try:
            # Clean the response
            cleaned_response = self._clean_llm_response(response)
            
            # Parse JSON
            parsed_data = json.loads(cleaned_response)
            
            # Validate structure
            if "bidirectional_evaluations" not in parsed_data:
                logger.error("Invalid response structure: missing bidirectional_evaluations")
                return {"error": "Invalid response structure"}
            
            logger.info(f"Successfully parsed reverse bidirectional response with {len(parsed_data['bidirectional_evaluations'])} evaluations")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"error": f"Failed to parse JSON response: {str(e)}"}
        except Exception as e:
            logger.error(f"Error parsing reverse bidirectional response: {e}")
            return {"error": f"Failed to parse response: {str(e)}"}
    
    def parse_batch_bidirectional_response(self, response: str) -> Dict[str, Any]:
        """
        Parse batch bidirectional response from LLM.
        
        Args:
            response: Raw response string from LLM
            
        Returns:
            Parsed dictionary with batch results
        """
        try:
            # Clean the response
            cleaned_response = self._clean_llm_response(response)
            
            # Parse JSON
            parsed_data = json.loads(cleaned_response)
            
            # Validate structure
            if "batch_evaluations" not in parsed_data:
                logger.error("Invalid response structure: missing batch_evaluations")
                return {"error": "Invalid response structure"}
            
            logger.info(f"Successfully parsed batch response with {len(parsed_data['batch_evaluations'])} evaluations")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"error": f"Failed to parse JSON response: {str(e)}"}
        except Exception as e:
            logger.error(f"Error parsing batch response: {e}")
            return {"error": f"Failed to parse response: {str(e)}"}
    
    def _format_patient_data(self, patient_data: Dict[str, Any]) -> str:
        """Format patient data for prompt."""
        return f"""
Patient ID: {patient_data.get('patient_id', 'Unknown')}
MRN: {patient_data.get('mrn', 'Unknown')}
Age: {patient_data.get('age', 'Unknown')}
Gender: {patient_data.get('gender', 'Unknown')}
Oncologist: {patient_data.get('oncologist', 'Unknown')}
Date of Visit: {patient_data.get('date_of_visit', 'Unknown')}

Medical Record Summary:
{patient_data.get('combined_text', 'No medical record available')}
"""
    
    def _format_trial_data(self, trial_data: Dict[str, Any]) -> str:
        """Format trial data for prompt."""
        return f"""
Trial ID: {trial_data.get('trial_id', 'Unknown')}
Title: {trial_data.get('title', 'Unknown')}
Condition: {trial_data.get('condition', 'Unknown')}
Phase: {trial_data.get('phase', 'Unknown')}
Status: {trial_data.get('status', 'Unknown')}
Investigator: {trial_data.get('investigator', 'Unknown')}
Age Range: {trial_data.get('minimum_age', 'Not specified')} - {trial_data.get('maximum_age', 'Not specified')}
Gender: {trial_data.get('sex', 'Not specified')}

Brief Summary: {trial_data.get('brief_summary', 'Not available')}

Detailed Description: {trial_data.get('detailed_description', 'Not available')}

Inclusion Criteria: {trial_data.get('inclusion_criteria', 'Not available')}

Exclusion Criteria: {trial_data.get('exclusion_criteria', 'Not available')}

Eligibility Criteria: {trial_data.get('eligibility_criteria', 'Not available')}
"""
    
    def _format_trials_data(self, trials_data: List[Dict[str, Any]]) -> str:
        """Format multiple trials data for prompt."""
        trials_text = ""
        for i, trial in enumerate(trials_data, 1):
            trials_text += f"\n{'='*60}\nTRIAL {i}:\n{'='*60}\n"
            trials_text += self._format_trial_data(trial)
        return trials_text
    
    def _format_patients_data(self, patients_data: List[Dict[str, Any]]) -> str:
        """Format multiple patients data for prompt."""
        patients_text = ""
        for i, patient in enumerate(patients_data, 1):
            patients_text += f"\n{'='*60}\nPATIENT {i}:\n{'='*60}\n"
            patients_text += self._format_patient_data(patient)
        return patients_text
    
    def _clean_llm_response(self, response: str) -> str:
        """Clean LLM response by removing code block markers."""
        cleaned = response.strip()
        
        # Remove code block markers
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        return cleaned.strip()
    
    def _get_bidirectional_patient_trials_template(self) -> str:
        """Get template for bidirectional patient-to-trials evaluation."""
        return """
You are an expert clinical trial coordinator conducting bidirectional evaluation.

PATIENT PROFILE:
{patient_data}

CLINICAL TRIALS:
{trials_data}

For each trial, evaluate:
1. Patient eligibility for trial
2. Trial suitability for patient
3. Overall compatibility

Return structured JSON with bidirectional results.
"""
    
    def _get_bidirectional_trial_patients_template(self) -> str:
        """Get template for bidirectional trial-to-patients evaluation."""
        return """
You are an expert clinical trial coordinator conducting bidirectional evaluation.

CLINICAL TRIAL PROFILE:
{trial_data}

PATIENTS:
{patients_data}

For each patient, evaluate:
1. Patient eligibility for trial
2. Trial suitability for patient
3. Overall compatibility

Return structured JSON with bidirectional results.
"""
    
    def _get_batch_bidirectional_template(self) -> str:
        """Get template for batch bidirectional evaluation."""
        return """
You are an expert clinical trial coordinator conducting batch bidirectional evaluation.

PATIENTS:
{patients_data}

CLINICAL TRIALS:
{trials_data}

For each patient-trial combination, evaluate:
1. Patient eligibility for trial
2. Trial suitability for patient
3. Overall compatibility

Return structured JSON with batch results.
"""
