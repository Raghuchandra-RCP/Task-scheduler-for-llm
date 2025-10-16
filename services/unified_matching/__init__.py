"""
Unified Bidirectional Clinical Trial Matching Services

This module provides a single unified approach for evaluating both:
- Patient-to-Trial matching (is patient eligible for trial?)
- Trial-to-Patient matching (is patient suitable for trial?)

All evaluations are performed in a single LLM call for maximum efficiency.
"""

from .bidirectional_evaluator import UnifiedBidirectionalEvaluator
from .unified_prompt_engine import UnifiedPromptEngine
from .result_processor import ResultProcessor
from .compatibility_calculator import CompatibilityCalculator

__all__ = [
    'UnifiedBidirectionalEvaluator',
    'UnifiedPromptEngine', 
    'ResultProcessor',
    'CompatibilityCalculator'
]

__version__ = "1.0.0"
__author__ = "Clinical Trial Matching System"
