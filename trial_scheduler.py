#!/usr/bin/env python3
"""
Windows Task Scheduler Integration for Clinical Trials Data Fetching

This standalone script fetches clinical trials from ClinicalTrials.gov API
and populates the insightsedge.clinical_trial_details table.

Usage:
    python trial_scheduler.py

Can be scheduled with Windows Task Scheduler to run daily/weekly/monthly.
"""

import asyncio
import logging
import json
import requests
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extras import RealDictCursor
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trial_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WindowsTrialScheduler:
    """Standalone trial scheduler for Windows Task Scheduler integration"""
    
    def __init__(self):
        """Initialize the scheduler with configuration"""
        self.execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        
        # Load configuration
        self.config = get_config()
        
        # ClinicalTrials.gov API configuration
        self.api_base_url = self.config.API_BASE_URL
        self.target_statuses = self.config.TARGET_STATUSES
        self.target_location = self.config.TARGET_LOCATION
        
        # Rate limiting
        self.request_delay = self.config.REQUEST_DELAY
        self.batch_size = self.config.BATCH_SIZE
        
        # Database configuration
        self.db_engine = None
        self.db_session = None
        
        # Statistics
        self.stats = {
            'total_fetched': 0,
            'total_saved': 0,
            'errors': 0,
            'execution_time': 0
        }
        
        logger.info(f"Windows Trial Scheduler initialized - Execution ID: {self.execution_id}")
    
    def setup_database_connection(self):
        """Setup database connection using environment variables"""
        try:
            # Get database credentials from environment variables
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'insightsedge')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', '')
            
            # Create database connection string
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Create SQLAlchemy engine
            self.db_engine = create_engine(db_url, echo=False)
            
            # Test connection
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    async def fetch_trials_from_api(self) -> List[Dict[str, Any]]:
        """Fetch trials from ClinicalTrials.gov API using proper pagination with nextPageToken"""
        try:
            logger.info("Using proven API v2 approach for trial fetching with proper pagination")
            
            all_trials = []
            page_size = self.config.PAGE_SIZE
            max_pages = self.config.MAX_PAGES
            
            # Fetch trials for each target status and each specific condition
            all_conditions = self.config.get_all_condition_filters()
            logger.info(f"Searching for {len(all_conditions)} specific conditions: {', '.join(all_conditions)}")
            
            for condition in all_conditions:
                logger.info(f"Searching for condition: {condition}")
                
                for status in self.target_statuses:
                    logger.info(f"Fetching {status} trials for '{condition}' in {self.target_location}...")
                    current_page = 1
                    next_page_token = None
                    
                    while current_page <= max_pages:
                        logger.info(f"Fetching page {current_page} for {status} trials with condition '{condition}'...")
                        
                        # Use configuration-based API parameters with specific condition filtering
                        params = self.config.get_api_params_for_condition(status, condition, page_size)
                        
                        # Add nextPageToken if available
                        if next_page_token:
                            params['pageToken'] = next_page_token
                        
                        try:
                            response = requests.get(
                                self.api_base_url,
                                params=params,
                                timeout=30
                            )
                            response.raise_for_status()
                            
                            data = response.json()
                            studies = data.get('studies', [])
                            total_count = data.get('totalCount', 0)
                            next_page_token = data.get('nextPageToken')
                            
                            if not studies:
                                logger.info(f"No more {status} studies found on page {current_page} for condition '{condition}'")
                                break
                            
                            logger.info(f"API returned {len(studies)} {status} studies on page {current_page} for condition '{condition}' (Total available: {total_count})")
                            
                            # Process studies
                            processed_trials = []
                            for study in studies:
                                trial_data = self._process_study_data(study)
                                if trial_data:
                                    processed_trials.append(trial_data)
                            
                            all_trials.extend(processed_trials)
                            logger.info(f"Processed {len(processed_trials)} {status} trials from page {current_page} for condition '{condition}'")
                            
                            # Check if we have more pages to fetch
                            if not next_page_token:
                                logger.info(f"Reached last page for {status} trials with condition '{condition}' (no nextPageToken) - moving to next status")
                                break
                            
                            current_page += 1
                            
                            # Rate limiting
                            await asyncio.sleep(self.request_delay)
                            
                        except requests.exceptions.RequestException as e:
                            logger.error(f"API request failed for {status} page {current_page} with condition '{condition}': {str(e)}")
                            break
            
            logger.info(f"Total trials fetched from API: {len(all_trials)}")
            self.stats['total_fetched'] = len(all_trials)
            return all_trials
            
        except Exception as e:
            logger.error(f"Error fetching trials from API: {str(e)}")
            self.stats['errors'] += 1
            return []
    
    def _process_study_data(self, study: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process raw study data from API into database format"""
        try:
            protocol_section = study.get('protocolSection', {})
            identification_module = protocol_section.get('identificationModule', {})
            status_module = protocol_section.get('statusModule', {})
            design_module = protocol_section.get('designModule', {})
            eligibility_module = protocol_section.get('eligibilityModule', {})
            conditions_module = protocol_section.get('conditionsModule', {})
            contacts_location_module = protocol_section.get('contactsLocationsModule', {})
            description_module = protocol_section.get('descriptionModule', {})
            outcomes_module = protocol_section.get('outcomesModule', {})
            
            # Extract basic information
            nct_id = identification_module.get('nctId', '')
            brief_title = identification_module.get('briefTitle', '')
            official_title = identification_module.get('officialTitle', '')
            
            # Check if trial has required status
            overall_status = status_module.get('overallStatus', '')
            if overall_status not in self.target_statuses:
                return None
            
            # Extract conditions
            conditions = []
            if conditions_module.get('conditions'):
                conditions = [condition.strip() for condition in conditions_module['conditions']]
            
            # Extract eligibility criteria
            inclusion_criteria = []
            exclusion_criteria = []
            if eligibility_module.get('eligibilityCriteria'):
                criteria_text = eligibility_module['eligibilityCriteria']
                # Simple split by inclusion/exclusion keywords
                if 'Inclusion Criteria:' in criteria_text:
                    parts = criteria_text.split('Inclusion Criteria:')
                    if len(parts) > 1:
                        inclusion_part = parts[1].split('Exclusion Criteria:')[0]
                        inclusion_criteria = [line.strip() for line in inclusion_part.split('\n') if line.strip()]
                
                if 'Exclusion Criteria:' in criteria_text:
                    parts = criteria_text.split('Exclusion Criteria:')
                    if len(parts) > 1:
                        exclusion_criteria = [line.strip() for line in parts[1].split('\n') if line.strip()]
            
            # Extract locations
            locations = []
            if contacts_location_module.get('locations'):
                for location in contacts_location_module['locations']:
                    location_info = {
                        'name': location.get('name', ''),
                        'city': location.get('city', ''),
                        'state': location.get('state', ''),
                        'country': location.get('country', '')
                    }
                    locations.append(location_info)
            
            # Extract age and sex requirements
            minimum_age = eligibility_module.get('minimumAge', '')
            maximum_age = eligibility_module.get('maximumAge', '')
            sex = eligibility_module.get('sex', 'All')
            
            # Extract study phase
            phases = design_module.get('phases', [])
            study_phase = phases[0] if phases else 'Not specified'
            
            # Extract interventions
            interventions = []
            if design_module.get('interventions'):
                for intervention in design_module['interventions']:
                    interventions.append({
                        'name': intervention.get('name', ''),
                        'type': intervention.get('type', ''),
                        'description': intervention.get('description', '')
                    })
            
            # Extract outcomes
            primary_outcomes = []
            secondary_outcomes = []
            if outcomes_module.get('primaryOutcomes'):
                primary_outcomes = [outcome.get('title', '') for outcome in outcomes_module['primaryOutcomes']]
            if outcomes_module.get('secondaryOutcomes'):
                secondary_outcomes = [outcome.get('title', '') for outcome in outcomes_module['secondaryOutcomes']]
            
            # Extract sponsor information
            lead_sponsor = contacts_location_module.get('leadSponsor', {})
            lead_sponsor_name = lead_sponsor.get('name', '') if lead_sponsor else ''
            
            # Extract enrollment count
            enrollment_info = status_module.get('enrollmentInfo', {})
            enrollment_count = enrollment_info.get('count', 0) if enrollment_info else 0
            
            # Extract dates with proper formatting
            start_date = self._format_date(status_module.get('startDateStruct', {}).get('date', ''))
            completion_date = self._format_date(status_module.get('completionDateStruct', {}).get('date', ''))
            
            # Create trial data dictionary
            trial_data = {
                'nct_id': nct_id,
                'brief_title': brief_title,
                'study_title': official_title,
                'official_title': official_title,
                'conditions': json.dumps(conditions) if conditions else None,
                'overall_status': overall_status,
                'study_phase': study_phase,
                'start_date': start_date,
                'completion_date': completion_date,
                'inclusion_criteria': json.dumps(inclusion_criteria) if inclusion_criteria else None,
                'exclusion_criteria': json.dumps(exclusion_criteria) if exclusion_criteria else None,
                'interventions': json.dumps(interventions) if interventions else None,
                'locations': json.dumps(locations) if locations else None,
                'primary_outcomes': json.dumps(primary_outcomes) if primary_outcomes else None,
                'secondary_outcomes': json.dumps(secondary_outcomes) if secondary_outcomes else None,
                'lead_sponsor_name': lead_sponsor_name,
                'brief_summary': description_module.get('briefSummary', ''),
                'detailed_description': description_module.get('detailedDescription', ''),
                'enrollment_count': enrollment_count,
                'study_type': design_module.get('studyType', ''),
                'sex': sex,
                'minimum_age': minimum_age,
                'maximum_age': maximum_age,
                'eligibility_criteria': eligibility_module.get('eligibilityCriteria', ''),
                'source_api': 'ClinicalTrials.gov (Windows Scheduler)',
                'last_synced': datetime.now(),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            return trial_data
            
        except Exception as e:
            logger.error(f"Error processing study data: {str(e)}")
            return None
    
    def _format_date(self, date_str: str) -> Optional[str]:
        """Format incomplete dates to valid PostgreSQL date format"""
        if not date_str or not isinstance(date_str, str):
            return None
        
        date_str = date_str.strip()
        
        # Handle different date formats from API
        if len(date_str) == 4:  # Year only: "2026"
            return f"{date_str}-01-01"  # Default to January 1st
        elif len(date_str) == 7 and date_str[4] == '-':  # Year-Month: "2026-04"
            return f"{date_str}-01"  # Default to 1st day of month
        elif len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':  # Full date: "2026-04-15"
            return date_str
        else:
            # Try to parse as date, if fails return None
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid date format: {date_str}")
                return None
    
    async def populate_database(self, trials_data: List[Dict[str, Any]]) -> int:
        """Populate database with trial data - Only insert new trials, don't update existing"""
        saved_count = 0
        
        try:
            with self.db_engine.connect() as conn:
                for trial_data in trials_data:
                    try:
                        # Check if trial already exists
                        check_query = text("""
                            SELECT nct_id FROM insightsedge.clinical_trial_details 
                            WHERE nct_id = :nct_id
                        """)
                        
                        result = conn.execute(check_query, {'nct_id': trial_data['nct_id']}).fetchone()
                        
                        if result:
                            logger.info(f"Skipping existing trial: {trial_data['nct_id']}")
                            continue
                        
                        # Insert new trial
                        insert_query = text("""
                            INSERT INTO insightsedge.clinical_trial_details (
                                nct_id, study_title, brief_title, official_title, overall_status,
                                study_phase, start_date, completion_date, conditions, interventions,
                                brief_summary, detailed_description, enrollment_count, study_type,
                                sex, minimum_age, maximum_age, eligibility_criteria, inclusion_criteria,
                                exclusion_criteria, locations, primary_outcomes, secondary_outcomes,
                                lead_sponsor_name, source_api, last_synced, created_at, updated_at
                            ) VALUES (
                                :nct_id, :study_title, :brief_title, :official_title, :overall_status,
                                :study_phase, :start_date, :completion_date, :conditions, :interventions,
                                :brief_summary, :detailed_description, :enrollment_count, :study_type,
                                :sex, :minimum_age, :maximum_age, :eligibility_criteria, :inclusion_criteria,
                                :exclusion_criteria, :locations, :primary_outcomes, :secondary_outcomes,
                                :lead_sponsor_name, :source_api, :last_synced, :created_at, :updated_at
                            )
                        """)
                        
                        conn.execute(insert_query, trial_data)
                        conn.commit()
                        
                        saved_count += 1
                        logger.info(f"Added new trial: {trial_data['nct_id']}")
                        
                        # Commit in batches
                        if saved_count % self.batch_size == 0:
                            logger.info(f"Committed batch - {saved_count} trials processed")
                    
                    except Exception as e:
                        logger.error(f"Error saving trial {trial_data.get('nct_id', 'unknown')}: {str(e)}")
                        conn.rollback()
                        continue
                
                logger.info(f"Database population completed - {saved_count} trials saved")
                self.stats['total_saved'] = saved_count
                
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            self.stats['errors'] += 1
            raise
        
        return saved_count
    
    def log_execution_summary(self):
        """Log execution summary"""
        end_time = datetime.now()
        execution_time = (end_time - self.start_time).total_seconds()
        self.stats['execution_time'] = execution_time
        
        logger.info("=" * 60)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Execution ID: {self.execution_id}")
        logger.info(f"Start Time: {self.start_time}")
        logger.info(f"End Time: {end_time}")
        logger.info(f"Execution Time: {execution_time:.2f} seconds")
        logger.info(f"Total Trials Fetched: {self.stats['total_fetched']}")
        logger.info(f"Total Trials Saved: {self.stats['total_saved']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)
    
    async def run(self):
        """Main execution method"""
        try:
            logger.info(f"Starting Windows Trial Scheduler - Execution ID: {self.execution_id}")
            
            # Setup database connection
            if not self.setup_database_connection():
                logger.error("Failed to establish database connection")
                return False
            
            # Fetch trials from API
            trials_data = await self.fetch_trials_from_api()
            
            if not trials_data:
                logger.warning("No trial data fetched from API")
                return False
            
            # Populate database
            saved_count = await self.populate_database(trials_data)
            
            # Log execution summary
            self.log_execution_summary()
            
            logger.info("Windows Trial Scheduler execution completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Windows Trial Scheduler execution failed: {str(e)}")
            self.stats['errors'] += 1
            self.log_execution_summary()
            return False

async def main():
    """Main entry point for the script"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create and run scheduler
    scheduler = WindowsTrialScheduler()
    success = await scheduler.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
