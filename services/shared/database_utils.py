"""
Shared Database Utilities
Common database operations and stored procedures for both patient-to-trial and trial-to-patient matching
"""

import json
import numpy as np
from sqlalchemy import create_engine, text
from config import DATABASE_URL
from typing import List, Dict, Any, Optional

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def safe_json_dump(data, file_path, **kwargs):
    """Safely dump data to JSON file handling numpy types"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=JSONEncoder, **kwargs)

class DatabaseUtils:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
    
    def get_connection(self):
        """Get database connection"""
        return self.engine.connect()
    
    def get_patient_data_for_keywords(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get patient data from database using stored procedure"""
        try:
            with self.get_connection() as connection:
                query = text("SELECT * FROM insightsedge.get_patient_data_for_keywords(:limit)")
                result = connection.execute(query, {"limit": limit})
                
                patients = []
                for row in result:
                    patients.append({
                        "patient_id": row[0],
                        "mrn": row[1],
                        "age": row[2],
                        "gender": row[3],
                        "combined_text": row[4],
                        "oncologist": row[5],
                        "date_of_visit": row[6].isoformat() if row[6] else None,
                        "created_at": row[7].isoformat() if row[7] else None
                    })
                
                return patients
        except Exception as e:
            print(f"Error getting patient data: {e}")
            return []
    
    def get_trial_data_for_embeddings(self) -> List[Dict[str, Any]]:
        """Get clinical trial data from database"""
        try:
            with self.get_connection() as connection:
                query = text("SELECT * FROM insightsedge.get_trial_data_for_embeddings()")
                result = connection.execute(query)
                
                trials = []
                for row in result:
                    trials.append({
                        "trial_id": row[0],
                        "title": row[1],
                        "condition": row[2],
                        "phase": row[3],
                        "status": row[4],
                        "investigator": row[5],
                        "created_date": row[6],
                        "patients_matched": row[7],
                        "matching_status": row[8]
                    })
                
                return trials
        except Exception as e:
            print(f"Error getting trial data: {e}")
            return []
    
    def get_detailed_trial_data(self) -> List[Dict[str, Any]]:
        """Get detailed clinical trial information"""
        try:
            with self.get_connection() as connection:
                # Use direct query instead of stored procedure to avoid data type issues
                query = text("""
                    SELECT 
                        ctd.nct_id::TEXT as trial_id,
                        ctd.study_title::TEXT as title,
                        ctd.conditions::TEXT as condition,
                        ctd.study_phase::TEXT as phase,
                        ctd.overall_status::TEXT as status,
                        ctd.lead_sponsor_name::TEXT as investigator,
                        ctd.start_date::TEXT as created_date,
                        0 as patients_matched,
                        'pending'::TEXT as matching_status,
                        CONCAT(
                            'Trial ID: ', ctd.nct_id, E'\n',
                            'Title: ', ctd.study_title, E'\n',
                            'Condition: ', ctd.conditions, E'\n',
                            'Phase: ', ctd.study_phase, E'\n',
                            'Status: ', ctd.overall_status, E'\n',
                            'Investigator: ', ctd.lead_sponsor_name, E'\n',
                            'Start Date: ', ctd.start_date::TEXT, E'\n',
                            'Age Range: ', COALESCE(ctd.minimum_age, 'Not specified'), ' - ', COALESCE(ctd.maximum_age, 'Not specified'), E'\n',
                            'Gender: ', COALESCE(ctd.sex, 'Not specified'), E'\n\n',
                            'Brief Summary: ', COALESCE(ctd.brief_summary, 'Not available'), E'\n\n',
                            'Detailed Description: ', COALESCE(ctd.detailed_description, 'Not available'), E'\n\n',
                            'Inclusion Criteria: ', COALESCE(ctd.inclusion_criteria, 'Not available'), E'\n\n',
                            'Exclusion Criteria: ', COALESCE(ctd.exclusion_criteria, 'Not available'), E'\n\n',
                            'Eligibility Criteria: ', COALESCE(ctd.eligibility_criteria, 'Not available')
                        ) as combined_trial_text
                    FROM insightsedge.clinical_trial_details ctd
                    WHERE ctd.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION', 'AVAILABLE')
                    ORDER BY ctd.created_at DESC
                    LIMIT 100
                """)
                result = connection.execute(query)
                
                trials = []
                for row in result:
                    trials.append({
                        "trial_id": str(row[0]),
                        "title": str(row[1]),
                        "condition": str(row[2]),
                        "phase": str(row[3]),
                        "status": str(row[4]),
                        "investigator": str(row[5]),
                        "created_date": str(row[6]),
                        "patients_matched": int(row[7]),
                        "matching_status": str(row[8]),
                        "combined_trial_text": str(row[9])
                    })
                
                print(f"Successfully retrieved {len(trials)} trials from database")
                return trials
        except Exception as e:
            print(f"Error getting detailed trial data: {e}")
            print("Returning empty list to continue processing")
            return []
    
    def get_patient_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get specific patient by ID"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    SELECT * FROM insightsedge.get_patient_data_for_keywords(1000)
                    WHERE patient_id = :patient_id
                """)
                result = connection.execute(query, {"patient_id": patient_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "patient_id": row[0],
                        "mrn": row[1],
                        "age": row[2],
                        "gender": row[3],
                        "combined_text": row[4],
                        "oncologist": row[5],
                        "date_of_visit": row[6].isoformat() if row[6] else None,
                        "created_at": row[7].isoformat() if row[7] else None
                    }
                return None
        except Exception as e:
            print(f"Error getting patient by ID: {e}")
            return None

    def get_patient_by_mrn(self, mrn: str) -> Optional[Dict[str, Any]]:
        """Get specific patient by MRN"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    SELECT * FROM insightsedge.get_patient_data_for_keywords(1000)
                    WHERE mrn = :mrn
                """)
                result = connection.execute(query, {"mrn": mrn})
                row = result.fetchone()
                
                if row:
                    return {
                        "patient_id": row[0],
                        "mrn": row[1],
                        "age": row[2],
                        "gender": row[3],
                        "combined_text": row[4],
                        "oncologist": row[5],
                        "date_of_visit": row[6].isoformat() if row[6] else None,
                        "created_at": row[7].isoformat() if row[7] else None
                    }
                return None
        except Exception as e:
            print(f"Error getting patient by MRN: {e}")
            return None
    
    def get_trial_by_id(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """Get specific trial by ID"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    SELECT 
                        ctd.nct_id::TEXT as trial_id,
                        ctd.study_title::TEXT as title,
                        ctd.conditions::TEXT as condition,
                        ctd.study_phase::TEXT as phase,
                        ctd.overall_status::TEXT as status,
                        ctd.lead_sponsor_name::TEXT as investigator,
                        ctd.start_date::TEXT as created_date,
                        0 as patients_matched,
                        'pending'::TEXT as matching_status,
                        CONCAT(
                            'Trial ID: ', ctd.nct_id, E'\n',
                            'Title: ', ctd.study_title, E'\n',
                            'Condition: ', ctd.conditions, E'\n',
                            'Phase: ', ctd.study_phase, E'\n',
                            'Status: ', ctd.overall_status, E'\n',
                            'Investigator: ', ctd.lead_sponsor_name, E'\n',
                            'Start Date: ', ctd.start_date::TEXT, E'\n',
                            'Age Range: ', COALESCE(ctd.minimum_age, 'Not specified'), ' - ', COALESCE(ctd.maximum_age, 'Not specified'), E'\n',
                            'Gender: ', COALESCE(ctd.sex, 'Not specified'), E'\n\n',
                            'Brief Summary: ', COALESCE(ctd.brief_summary, 'Not available'), E'\n\n',
                            'Detailed Description: ', COALESCE(ctd.detailed_description, 'Not available'), E'\n\n',
                            'Inclusion Criteria: ', COALESCE(ctd.inclusion_criteria, 'Not available'), E'\n\n',
                            'Exclusion Criteria: ', COALESCE(ctd.exclusion_criteria, 'Not available'), E'\n\n',
                            'Eligibility Criteria: ', COALESCE(ctd.eligibility_criteria, 'Not available')
                        ) as combined_trial_text
                    FROM insightsedge.clinical_trial_details ctd
                    WHERE ctd.nct_id = :trial_id
                        AND ctd.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION', 'AVAILABLE')
                """)
                result = connection.execute(query, {"trial_id": trial_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "trial_id": str(row[0]),
                        "title": str(row[1]),
                        "condition": str(row[2]),
                        "phase": str(row[3]),
                        "status": str(row[4]),
                        "investigator": str(row[5]),
                        "created_date": str(row[6]),
                        "patients_matched": int(row[7]),
                        "matching_status": str(row[8]),
                        "combined_trial_text": str(row[9])
                    }
                return None
        except Exception as e:
            print(f"Error getting trial by ID {trial_id}: {e}")
            return None
