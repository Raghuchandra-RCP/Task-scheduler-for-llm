"""
Patient-to-Trial Keyword Generator
Generates keywords from patient medical records for finding suitable clinical trials
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from services.shared.database_utils import DatabaseUtils, safe_json_dump
from services.shared.llm_utils import LLMUtils

class PatientKeywordGenerator:
    def __init__(self):
        self.db_utils = DatabaseUtils()
        self.llm_utils = LLMUtils()
        
        # Create results directory structure
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Create keyword generation subdirectory
        self.keyword_dir = self.results_dir / "keyword_generation"
        self.keyword_dir.mkdir(exist_ok=True)

    def check_existing_keywords(self, patient_id: int) -> bool:
        """Check if keywords already exist for a patient"""
        keyword_file = self.keyword_dir / f"patient_{patient_id}_keywords.json"
        return keyword_file.exists()

    def load_existing_keywords(self, patient_id: int) -> Dict[str, Any]:
        """Load existing keywords for a patient"""
        keyword_file = self.keyword_dir / f"patient_{patient_id}_keywords.json"
        try:
            with open(keyword_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading existing keywords for patient {patient_id}: {e}")
            return {}

    def save_keywords(self, keywords_data: Dict[str, Any]) -> str:
        """Save keywords to file"""
        patient_id = keywords_data.get('patient_id', 'unknown')
        keyword_file = self.keyword_dir / f"patient_{patient_id}_keywords.json"
        
        safe_json_dump(keywords_data, keyword_file, indent=2, ensure_ascii=False)
        return str(keyword_file)

    def generate_keywords_for_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate keywords for a single patient using LLM (only if not already exists)"""
        patient_id = patient_data['patient_id']
        
        # Check if keywords already exist
        if self.check_existing_keywords(patient_id):
            print(f"✅ Patient {patient_id} (MRN: {patient_data['mrn']}) already has keywords - loading existing")
            return self.load_existing_keywords(patient_id)
        
        try:
            print(f"🆕 Generating NEW keywords for patient MRN: {patient_data['mrn']}")
            
            keywords_data = self.llm_utils.generate_keywords_for_patient(patient_data)
            
            if "error" in keywords_data:
                print(f"Failed to generate keywords for patient {patient_id}")
                return {
                    "patient_id": patient_id,
                    "error": keywords_data["error"],
                    "raw_response": keywords_data.get("raw_response", "")
                }
            
            # Save the generated keywords
            self.save_keywords(keywords_data)
            print(f"💾 Keywords saved for patient {patient_id}")
            
            return keywords_data
                
        except Exception as e:
            print(f"Error generating keywords for patient {patient_id}: {e}")
            return {
                "patient_id": patient_id,
                "error": str(e)
            }

    def generate_keywords_batch(self, patients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate keywords for multiple patients in one batch (only new patients)"""
        results = {
            "successful": {},
            "failed": {},
            "skipped": {},
            "metadata": {
                "total_patients": len(patients),
                "generated_at": datetime.now().isoformat(),
                "model": "gemini-2.0-flash-exp",
                "matching_direction": "patient_to_trial",
                "batch_processing": "optimized_new_patients_only"
            }
        }
        
        # Separate new patients from existing ones
        new_patients = []
        existing_patients = []
        
        for patient in patients:
            patient_id = patient['patient_id']
            if self.check_existing_keywords(patient_id):
                existing_patients.append(patient)
                # Load existing keywords
                existing_keywords = self.load_existing_keywords(patient_id)
                results["skipped"][patient_id] = existing_keywords
            else:
                new_patients.append(patient)
        
        print(f"📊 Keyword Generation Summary:")
        print(f"   Total patients: {len(patients)}")
        print(f"   Existing patients (skipped): {len(existing_patients)}")
        print(f"   New patients (to process): {len(new_patients)}")
        
        if not new_patients:
            print("🎉 All patients already have keywords - no new generation needed!")
            results["metadata"]["batch_status"] = "all_existing"
            return results
        
        print(f"🆕 Generating keywords for {len(new_patients)} NEW patients...")
        
        # Process only new patients
        try:
            batch_keywords_data = self.llm_utils.generate_keywords_for_patient_batch(new_patients)
            
            if "error" in batch_keywords_data:
                print(f"❌ Batch processing failed: {batch_keywords_data['error']}")
                print("🔄 Falling back to individual patient processing...")
                
                # Fallback to individual processing
                individual_results = self._process_patients_individually(new_patients)
                results["successful"] = individual_results.get("successful", {})
                results["failed"] = individual_results.get("failed", {})
                results["metadata"]["batch_status"] = "fallback_individual"
                results["metadata"]["fallback_reason"] = batch_keywords_data["error"]
            else:
                # Process successful results
                for patient_id, keywords_data in batch_keywords_data.get("successful", {}).items():
                    results["successful"][patient_id] = keywords_data
                    # Save the keywords
                    self.save_keywords(keywords_data)
                
                # Process failed results
                for patient_id, error_data in batch_keywords_data.get("failed", {}).items():
                    results["failed"][patient_id] = error_data
                
                results["metadata"]["batch_status"] = "success"
            
            print(f"✅ Processing completed:")
            print(f"   Successful: {len(results['successful'])}")
            print(f"   Failed: {len(results['failed'])}")
            print(f"   Skipped: {len(results['skipped'])}")
                
        except Exception as e:
            print(f"Error in batch processing: {e}")
            results["metadata"]["batch_status"] = "error"
            results["metadata"]["error"] = str(e)
            for patient in new_patients:
                results["failed"][patient['patient_id']] = {
                    "error": str(e)
                }
        
        return results

    def _process_patients_individually(self, patients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process patients individually as fallback when batch processing fails"""
        print(f"🔄 Processing {len(patients)} patients individually...")
        
        results = {
            "successful": {},
            "failed": {}
        }
        
        for i, patient in enumerate(patients):
            patient_id = patient['patient_id']
            print(f"Processing patient {i+1}/{len(patients)}: MRN {patient['mrn']}")
            
            try:
                keywords_data = self.generate_keywords_for_patient(patient)
                
                if "error" in keywords_data:
                    results["failed"][patient_id] = keywords_data
                    print(f"❌ Failed to generate keywords for patient {patient_id}")
                else:
                    results["successful"][patient_id] = keywords_data
                    print(f"✅ Generated keywords for patient {patient_id}")
                    
            except Exception as e:
                results["failed"][patient_id] = {
                    "patient_id": patient_id,
                    "error": str(e)
                }
                print(f"❌ Error processing patient {patient_id}: {e}")
        
        print(f"Individual processing completed:")
        print(f"   Successful: {len(results['successful'])}")
        print(f"   Failed: {len(results['failed'])}")
        
        return results

    def _load_existing_keywords(self) -> Dict[str, Any]:
        """Load existing keywords from the most recent file"""
        try:
            # Find the most recent keywords file
            keyword_files = list(self.results_dir.glob("patient_keywords_*.json"))
            if not keyword_files:
                return {}
            
            # Sort by modification time (most recent first)
            latest_file = max(keyword_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get('successful', {})
        except Exception as e:
            print(f"Error loading existing keywords: {e}")
            return {}

    def save_keywords_to_file(self, results: Dict[str, Any]) -> str:
        """Save keyword generation results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patient_keywords_{timestamp}.json"
        filepath = self.keyword_dir / filename
        
        safe_json_dump(results, filepath, indent=2, ensure_ascii=False)
        
        print(f"Keywords saved to: {filepath}")
        return str(filepath)

    def run_keyword_generation(self, limit: int = 50) -> Dict[str, Any]:
        """Main method to run keyword generation process - OPTIMIZED for existing patients"""
        print("Starting patient keyword generation for trial matching...")
        
        # Get patient data
        patients = self.db_utils.get_patient_data_for_keywords(limit)
        if not patients:
            print("No patient data found!")
            return {}
        
        print(f"Found {len(patients)} patients")
        
        # Check which patients already have keywords
        existing_keywords = self._load_existing_keywords()
        new_patients = []
        
        for patient in patients:
            patient_id = str(patient['patient_id'])
            if patient_id not in existing_keywords:
                new_patients.append(patient)
            else:
                print(f"✅ Patient {patient_id} (MRN: {patient['mrn']}) already has keywords - skipping")
        
        if not new_patients:
            print("🎉 All patients already have keywords - no new generation needed!")
            return {
                "successful": existing_keywords,
                "failed": {},
                "metadata": {
                    "total_patients": len(patients),
                    "new_patients": 0,
                    "existing_patients": len(patients),
                    "generated_at": datetime.now().isoformat(),
                    "note": "All patients already had keywords"
                }
            }
        
        print(f"🆕 Found {len(new_patients)} NEW patients needing keyword generation")
        
        # Generate keywords only for new patients
        print("Generating keywords for NEW patients only...")
        results = self.generate_keywords_batch(new_patients)
        
        # Merge with existing keywords
        all_keywords = existing_keywords.copy()
        all_keywords.update(results.get('successful', {}))
        
        # Update results with combined data
        results["successful"] = all_keywords
        results["metadata"]["total_patients"] = len(patients)
        results["metadata"]["new_patients"] = len(new_patients)
        results["metadata"]["existing_patients"] = len(patients) - len(new_patients)
        results["metadata"]["note"] = f"Generated keywords for {len(new_patients)} new patients"
        
        # Save results
        filepath = self.save_keywords_to_file(results)
        
        # Print summary
        successful_count = len(results["successful"])
        failed_count = len(results["failed"])
        
        print(f"\nPatient Keyword Generation Summary:")
        print(f"Total patients: {len(patients)}")
        print(f"New patients processed: {len(new_patients)}")
        print(f"Existing patients skipped: {len(patients) - len(new_patients)}")
        print(f"Total successful: {successful_count}")
        print(f"Failed: {failed_count}")
        print(f"Results saved to: {filepath}")
        
        return results

def main():
    """Main function to run patient keyword generation"""
    generator = PatientKeywordGenerator()
    results = generator.run_keyword_generation(limit=50)
    
    if results:
        print("\nPatient keyword generation completed successfully!")
    else:
        print("\nPatient keyword generation failed!")

if __name__ == "__main__":
    main()
