"""
Services module for clinical trial matching functionality
"""

# Import the new modular services
from .patient_to_trial import (
    PatientKeywordGenerator,
    PatientEmbeddingGenerator,
    PatientMatcher,
    PatientEvaluator
)

from .trial_to_patient import (
    TrialEmbeddingGenerator,
    TrialMatcher,
    TrialEvaluator,
    HybridMatcher
)

from .shared import (
    DatabaseUtils,
    EmbeddingUtils,
    LLMUtils
)

__all__ = [
    # Patient-to-Trial services
    "PatientKeywordGenerator",
    "PatientEmbeddingGenerator",
    "PatientMatcher",
    "PatientEvaluator",
    
    # Trial-to-Patient services
    "TrialEmbeddingGenerator",
    "TrialMatcher",
    "TrialEvaluator",
    "HybridMatcher",
    
    # Shared utilities
    "DatabaseUtils",
    "EmbeddingUtils",
    "LLMUtils"
]
