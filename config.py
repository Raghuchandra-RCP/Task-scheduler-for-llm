"""
Configuration for Task Scheduler LLM Service
"""
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Configuration flags
USE_DUMMY_DATA = False
USE_LLM_PROCESSING = os.getenv("USE_LLM_PROCESSING", "true").lower() == "true"
USE_DATABASE = os.getenv("USE_DATABASE", "true").lower() == "true"
AUTOMATION_ENABLED = os.getenv("AUTOMATION_ENABLED", "false").lower() == "true"

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAaK5LASwLAzQljsficijwt6--HTPztOx4")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "8000"))
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "60"))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://Admin:NeXtUrN%40123@13.60.219.182:5432/Insightedgedb")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Task Scheduler Configuration
SCHEDULER_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "30"))
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
TASK_TIMEOUT_SECONDS = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))

# Patient Processing Configuration
DEFAULT_PATIENT_LIMIT = int(os.getenv("DEFAULT_PATIENT_LIMIT", "50"))
AUTOMATION_PATIENT_BATCH_SIZE = int(os.getenv("AUTOMATION_PATIENT_BATCH_SIZE", "100"))
AUTOMATION_TRIAL_BATCH_SIZE = int(os.getenv("AUTOMATION_TRIAL_BATCH_SIZE", "100"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "task_scheduler.log")

# API Configuration
API_TITLE = "Task Scheduler LLM Service"
API_DESCRIPTION = "Standalone task scheduler for LLM processing"

if USE_DUMMY_DATA:
    API_DESCRIPTION += " (Dummy Data Mode)"
else:
    API_DESCRIPTION += " (Real Data Mode)"

if USE_LLM_PROCESSING:
    API_DESCRIPTION += " with LLM Processing"
else:
    API_DESCRIPTION += " with Static Data"

print(f"Task Scheduler Configuration loaded:")
print(f"  - USE_DUMMY_DATA: {USE_DUMMY_DATA}")
print(f"  - USE_LLM_PROCESSING: {USE_LLM_PROCESSING}")
print(f"  - AUTOMATION_ENABLED: {AUTOMATION_ENABLED}")
print(f"  - SCHEDULER_INTERVAL_MINUTES: {SCHEDULER_INTERVAL_MINUTES}")
print(f"  - MAX_CONCURRENT_TASKS: {MAX_CONCURRENT_TASKS}")
print(f"  - LOG_LEVEL: {LOG_LEVEL}")
