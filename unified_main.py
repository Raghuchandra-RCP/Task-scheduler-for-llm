"""
Main Entry Point for Unified Bidirectional Clinical Trial Matching System

This module provides the main interface for running unified bidirectional evaluations.
It can be used as a standalone script or imported as a module.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipelines.unified_bidirectional_pipeline import UnifiedBidirectionalPipeline
from services.unified_matching.json_data_persistence import JSONDataPersistence
import config


class UnifiedMatchingSystem:
    """
    Main interface for the Unified Bidirectional Clinical Trial Matching System.
    
    This class provides high-level methods to run evaluations and manage the system.
    """
    
    def __init__(self):
        """Initialize the unified matching system."""
        self.pipeline = UnifiedBidirectionalPipeline()
        self.persistence = JSONDataPersistence(config.JSON_DATA_DIR)
        
        logger.info("Unified Matching System initialized successfully")
    
    def setup_sample_data(self) -> Dict[str, Any]:
        """
        Set up sample data for testing and demonstration.
        
        Returns:
            Dictionary containing setup results
        """
        logger.info("Setting up sample data...")
        
        try:
            result = self.persistence.create_sample_data()
            
            if result["success"]:
                logger.info(f"Sample data created successfully:")
                logger.info(f"  - {result['sample_patients_created']} patients")
                logger.info(f"  - {result['sample_trials_created']} trials")
                logger.info(f"  - Patient IDs: {result['patient_ids']}")
                logger.info(f"  - Trial IDs: {result['trial_ids']}")
            else:
                logger.error(f"Failed to create sample data: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting up sample data: {e}")
            return {"success": False, "error": str(e)}
    
    def run_patient_evaluation(self, patient_id: int, trial_ids: List[str] = None,
                             max_trials: int = 10, save_results: bool = True) -> Dict[str, Any]:
        """
        Run unified bidirectional evaluation for a patient.
        
        Args:
            patient_id: ID of the patient to evaluate
            trial_ids: List of specific trial IDs to evaluate (optional)
            max_trials: Maximum number of trials to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing evaluation results
        """
        logger.info(f"Running patient evaluation for patient {patient_id}")
        
        try:
            # First check if patient exists
            patient_data = self.persistence.load_patient_data(patient_id)
            if not patient_data:
                logger.warning(f"Patient {patient_id} not found in JSON data, trying database...")
                # Try to get from database
                try:
                    from services.shared.database_utils import DatabaseUtils
                    db_utils = DatabaseUtils()
                    patient_data = db_utils.get_patient_by_id(patient_id)
                    if patient_data:
                        logger.info(f"Found patient {patient_id} in database")
                    else:
                        logger.error(f"Patient {patient_id} not found in database either")
                        return {"error": f"Patient {patient_id} not found", "success": False}
                except Exception as db_error:
                    logger.error(f"Database error: {db_error}")
                    return {"error": f"Patient {patient_id} not found and database error: {db_error}", "success": False}
            
            result = self.pipeline.run_patient_evaluation(
                patient_id=patient_id,
                trial_ids=trial_ids,
                max_trials=max_trials,
                save_results=save_results
            )
            
            if "error" in result:
                logger.error(f"Patient evaluation failed: {result['error']}")
            else:
                logger.info(f"Patient evaluation completed successfully")
                logger.info(f"  - Evaluated {len(result.get('bidirectional_results', []))} trials")
                logger.info(f"  - Average compatibility: {result.get('summary', {}).get('average_compatibility_score', 'N/A')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in patient evaluation: {e}")
            return {"error": str(e), "success": False}
    
    def run_trial_evaluation(self, trial_id: str, patient_ids: List[int] = None,
                           max_patients: int = 10, save_results: bool = True) -> Dict[str, Any]:
        """
        Run unified bidirectional evaluation for a trial.
        
        Args:
            trial_id: ID of the trial to evaluate
            patient_ids: List of specific patient IDs to evaluate (optional)
            max_patients: Maximum number of patients to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing evaluation results
        """
        logger.info(f"Running trial evaluation for trial {trial_id}")
        
        try:
            result = self.pipeline.run_trial_evaluation(
                trial_id=trial_id,
                patient_ids=patient_ids,
                max_patients=max_patients,
                save_results=save_results
            )
            
            if "error" in result:
                logger.error(f"Trial evaluation failed: {result['error']}")
            else:
                logger.info(f"Trial evaluation completed successfully")
                logger.info(f"  - Evaluated {len(result.get('bidirectional_results', []))} patients")
                logger.info(f"  - Average compatibility: {result.get('summary', {}).get('average_compatibility_score', 'N/A')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trial evaluation: {e}")
            return {"error": str(e), "success": False}
    
    def run_batch_evaluation(self, patient_ids: List[int], trial_ids: List[str],
                           save_results: bool = True) -> Dict[str, Any]:
        """
        Run batch bidirectional evaluation.
        
        Args:
            patient_ids: List of patient IDs to evaluate
            trial_ids: List of trial IDs to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing batch evaluation results
        """
        logger.info(f"Running batch evaluation for {len(patient_ids)} patients and {len(trial_ids)} trials")
        
        try:
            result = self.pipeline.run_batch_evaluation(
                patient_ids=patient_ids,
                trial_ids=trial_ids,
                save_results=save_results
            )
            
            if "error" in result:
                logger.error(f"Batch evaluation failed: {result['error']}")
            else:
                logger.info(f"Batch evaluation completed successfully")
                logger.info(f"  - Total evaluations: {len(result.get('evaluations', []))}")
                logger.info(f"  - Average compatibility: {result.get('summary', {}).get('average_compatibility', 'N/A')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in batch evaluation: {e}")
            return {"error": str(e), "success": False}
    
    def run_comprehensive_evaluation(self, patient_ids: List[int], trial_ids: List[str],
                                   save_results: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive evaluation combining all approaches.
        
        Args:
            patient_ids: List of patient IDs to evaluate
            trial_ids: List of trial IDs to evaluate
            save_results: Whether to save results to JSON file
            
        Returns:
            Dictionary containing comprehensive evaluation results
        """
        logger.info(f"Running comprehensive evaluation for {len(patient_ids)} patients and {len(trial_ids)} trials")
        
        try:
            result = self.pipeline.run_comprehensive_evaluation(
                patient_ids=patient_ids,
                trial_ids=trial_ids,
                save_results=save_results
            )
            
            if "error" in result:
                logger.error(f"Comprehensive evaluation failed: {result['error']}")
            else:
                logger.info(f"Comprehensive evaluation completed successfully")
                logger.info(f"  - Patient evaluations: {len(result.get('patient_evaluations', []))}")
                logger.info(f"  - Trial evaluations: {len(result.get('trial_evaluations', []))}")
                logger.info(f"  - Batch evaluation: {'completed' if result.get('batch_evaluation') else 'not completed'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            return {"error": str(e), "success": False}
    
    def get_available_data(self) -> Dict[str, Any]:
        """
        Get information about available data.
        
        Returns:
            Dictionary containing available data information
        """
        try:
            patient_ids = self.persistence.get_patient_ids()
            trial_ids = self.persistence.get_trial_ids()
            
            return {
                "patients": {
                    "count": len(patient_ids),
                    "ids": patient_ids
                },
                "trials": {
                    "count": len(trial_ids),
                    "ids": trial_ids
                },
                "total_combinations": len(patient_ids) * len(trial_ids)
            }
            
        except Exception as e:
            logger.error(f"Error getting available data: {e}")
            return {"error": str(e)}
    
    def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Clean up old files.
        
        Args:
            days_old: Number of days old files should be to be deleted
            
        Returns:
            Dictionary containing cleanup results
        """
        logger.info(f"Cleaning up files older than {days_old} days...")
        
        try:
            cleanup_stats = self.persistence.cleanup_old_files(days_old)
            
            total_deleted = sum(cleanup_stats.values())
            logger.info(f"Cleanup completed: {total_deleted} files deleted")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
    
    def print_evaluation_summary(self, result: Dict[str, Any]) -> None:
        """
        Print a formatted summary of evaluation results.
        
        Args:
            result: Evaluation result dictionary
        """
        try:
            if "error" in result:
                print(f"Evaluation failed: {result['error']}")
                return
            
            print("\n" + "="*80)
            print("UNIFIED BIDIRECTIONAL EVALUATION RESULTS")
            print("="*80)
            
            # Print basic info
            if "patient_info" in result:
                patient_info = result["patient_info"]
                print(f"Patient: {patient_info.get('mrn', 'Unknown')} (ID: {patient_info.get('patient_id', 'Unknown')})")
                print(f"   Age: {patient_info.get('age', 'Unknown')}, Gender: {patient_info.get('gender', 'Unknown')}")
                print(f"   Condition: {patient_info.get('condition', 'Unknown')}")
            
            if "trial_info" in result:
                trial_info = result["trial_info"]
                print(f"🧪 Trial: {trial_info.get('trial_id', 'Unknown')}")
                print(f"   Title: {trial_info.get('title', 'Unknown')}")
                print(f"   Phase: {trial_info.get('phase', 'Unknown')}, Status: {trial_info.get('status', 'Unknown')}")
            
            # Print bidirectional results
            bidirectional_results = result.get("bidirectional_results", [])
            if bidirectional_results:
                print(f"\nEVALUATION RESULTS ({len(bidirectional_results)} items):")
                print("-" * 80)
                
                for i, eval_result in enumerate(bidirectional_results, 1):
                    if "trial_info" in eval_result:
                        trial_info = eval_result["trial_info"]
                        print(f"\n{i}. Trial: {trial_info.get('trial_id', 'Unknown')}")
                        print(f"   Title: {trial_info.get('title', 'Unknown')}")
                    
                    if "patient_info" in eval_result:
                        patient_info = eval_result["patient_info"]
                        print(f"\n{i}. Patient: {patient_info.get('mrn', 'Unknown')} (ID: {patient_info.get('patient_id', 'Unknown')})")
                        print(f"   Age: {patient_info.get('age', 'Unknown')}, Gender: {patient_info.get('gender', 'Unknown')}")
                    
                    # Patient-to-Trial evaluation
                    p2t_eval = eval_result.get("patient_to_trial_evaluation", {})
                    print(f"   Patient -> Trial:")
                    print(f"      Status: {p2t_eval.get('eligibility_status', 'Unknown')}")
                    print(f"      Confidence: {p2t_eval.get('confidence_score', 0)}%")
                    print(f"      Next Steps: {p2t_eval.get('next_steps', 'None')}")
                    
                    # Trial-to-Patient evaluation
                    t2p_eval = eval_result.get("trial_to_patient_evaluation", {})
                    print(f"   Trial -> Patient:")
                    print(f"      Status: {t2p_eval.get('suitability_status', 'Unknown')}")
                    print(f"      Priority: {t2p_eval.get('priority_score', 0)}%")
                    print(f"      Recommendation: {t2p_eval.get('enrollment_recommendation', 'Unknown')}")
                    
                    # Overall compatibility
                    compatibility = eval_result.get("overall_compatibility", {})
                    print(f"   Overall Compatibility:")
                    print(f"      Match Quality: {compatibility.get('match_quality', 'Unknown')}")
                    print(f"      Combined Score: {compatibility.get('combined_score', 0)}%")
                    print(f"      Final Recommendation: {compatibility.get('final_recommendation', 'Unknown')}")
                    print(f"      Enrollment Probability: {compatibility.get('enrollment_probability', 'Unknown')}")
            
            # Print summary
            summary = result.get("summary", {})
            if summary:
                print(f"\nSUMMARY:")
                print("-" * 40)
                print(f"Total Evaluations: {summary.get('total_trials_evaluated', summary.get('total_patients_evaluated', 0))}")
                print(f"Eligible Matches: {summary.get('eligible_trials', summary.get('eligible_patients', 0))}")
                print(f"Suitable Matches: {summary.get('suitable_trials', summary.get('suitable_patients', 0))}")
                print(f"Average Compatibility: {summary.get('average_compatibility_score', 'N/A')}%")
                print(f"Success Rate: {summary.get('success_rate', 'N/A')}%")
            
            # Print action items
            summary_report = result.get("summary_report", {})
            if summary_report and "action_items" in summary_report:
                action_items = summary_report["action_items"]
                if action_items:
                    print(f"\nACTION ITEMS:")
                    print("-" * 40)
                    for item in action_items:
                        print(f"   • {item}")
            
            print("\n" + "="*80)
            
        except Exception as e:
            logger.error(f"Error printing evaluation summary: {e}")
            print(f"Error printing summary: {e}")


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Unified Bidirectional Clinical Trial Matching System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set up sample data
  python unified_main.py --setup-sample-data
  
  # Evaluate a patient against all trials
  python unified_main.py --patient-evaluation 1
  
  # Evaluate a patient against specific trials
  python unified_main.py --patient-evaluation 1 --trial-ids NCT04929223 NCT05123456
  
  # Evaluate a trial against all patients
  python unified_main.py --trial-evaluation NCT04929223
  
  # Run batch evaluation
  python unified_main.py --batch-evaluation --patient-ids 1 2 3 --trial-ids NCT04929223 NCT05123456
  
  # Run comprehensive evaluation
  python unified_main.py --comprehensive-evaluation --patient-ids 1 2 3 --trial-ids NCT04929223 NCT05123456
  
  # Get available data
  python unified_main.py --list-data
  
  # Clean up old files
  python unified_main.py --cleanup --days 30
        """
    )
    
    # Main commands
    parser.add_argument("--setup-sample-data", action="store_true",
                       help="Set up sample data for testing")
    parser.add_argument("--patient-evaluation", type=int, metavar="PATIENT_ID",
                       help="Run patient evaluation for specified patient ID")
    parser.add_argument("--trial-evaluation", type=str, metavar="TRIAL_ID",
                       help="Run trial evaluation for specified trial ID")
    parser.add_argument("--batch-evaluation", action="store_true",
                       help="Run batch evaluation")
    parser.add_argument("--comprehensive-evaluation", action="store_true",
                       help="Run comprehensive evaluation")
    parser.add_argument("--list-data", action="store_true",
                       help="List available data")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up old files")
    
    # Options
    parser.add_argument("--patient-ids", nargs="+", type=int, metavar="ID",
                       help="List of patient IDs for batch/comprehensive evaluation")
    parser.add_argument("--trial-ids", nargs="+", type=str, metavar="ID",
                       help="List of trial IDs for evaluation")
    parser.add_argument("--max-trials", type=int, default=10,
                       help="Maximum number of trials to evaluate (default: 10)")
    parser.add_argument("--max-patients", type=int, default=10,
                       help="Maximum number of patients to evaluate (default: 10)")
    parser.add_argument("--days", type=int, default=30,
                       help="Days old for cleanup (default: 30)")
    parser.add_argument("--no-save", action="store_true",
                       help="Don't save results to files")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    # Initialize system
    try:
        system = UnifiedMatchingSystem()
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        sys.exit(1)
    
    # Execute commands
    try:
        if args.setup_sample_data:
            result = system.setup_sample_data()
            if result["success"]:
                print("Sample data set up successfully!")
                print(f"   Patients: {result['sample_patients_created']}")
                print(f"   Trials: {result['sample_trials_created']}")
            else:
                print(f"Failed to set up sample data: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        
        elif args.patient_evaluation:
            result = system.run_patient_evaluation(
                patient_id=args.patient_evaluation,
                trial_ids=args.trial_ids,
                max_trials=args.max_trials,
                save_results=not args.no_save
            )
            system.print_evaluation_summary(result)
        
        elif args.trial_evaluation:
            result = system.run_trial_evaluation(
                trial_id=args.trial_evaluation,
                patient_ids=args.patient_ids,
                max_patients=args.max_patients,
                save_results=not args.no_save
            )
            system.print_evaluation_summary(result)
        
        elif args.batch_evaluation:
            if not args.patient_ids or not args.trial_ids:
                print("Batch evaluation requires --patient-ids and --trial-ids")
                sys.exit(1)
            
            result = system.run_batch_evaluation(
                patient_ids=args.patient_ids,
                trial_ids=args.trial_ids,
                save_results=not args.no_save
            )
            system.print_evaluation_summary(result)
        
        elif args.comprehensive_evaluation:
            if not args.patient_ids or not args.trial_ids:
                print("Comprehensive evaluation requires --patient-ids and --trial-ids")
                sys.exit(1)
            
            result = system.run_comprehensive_evaluation(
                patient_ids=args.patient_ids,
                trial_ids=args.trial_ids,
                save_results=not args.no_save
            )
            system.print_evaluation_summary(result)
        
        elif args.list_data:
            data_info = system.get_available_data()
            if "error" in data_info:
                print(f"Error getting data info: {data_info['error']}")
            else:
                print("Available Data:")
                print(f"   Patients: {data_info['patients']['count']} ({data_info['patients']['ids']})")
                print(f"   Trials: {data_info['trials']['count']} ({data_info['trials']['ids']})")
                print(f"   Total Combinations: {data_info['total_combinations']}")
        
        elif args.cleanup:
            cleanup_stats = system.cleanup_old_files(args.days)
            if "error" in cleanup_stats:
                print(f"Cleanup failed: {cleanup_stats['error']}")
            else:
                total_deleted = sum(cleanup_stats.values())
                print(f"Cleanup completed: {total_deleted} files deleted")
                print(f"   Patients: {cleanup_stats['patients_deleted']}")
                print(f"   Trials: {cleanup_stats['trials_deleted']}")
                print(f"   Evaluations: {cleanup_stats['evaluations_deleted']}")
                print(f"   Results: {cleanup_stats['results_deleted']}")
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
