"""
Shared Database Utilities
Common database operations and stored procedures for both patient-to-trial and trial-to-patient matching
"""

import json
import numpy as np
from datetime import datetime
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
    
    def _safe_isoformat(self, date_value):
        """Safely convert date/datetime to ISO format string, handling both datetime objects and strings"""
        if date_value is None:
            return None
        
        # Check if it's already a datetime object
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        
        # Check if it's already a string
        if isinstance(date_value, str):
            # If it's already a string, check if it looks like a valid ISO format
            if 'T' in date_value or len(date_value) >= 10:  # ISO format has 'T' or at least YYYY-MM-DD
                # Try to validate it's a proper ISO format
                try:
                    # Try parsing with fromisoformat (supports various formats)
                    datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    return date_value
                except (ValueError, AttributeError):
                    pass
            
            # Try to parse from common date formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S',  # PostgreSQL timestamp format
                '%Y-%m-%d %H:%M:%S.%f',  # PostgreSQL timestamp with microseconds
                '%Y-%m-%d',  # Date only
                '%m/%d/%Y',  # US format
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.isoformat()
                except (ValueError, AttributeError):
                    continue
            
            # If all parsing fails, return the string as-is
            return date_value
        
        # Check if it has date/time methods (like date objects from database)
        if hasattr(date_value, 'isoformat'):
            try:
                return date_value.isoformat()
            except:
                pass
        
        # For other types, try to convert to string
        try:
            return str(date_value)
        except:
            return None
    
    def _safe_json_load(self, data):
        """Safely load JSON data, handling both string and list formats"""
        if data is None:
            return []
        elif isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return []
        elif isinstance(data, (list, dict)):
            return data
        else:
            return []
    
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
                        "date_of_visit": self._safe_isoformat(row[6]),
                        "created_at": self._safe_isoformat(row[7])
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
                        "date_of_visit": self._safe_isoformat(row[6]),
                        "created_at": self._safe_isoformat(row[7])
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
                        "date_of_visit": self._safe_isoformat(row[6]),
                        "created_at": self._safe_isoformat(row[7])
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
    
    def save_patient_keywords(self, keywords_data: Dict[str, Any]) -> bool:
        """Save patient keywords to database"""
        try:
            with self.get_connection() as connection:
                # Check if keywords already exist for this patient
                check_query = text("""
                    SELECT id FROM insightsedge.patient_keywords 
                    WHERE patient_id = :patient_id
                """)
                result = connection.execute(check_query, {"patient_id": keywords_data["patient_id"]})
                existing_record = result.fetchone()
                
                if existing_record:
                    # Update existing record
                    update_query = text("""
                        UPDATE insightsedge.patient_keywords SET
                            mrn = :mrn,
                            age = :age,
                            gender = :gender,
                            summary = :summary,
                            primary_diagnosis = :primary_diagnosis,
                            stage = :stage,
                            metastatic_sites = :metastatic_sites,
                            molecular_markers = :molecular_markers,
                            comorbidities = :comorbidities,
                            medications = :medications,
                            allergies = :allergies,
                            performance_status = :performance_status,
                            family_history = :family_history,
                            keywords = :keywords,
                            keywords_text = :keywords_text,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE patient_id = :patient_id
                    """)
                    
                    connection.execute(update_query, {
                        "patient_id": keywords_data["patient_id"],
                        "mrn": keywords_data.get("mrn"),
                        "age": keywords_data.get("age"),
                        "gender": keywords_data.get("gender"),
                        "summary": keywords_data.get("summary"),
                        "primary_diagnosis": keywords_data.get("primary_diagnosis"),
                        "stage": keywords_data.get("stage"),
                        "metastatic_sites": json.dumps(keywords_data.get("metastatic_sites", [])),
                        "molecular_markers": json.dumps(keywords_data.get("molecular_markers", [])),
                        "comorbidities": json.dumps(keywords_data.get("comorbidities", [])),
                        "medications": json.dumps(keywords_data.get("medications", [])),
                        "allergies": json.dumps(keywords_data.get("allergies", [])),
                        "performance_status": keywords_data.get("performance_status"),
                        "family_history": json.dumps(keywords_data.get("family_history", [])),
                        "keywords": json.dumps(keywords_data.get("keywords", [])),
                        "keywords_text": keywords_data.get("keywords_text")
                    })
                    print(f"Updated keywords for patient {keywords_data['patient_id']}")
                else:
                    # Insert new record
                    insert_query = text("""
                        INSERT INTO insightsedge.patient_keywords (
                            patient_id, mrn, age, gender, summary, primary_diagnosis, stage,
                            metastatic_sites, molecular_markers, comorbidities, medications,
                            allergies, performance_status, family_history, keywords, keywords_text
                        ) VALUES (
                            :patient_id, :mrn, :age, :gender, :summary, :primary_diagnosis, :stage,
                            :metastatic_sites, :molecular_markers, :comorbidities, :medications,
                            :allergies, :performance_status, :family_history, :keywords, :keywords_text
                        )
                    """)
                    
                    connection.execute(insert_query, {
                        "patient_id": keywords_data["patient_id"],
                        "mrn": keywords_data.get("mrn"),
                        "age": keywords_data.get("age"),
                        "gender": keywords_data.get("gender"),
                        "summary": keywords_data.get("summary"),
                        "primary_diagnosis": keywords_data.get("primary_diagnosis"),
                        "stage": keywords_data.get("stage"),
                        "metastatic_sites": json.dumps(keywords_data.get("metastatic_sites", [])),
                        "molecular_markers": json.dumps(keywords_data.get("molecular_markers", [])),
                        "comorbidities": json.dumps(keywords_data.get("comorbidities", [])),
                        "medications": json.dumps(keywords_data.get("medications", [])),
                        "allergies": json.dumps(keywords_data.get("allergies", [])),
                        "performance_status": keywords_data.get("performance_status"),
                        "family_history": json.dumps(keywords_data.get("family_history", [])),
                        "keywords": json.dumps(keywords_data.get("keywords", [])),
                        "keywords_text": keywords_data.get("keywords_text")
                    })
                    print(f"Inserted keywords for patient {keywords_data['patient_id']}")
                
                connection.commit()
                return True
                
        except Exception as e:
            print(f"Error saving patient keywords: {e}")
            return False
    
    def get_patient_keywords(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get patient keywords from database"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    SELECT * FROM insightsedge.patient_keywords 
                    WHERE patient_id = :patient_id
                """)
                result = connection.execute(query, {"patient_id": patient_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "patient_id": row[1],
                        "mrn": row[2],
                        "age": row[3],
                        "gender": row[4],
                        "summary": row[5],
                        "primary_diagnosis": row[6],
                        "stage": row[7],
                        "metastatic_sites": self._safe_json_load(row[8]),
                        "molecular_markers": self._safe_json_load(row[9]),
                        "comorbidities": self._safe_json_load(row[10]),
                        "medications": self._safe_json_load(row[11]),
                        "allergies": self._safe_json_load(row[12]),
                        "performance_status": row[13],
                        "family_history": self._safe_json_load(row[14]),
                        "keywords": self._safe_json_load(row[15]),
                        "keywords_text": row[16],
                        "generated_at": self._safe_isoformat(row[17]),
                        "created_at": self._safe_isoformat(row[18]),
                        "updated_at": self._safe_isoformat(row[19])
                    }
                return None
        except Exception as e:
            print(f"Error getting patient keywords: {e}")
            return None
    
    def get_all_patient_keywords(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all patient keywords from database"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    SELECT * FROM insightsedge.patient_keywords 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """)
                result = connection.execute(query, {"limit": limit})
                
                keywords_list = []
                for row in result:
                    keywords_list.append({
                        "id": row[0],
                        "patient_id": row[1],
                        "mrn": row[2],
                        "age": row[3],
                        "gender": row[4],
                        "summary": row[5],
                        "primary_diagnosis": row[6],
                        "stage": row[7],
                        "metastatic_sites": self._safe_json_load(row[8]),
                        "molecular_markers": self._safe_json_load(row[9]),
                        "comorbidities": self._safe_json_load(row[10]),
                        "medications": self._safe_json_load(row[11]),
                        "allergies": self._safe_json_load(row[12]),
                        "performance_status": row[13],
                        "family_history": self._safe_json_load(row[14]),
                        "keywords": self._safe_json_load(row[15]),
                        "keywords_text": row[16],
                        "generated_at": self._safe_isoformat(row[17]),
                        "created_at": self._safe_isoformat(row[18]),
                        "updated_at": self._safe_isoformat(row[19])
                    })
                
                return keywords_list
        except Exception as e:
            print(f"Error getting all patient keywords: {e}")
            return []
    
    def delete_patient_keywords(self, patient_id: int) -> bool:
        """Delete patient keywords from database"""
        try:
            with self.get_connection() as connection:
                query = text("""
                    DELETE FROM insightsedge.patient_keywords 
                    WHERE patient_id = :patient_id
                """)
                result = connection.execute(query, {"patient_id": patient_id})
                connection.commit()
                
                if result.rowcount > 0:
                    print(f"Deleted keywords for patient {patient_id}")
                    return True
                else:
                    print(f"No keywords found for patient {patient_id}")
                    return False
                    
        except Exception as e:
            print(f"Error deleting patient keywords: {e}")
            return False