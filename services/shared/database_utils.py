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
    
    # Automation-specific methods for processing ALL data
    def get_all_patients_for_automation(self) -> List[Dict[str, Any]]:
        """Get ALL patients from database for automation processing"""
        try:
            with self.get_connection() as connection:
                query = text("SELECT * FROM insightsedge.get_patient_data_for_keywords(999999)")
                result = connection.execute(query)
                
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
                
                print(f"Retrieved {len(patients)} patients for automation processing")
                return patients
        except Exception as e:
            print(f"Error getting all patients for automation: {e}")
            return []
    
    def get_all_trials_for_automation(self) -> List[Dict[str, Any]]:
        """Get ALL trials from database for automation processing"""
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
                    WHERE ctd.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION', 'AVAILABLE')
                    ORDER BY ctd.created_at DESC
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
                
                print(f"Retrieved {len(trials)} trials for automation processing")
                return trials
        except Exception as e:
            print(f"Error getting all trials for automation: {e}")
            return []
    
    # Methods for automation processing status and results
    def get_patients_needing_embeddings(self) -> List[Dict[str, Any]]:
        """Get patients that need embedding generation"""
        try:
            with self.get_connection() as connection:
                query = text("SELECT * FROM insightsedge.get_patients_needing_embeddings()")
                result = connection.execute(query)
                
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
                
                print(f"Found {len(patients)} patients needing embeddings")
                return patients
        except Exception as e:
            print(f"Error getting patients needing embeddings: {e}")
            return []
    
    def get_trials_needing_embeddings(self) -> List[Dict[str, Any]]:
        """Get trials that need embedding generation"""
        try:
            with self.get_connection() as connection:
                query = text("SELECT * FROM insightsedge.get_trials_needing_embeddings()")
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
                
                print(f"Found {len(trials)} trials needing embeddings")
                return trials
        except Exception as e:
            print(f"Error getting trials needing embeddings: {e}")
            return []
    
    def update_patient_processing_status(self, patient_id: int, embedding_generated: bool = None, 
                                       keywords_generated: bool = None, error_message: str = None):
        """Update patient processing status"""
        try:
            with self.get_connection() as connection:
                query = text("SELECT insightsedge.update_patient_processing_status(:patient_id, :embedding_generated, :keywords_generated, :error_message)")
                connection.execute(query, {
                    "patient_id": patient_id,
                    "embedding_generated": embedding_generated,
                    "keywords_generated": keywords_generated,
                    "error_message": error_message
                })
                connection.commit()
        except Exception as e:
            print(f"Error updating patient processing status: {e}")
    
    def update_trial_processing_status(self, trial_id: str, embedding_generated: bool = None, error_message: str = None):
        """Update trial processing status"""
        try:
            with self.get_connection() as connection:
                query = text("SELECT insightsedge.update_trial_processing_status(:trial_id, :embedding_generated, :error_message)")
                connection.execute(query, {
                    "trial_id": trial_id,
                    "embedding_generated": embedding_generated,
                    "error_message": error_message
                })
                connection.commit()
        except Exception as e:
            print(f"Error updating trial processing status: {e}")
    
    def store_patient_trial_match(self, patient_id: int, patient_mrn: str, trial_id: str, 
                                 hybrid_score: float, embedding_score: float, bm25_score: float,
                                 llm_evaluation_score: float = None, llm_evaluation_text: str = None,
                                 match_rank: int = None, batch_id: str = None):
        """Store patient-trial matching result"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    INSERT INTO insightsedge.patient_trial_matches 
                    (patient_id, patient_mrn, trial_id, hybrid_score, embedding_score, bm25_score, 
                     llm_evaluation_score, llm_evaluation_text, match_rank, processing_batch_id)
                    VALUES (:patient_id, :patient_mrn, :trial_id, :hybrid_score, :embedding_score, :bm25_score,
                            :llm_evaluation_score, :llm_evaluation_text, :match_rank, :batch_id)
                    ON CONFLICT (patient_id, trial_id, processing_batch_id) DO UPDATE SET
                        hybrid_score = EXCLUDED.hybrid_score,
                        embedding_score = EXCLUDED.embedding_score,
                        bm25_score = EXCLUDED.bm25_score,
                        llm_evaluation_score = EXCLUDED.llm_evaluation_score,
                        llm_evaluation_text = EXCLUDED.llm_evaluation_text,
                        match_rank = EXCLUDED.match_rank,
                        updated_at = CURRENT_TIMESTAMP
                """)
                connection.execute(query, {
                    "patient_id": patient_id,
                    "patient_mrn": patient_mrn,
                    "trial_id": trial_id,
                    "hybrid_score": hybrid_score,
                    "embedding_score": embedding_score,
                    "bm25_score": bm25_score,
                    "llm_evaluation_score": llm_evaluation_score,
                    "llm_evaluation_text": llm_evaluation_text,
                    "match_rank": match_rank,
                    "batch_id": batch_id
                })
                connection.commit()
        except Exception as e:
            print(f"Error storing patient-trial match: {e}")
    
    def store_trial_patient_match(self, trial_id: str, patient_id: int, patient_mrn: str,
                                 hybrid_score: float, embedding_score: float, bm25_score: float,
                                 llm_evaluation_score: float = None, llm_evaluation_text: str = None,
                                 match_rank: int = None, batch_id: str = None):
        """Store trial-patient matching result"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    INSERT INTO insightsedge.trial_patient_matches 
                    (trial_id, patient_id, patient_mrn, hybrid_score, embedding_score, bm25_score,
                     llm_evaluation_score, llm_evaluation_text, match_rank, processing_batch_id)
                    VALUES (:trial_id, :patient_id, :patient_mrn, :hybrid_score, :embedding_score, :bm25_score,
                            :llm_evaluation_score, :llm_evaluation_text, :match_rank, :batch_id)
                    ON CONFLICT (trial_id, patient_id, processing_batch_id) DO UPDATE SET
                        hybrid_score = EXCLUDED.hybrid_score,
                        embedding_score = EXCLUDED.embedding_score,
                        bm25_score = EXCLUDED.bm25_score,
                        llm_evaluation_score = EXCLUDED.llm_evaluation_score,
                        llm_evaluation_text = EXCLUDED.llm_evaluation_text,
                        match_rank = EXCLUDED.match_rank,
                        updated_at = CURRENT_TIMESTAMP
                """)
                connection.execute(query, {
                    "trial_id": trial_id,
                    "patient_id": patient_id,
                    "patient_mrn": patient_mrn,
                    "hybrid_score": hybrid_score,
                    "embedding_score": embedding_score,
                    "bm25_score": bm25_score,
                    "llm_evaluation_score": llm_evaluation_score,
                    "llm_evaluation_text": llm_evaluation_text,
                    "match_rank": match_rank,
                    "batch_id": batch_id
                })
                connection.commit()
        except Exception as e:
            print(f"Error storing trial-patient match: {e}")
    
    def create_processing_batch(self, batch_id: str, processing_type: str, total_items: int, metadata: Dict[str, Any] = None):
        """Create a new processing batch"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    INSERT INTO insightsedge.automation_processing_log 
                    (batch_id, processing_type, total_items, metadata)
                    VALUES (:batch_id, :processing_type, :total_items, :metadata)
                """)
                connection.execute(query, {
                    "batch_id": batch_id,
                    "processing_type": processing_type,
                    "total_items": total_items,
                    "metadata": json.dumps(metadata) if metadata else None
                })
                connection.commit()
        except Exception as e:
            print(f"Error creating processing batch: {e}")
    
    def update_processing_batch(self, batch_id: str, processing_type: str, processed_items: int = None, 
                              failed_items: int = None, status: str = None, error_message: str = None):
        """Update processing batch status"""
        try:
            with self.get_connection() as connection:
                updates = []
                params = {"batch_id": batch_id, "processing_type": processing_type}
                
                if processed_items is not None:
                    updates.append("processed_items = :processed_items")
                    params["processed_items"] = processed_items
                
                if failed_items is not None:
                    updates.append("failed_items = :failed_items")
                    params["failed_items"] = failed_items
                
                if status is not None:
                    updates.append("status = :status")
                    params["status"] = status
                    if status == "completed":
                        updates.append("completed_at = CURRENT_TIMESTAMP")
                
                if error_message is not None:
                    updates.append("error_message = :error_message")
                    params["error_message"] = error_message
                
                if updates:
                    query = text(f"""
                        UPDATE insightsedge.automation_processing_log 
                        SET {', '.join(updates)}
                        WHERE batch_id = :batch_id AND processing_type = :processing_type
                    """)
                    connection.execute(query, params)
                    connection.commit()
        except Exception as e:
            print(f"Error updating processing batch: {e}")