"""
Trial-to-Patient Pipeline Orchestrator
Coordinates trial-to-patient matching components
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple

from services.trial_to_patient.trial_embedding import TrialEmbeddingGenerator
from services.trial_to_patient.trial_matcher import TrialMatcher
from services.trial_to_patient.hybrid_matcher import HybridMatcher
from services.trial_to_patient.trial_evaluator import TrialEvaluator

class TrialToPatientOrchestrator:
    def __init__(self):
        self.embedding_generator = TrialEmbeddingGenerator()
        self.trial_matcher = TrialMatcher()
        self.hybrid_matcher = HybridMatcher()
        self.trial_evaluator = TrialEvaluator()
        
        # Results directory
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

    def run_embedding_generation(self) -> Dict[str, Any]:
        """Run embedding generation for trials"""
        print("=" * 80)
        print("STEP 1: TRIAL EMBEDDING GENERATION")
        print("=" * 80)
        
        results = self.embedding_generator.run_trial_embedding_generation()
        
        if results:
            print("✅ Embedding generation completed successfully!")
            return results
        else:
            print("❌ Embedding generation failed!")
            return {}

    def run_trial_patient_matching(self, trial_id: str, age_range: Tuple[int, int] = None, gender: str = None) -> Dict[str, Any]:
        """Run trial-to-patient matching pipeline"""
        print("=" * 80)
        print("STEP 2: TRIAL-TO-PATIENT MATCHING")
        print("=" * 80)
        
        results = self.trial_evaluator.run_trial_matching_pipeline(
            trial_id=trial_id,
            age_range=age_range,
            gender=gender
        )
        
        if results:
            print("✅ Trial-to-patient matching completed successfully!")
            return results
        else:
            print("❌ Trial-to-patient matching failed!")
            return {}

    def run_complete_pipeline(self, trial_id: str, age_range: Tuple[int, int] = None, 
                            gender: str = None) -> Dict[str, Any]:
        """Run the complete trial-to-patient matching pipeline"""
        print("🚀 STARTING TRIAL-TO-PATIENT MATCHING PIPELINE")
        print(f"Trial ID: {trial_id}")
        print(f"Age Range: {age_range}")
        print(f"Gender Filter: {gender}")
        print("=" * 80)
        
        pipeline_results = {
            "pipeline_started_at": datetime.now().isoformat(),
            "trial_id": trial_id,
            "filters": {
                "age_range": age_range,
                "gender": gender
            },
            "steps": {}
        }
        
        try:
            # Step 1: Embedding Generation
            embedding_results = self.run_embedding_generation()
            pipeline_results["steps"]["embedding_generation"] = {
                "status": "completed" if embedding_results else "failed",
                "results": embedding_results
            }
            
            if not embedding_results:
                print("❌ Pipeline stopped due to embedding generation failure")
                return pipeline_results
            
            # Step 2: Trial-to-Patient Matching
            matching_results = self.run_trial_patient_matching(trial_id, age_range, gender)
            pipeline_results["steps"]["trial_patient_matching"] = {
                "status": "completed" if matching_results else "failed",
                "results": matching_results
            }
            
            # Pipeline Summary
            pipeline_results["pipeline_completed_at"] = datetime.now().isoformat()
            pipeline_results["overall_status"] = "completed"
            
            # Save pipeline results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pipeline_file = self.results_dir / f"trial_to_patient_pipeline_{trial_id}_{timestamp}.json"
            
            # Use safe_json_dump to handle numpy types
            from services.shared.database_utils import safe_json_dump
            safe_json_dump(pipeline_results, pipeline_file, indent=2, ensure_ascii=False)
            
            print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"Pipeline results saved to: {pipeline_file}")
            
            # Print final summary
            if matching_results:
                summary = matching_results.get('summary', {})
                print(f"\nFinal Summary:")
                print(f"  Trial: {matching_results.get('trial_info', {}).get('title', 'Unknown')}")
                print(f"  Total patients found: {summary.get('total_patients_found', 0)}")
                print(f"  Patients evaluated: {summary.get('patients_evaluated', 0)}")
                print(f"  Eligible patients: {summary.get('eligible_patients', 0)}")
                print(f"  Average confidence: {summary.get('average_confidence', 0):.1f}%")
            
            return pipeline_results
            
        except Exception as e:
            print(f"❌ Pipeline failed with error: {e}")
            pipeline_results["pipeline_failed_at"] = datetime.now().isoformat()
            pipeline_results["overall_status"] = "failed"
            pipeline_results["error"] = str(e)
            return pipeline_results

    def run_individual_step(self, step: str, **kwargs) -> Dict[str, Any]:
        """Run individual pipeline steps"""
        if step == "embeddings":
            return self.run_embedding_generation()
        elif step == "matching":
            return self.run_trial_patient_matching(
                kwargs.get('trial_id'),
                kwargs.get('age_range'),
                kwargs.get('gender')
            )
        else:
            print(f"Unknown step: {step}")
            return {}

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Trial-to-Patient Matching Pipeline")
    
    # Pipeline options
    parser.add_argument("--trial-id", required=True, help="Trial ID to find patients for")
    parser.add_argument("--age-min", type=int, help="Minimum age filter")
    parser.add_argument("--age-max", type=int, help="Maximum age filter")
    parser.add_argument("--gender", choices=['Male', 'Female'], help="Gender filter")
    
    # Individual step options
    parser.add_argument("--step", choices=['embeddings', 'matching'], 
                       help="Run only a specific step")
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = TrialToPatientOrchestrator()
    
    # Prepare age range
    age_range = None
    if args.age_min and args.age_max:
        age_range = (args.age_min, args.age_max)
    
    # Run pipeline or individual step
    if args.step:
        print(f"Running individual step: {args.step}")
        results = orchestrator.run_individual_step(
            args.step,
            trial_id=args.trial_id,
            age_range=age_range,
            gender=args.gender
        )
    else:
        print("Running complete trial-to-patient pipeline")
        results = orchestrator.run_complete_pipeline(
            trial_id=args.trial_id,
            age_range=age_range,
            gender=args.gender
        )
    
    if results:
        print("\n✅ Operation completed successfully!")
    else:
        print("\n❌ Operation failed!")

if __name__ == "__main__":
    main()
