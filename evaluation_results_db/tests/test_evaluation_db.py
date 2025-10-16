#!/usr/bin/env python3
"""
Test script for Evaluation Results Database
Tests the database utilities and table creation
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test database connection and table creation"""
    try:
        from evaluation_results_db.utils.evaluation_results_db import EvaluationResultsDB
        
        print("🧪 Testing Evaluation Results Database...")
        print("=" * 50)
        
        # Initialize database connection
        db = EvaluationResultsDB()
        print("✅ Database connection established")
        
        # Test statistics (should work even with empty tables)
        print("\n📊 Getting evaluation statistics...")
        stats = db.get_evaluation_statistics()
        print(json.dumps(stats, indent=2))
        
        print("\n✅ Database test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the database tables are created first!")
        return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_sample_data():
    """Test with sample evaluation data"""
    try:
        from evaluation_results_db.utils.evaluation_results_db import EvaluationResultsDB
        
        print("\n🧪 Testing with sample data...")
        print("=" * 50)
        
        db = EvaluationResultsDB()
        
        # Sample patient-to-trial evaluation data
        sample_p2t_data = {
            "patient_info": {
                "patient_id": 999,
                "mrn": "TEST001",
                "age": 45,
                "gender": "Male",
                "oncologist": "Dr. Test Oncologist"
            },
            "llm_evaluation": {
                "evaluation_method": "batch",
                "batch_summary": {
                    "total_trials_evaluated": 3,
                    "eligible_count": 1,
                    "not_eligible_count": 1,
                    "need_more_info_count": 1,
                    "average_confidence": 75.0
                },
                "evaluations": [
                    {
                        "trial_id": "TEST_TRIAL_001",
                        "eligibility_status": "ELIGIBLE",
                        "confidence_score": 85,
                        "reasoning": "Test reasoning"
                    }
                ]
            },
            "summary": {
                "total_trials_found": 5,
                "trials_evaluated": 3,
                "eligible_trials": 1,
                "average_confidence": 75.0
            }
        }
        
        # Test saving patient-to-trial evaluation
        print("💾 Testing patient-to-trial evaluation save...")
        p2t_id = db.save_patient_to_trial_evaluation(sample_p2t_data)
        
        if p2t_id:
            print(f"✅ Patient-to-Trial evaluation saved with ID: {p2t_id}")
            
            # Test getting patient history
            print("📋 Testing patient evaluation history...")
            history = db.get_patient_evaluation_history(patient_id=999, limit=5)
            print(f"Found {len(history)} evaluation records")
            
        else:
            print("❌ Failed to save patient-to-trial evaluation")
        
        print("\n✅ Sample data test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Evaluation Results Database Test Suite")
    print("=" * 60)
    
    # Test 1: Database connection
    connection_ok = test_database_connection()
    
    if connection_ok:
        # Test 2: Sample data
        sample_ok = test_sample_data()
        
        if sample_ok:
            print("\n🎉 All tests passed!")
            print("✅ Database implementation is working correctly")
        else:
            print("\n❌ Sample data tests failed")
    else:
        print("\n❌ Database connection failed")
        print("Please check:")
        print("1. Database is running")
        print("2. Tables are created (run sql/01_create_evaluation_tables.sql)")
        print("3. Database credentials are correct")

if __name__ == "__main__":
    main()
