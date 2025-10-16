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

# Unified Bidirectional Matching Configuration
UNIFIED_EVALUATION_ENABLED = os.getenv("UNIFIED_EVALUATION_ENABLED", "true").lower() == "true"
BIDIRECTIONAL_BATCH_SIZE = int(os.getenv("BIDIRECTIONAL_BATCH_SIZE", "10"))
COMBINED_SCORING_WEIGHTS = {
    "p2t_weight": float(os.getenv("P2T_WEIGHT", "0.6")),
    "t2p_weight": float(os.getenv("T2P_WEIGHT", "0.4"))
}
UNIFIED_PROMPT_TEMPLATE = os.getenv("UNIFIED_PROMPT_TEMPLATE", "unified_bidirectional_prompt_v1")

# JSON Data Persistence Configuration (No Database Mode)
USE_JSON_PERSISTENCE = os.getenv("USE_JSON_PERSISTENCE", "true").lower() == "true"
JSON_DATA_DIR = os.getenv("JSON_DATA_DIR", "data")
JSON_CLEANUP_DAYS = int(os.getenv("JSON_CLEANUP_DAYS", "30"))

# Hybrid Matching Configuration
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.7"))  # Weight for embedding vs BM25
MAX_TRIALS_FOR_LLM = int(os.getenv("MAX_TRIALS_FOR_LLM", "10"))
MAX_PATIENTS_FOR_LLM = int(os.getenv("MAX_PATIENTS_FOR_LLM", "10"))

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
print(f"  - USE_DATABASE: {USE_DATABASE}")
print(f"  - UNIFIED_EVALUATION_ENABLED: {UNIFIED_EVALUATION_ENABLED}")
print(f"  - USE_JSON_PERSISTENCE: {USE_JSON_PERSISTENCE}")
print(f"  - SCHEDULER_INTERVAL_MINUTES: {SCHEDULER_INTERVAL_MINUTES}")
print(f"  - MAX_CONCURRENT_TASKS: {MAX_CONCURRENT_TASKS}")
print(f"  - LOG_LEVEL: {LOG_LEVEL}")
