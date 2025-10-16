"""
Configuration file for Windows Trial Scheduler

This file contains all configuration settings for the standalone trial scheduler.
Modify these settings as needed for your environment.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

class Config:
    """Configuration class for Windows Trial Scheduler"""
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://Admin:NeXtUrN%40123@13.60.219.182:5432/Insightedgedb")
    
    # Legacy database configuration (for backward compatibility)
    DB_HOST = os.getenv('DB_HOST', '13.60.219.182')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'Insightedgedb')
    DB_USER = os.getenv('DB_USER', 'Admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'NeXtUrN%40123')
    
    # ClinicalTrials.gov API Configuration
    API_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    TARGET_STATUSES = ["RECRUITING", "AVAILABLE", "ENROLLING_BY_INVITATION"]
    
    # Geographic Configuration
    SAN_FRANCISCO_LAT = 37.7749
    SAN_FRANCISCO_LON = -122.4194
    SEARCH_RADIUS_KM = 200  # Radius in kilometers (change to 300, 400, etc. as needed)
    
    # Colorectal Cancer Conditions
    COLORECTAL_CANCER_CONDITIONS = [
        "metastatic colorectal cancer",
        "stage IV colon cancer", 
        "advanced colorectal cancer",
        "incurable colorectal cancer"
    ]
    
    # Usage Examples:
    # To change radius: Set SEARCH_RADIUS_KM = 300 (for 300km radius)
    # To add conditions: Add new conditions to COLORECTAL_CANCER_CONDITIONS list
    # API will automatically filter for trials within radius with target statuses
    
    # Location Filtering (legacy - kept for backward compatibility)
    TARGET_LOCATION = "San Francisco"  # Filter for San Francisco trials only
    
    # Rate Limiting
    REQUEST_DELAY = 1.0  # seconds between requests
    BATCH_SIZE = 100  # trials per batch
    
    # Pagination Settings
    PAGE_SIZE = 1000  # trials per API request
    MAX_PAGES = 50  # maximum pages per status (50,000 trials per status)
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/trial_scheduler.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Execution Settings
    TIMEOUT_SECONDS = 30  # API request timeout
    MAX_RETRIES = 3  # maximum retries for failed requests
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL"""
        # Use DATABASE_URL if available, otherwise construct from individual components
        if cls.DATABASE_URL and cls.DATABASE_URL != "postgresql+psycopg2://Admin:NeXtUrN%40123@13.60.219.182:5432/Insightedgedb":
            return cls.DATABASE_URL
        return f"postgresql+psycopg2://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def get_geographic_filter(cls) -> str:
        """Build geographic distance filter string"""
        return f"distance({cls.SAN_FRANCISCO_LAT},{cls.SAN_FRANCISCO_LON},{cls.SEARCH_RADIUS_KM}km)"
    
    @classmethod
    def get_condition_filter(cls) -> str:
        """Build condition filter string for colorectal cancer conditions"""
        # Use the first condition as primary filter
        # We'll search each condition separately to avoid API complexity
        return cls.COLORECTAL_CANCER_CONDITIONS[0]  # "metastatic colorectal cancer"
    
    @classmethod
    def get_all_condition_filters(cls) -> List[str]:
        """Get all condition filters as separate strings"""
        return cls.COLORECTAL_CANCER_CONDITIONS
    
    @classmethod
    def get_api_params(cls, status: str, page_size: int = None) -> Dict[str, Any]:
        """Get API parameters for a specific status with geographic and condition filtering"""
        params = {
            'format': 'json',
            'pageSize': page_size or cls.PAGE_SIZE,
            'countTotal': 'true',
            'filter.overallStatus': status,
            'query.cond': cls.get_condition_filter(),  # Add colorectal cancer condition filter
            'filter.geo': cls.get_geographic_filter()  # Add geographic distance filter
        }
        return params
    
    @classmethod
    def get_api_params_for_condition(cls, status: str, condition: str, page_size: int = None) -> Dict[str, Any]:
        """Get API parameters for a specific status and condition with geographic filtering"""
        params = {
            'format': 'json',
            'pageSize': page_size or cls.PAGE_SIZE,
            'countTotal': 'true',
            'filter.overallStatus': status,
            'query.cond': condition,  # Use specific condition
            'filter.geo': cls.get_geographic_filter()  # Add geographic distance filter
        }
        return params
    
    @classmethod
    def get_api_params_all_statuses(cls, page_size: int = None) -> Dict[str, Any]:
        """Get API parameters for all target statuses with geographic and condition filtering"""
        # For multiple statuses, we need to make separate calls or use a different approach
        # The API doesn't support multiple filter.overallStatus parameters in one call
        params = {
            'format': 'json',
            'pageSize': page_size or cls.PAGE_SIZE,
            'countTotal': 'true',
            'query.cond': cls.get_condition_filter(),  # Add colorectal cancer condition filter
            'filter.geo': cls.get_geographic_filter()  # Add geographic distance filter
        }
        
        # Note: Multiple statuses need to be handled by making separate API calls
        # This method returns base parameters without status filter
        return params
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER']
        
        for var in required_vars:
            if not getattr(cls, var):
                print(f"Error: {var} is not set")
                return False
        
        return True

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    LOG_LEVEL = "DEBUG"
    REQUEST_DELAY = 0.5  # Faster for development

class ProductionConfig(Config):
    """Production environment configuration"""
    LOG_LEVEL = "INFO"
    REQUEST_DELAY = 2.0  # Slower for production
    MAX_PAGES = 5  # Limit trials in production

class TestingConfig(Config):
    """Testing environment configuration"""
    LOG_LEVEL = "DEBUG"
    MAX_PAGES = 1  # Minimal trials for testing
    BATCH_SIZE = 10

# Configuration factory
def get_config(env: str = None) -> Config:
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(env.lower(), DevelopmentConfig)
