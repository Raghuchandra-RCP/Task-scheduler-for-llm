# Clinical Trial Matching System - Task Scheduler

A sophisticated **Clinical Trial Matching System** that uses AI/ML to match patients with suitable clinical trials and vice versa. The system combines traditional database queries with modern AI techniques including embeddings, vector search, and OpenAI GPT-4o Mini processing.

## 🚀 Key Features

### **Automation**
- **Full Automation Mode**: Process all patients and trials automatically
- **Manual Mode**: Process specific patients/trials on demand
- **Batch Processing**: Efficient processing of large datasets
- **Progress Tracking**: Real-time monitoring of automation status

### **AI/ML Integration**
- **OpenAI GPT-4o Mini**: Advanced LLM for intelligent matching and evaluation
- **MedCPT Embeddings**: Medical-specific embeddings for semantic understanding
- **FAISS Vector Search**: Fast similarity search for trial-patient matching
- **BM25 Keyword Matching**: Traditional keyword-based matching
- **Hybrid Scoring**: Combines semantic and keyword approaches

### **Dual Processing**
- **Patient-to-Trial**: Find suitable trials for specific patients
- **Trial-to-Patient**: Find suitable patients for specific trials
- **Comprehensive Evaluation**: LLM-based eligibility assessment
- **Detailed Reasoning**: Explainable AI decisions

## 🏗️ System Architecture

```
Clinical Trial Matching System
├── main.py                          # Application entry point
├── task_scheduler.py                # Background task scheduler
├── config.py                        # Configuration management
├── requirements.txt                 # Python dependencies
├── database/                        # Database layer
│   └── patient_trial_stored_procedures.sql
├── services/                        # Business logic services
│   ├── patient_to_trial/           # Patient → Trial matching
│   │   ├── patient_matcher.py
│   │   ├── patient_embedding.py
│   │   ├── patient_evaluator.py
│   │   └── keyword_generator.py
│   ├── trial_to_patient/           # Trial → Patient matching
│   │   ├── trial_matcher.py
│   │   ├── trial_embedding.py
│   │   ├── trial_evaluator.py
│   │   └── hybrid_matcher.py
│   └── shared/                     # Common utilities
│       ├── database_utils.py
│       ├── embedding_utils.py
│       └── llm_utils.py
├── persist/embeddings/              # Cached embeddings and indices
│   ├── patients/                   # Patient embeddings
│   └── trials/                     # Trial embeddings
└── results/                        # Processing results and logs
```

## 🚀 Quick Start

### **1. Environment Setup**

   ```bash
# Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
   pip install -r requirements.txt
   ```

### **2. Configuration**

   Create a `.env` file with your configuration:

   ```env
# Database Configuration
   DATABASE_URL=postgresql+psycopg2://user:password@host:port/database
   
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.2
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3

# Automation Configuration
AUTOMATION_ENABLED=true
AUTOMATION_PATIENT_BATCH_SIZE=100
AUTOMATION_TRIAL_BATCH_SIZE=100

# Task Scheduler Configuration
   SCHEDULER_INTERVAL_MINUTES=30
   MAX_CONCURRENT_TASKS=5
   TASK_TIMEOUT_SECONDS=300
   
# Service Flags
USE_LLM_PROCESSING=true
USE_DATABASE=true
USE_DUMMY_DATA=false

# Logging Configuration
   LOG_LEVEL=INFO
   LOG_FILE=task_scheduler.log
   ```

### **3. Database Setup**

Run the database setup scripts:

```sql
-- Execute the stored procedures
\i database/patient_trial_stored_procedures.sql

-- For automation features (if using automation mode)
\i database/automation_tables.sql
```

### **4. Test Integration**

```bash
# Test OpenAI integration
python test_openai_integration.py

# Test automation system
python test_automation.py
```

### **5. Run the System**

```bash
# Start the task scheduler
python main.py
```

## 🔧 Automation Modes

### **Full Automation Mode (`AUTOMATION_ENABLED=true`)**

When enabled, the system automatically:

1. **Processes ALL patients** in the database
2. **Generates embeddings** for all patients and trials
3. **Runs comprehensive matching** between all patients and trials
4. **Stores results** in dedicated automation tables
5. **Tracks progress** and handles errors gracefully

**Benefits:**
- Complete system-wide matching
- No manual intervention required
- Comprehensive coverage of all data
- Automated progress tracking

### **Manual Mode (`AUTOMATION_ENABLED=false`)**

When disabled, the system:

1. **Processes only new patients** that need embeddings
2. **Processes only new trials** that need embeddings
3. **Runs targeted matching** for specific requests
4. **Stores results** in standard tables

**Benefits:**
- Resource-efficient
- Targeted processing
- Manual control over operations
- Suitable for development/testing

## 🔄 Processing Pipeline

### **Patient-to-Trial Matching**

1. **Data Retrieval**: Get patient medical history from database
2. **Text Processing**: Combine patient data into searchable text
3. **Embedding Generation**: Create MedCPT embedding for patient
4. **Hybrid Search**: 
   - Semantic search using FAISS index
   - Keyword search using BM25
   - Combine scores with configurable weights
5. **LLM Evaluation**: Use OpenAI GPT-4o Mini to evaluate match quality
6. **Result Ranking**: Sort by combined similarity scores
7. **Filtering**: Apply age, gender, phase filters
8. **Storage**: Save results to database

### **Trial-to-Patient Matching**

1. **Trial Data**: Get trial details and eligibility criteria
2. **Text Processing**: Combine trial information
3. **Embedding Generation**: Create trial embedding
4. **Patient Search**: Find matching patients using hybrid approach
5. **Eligibility Check**: Verify patient meets trial criteria
6. **Ranking**: Sort patients by match quality
7. **Results**: Return top matching patients

## 🗄️ Database Schema

### **Core Tables**
- `patient_medical_history`: Patient medical records
- `clinical_trial_details`: Clinical trial information
- `patient_trial_matches`: Patient-to-trial matching results
- `trial_patient_matches`: Trial-to-patient matching results

### **Automation Tables** (when `AUTOMATION_ENABLED=true`)
- `patient_processing_status`: Track patient processing status
- `trial_processing_status`: Track trial processing status
- `automation_processing_log`: Log automation batch processing

### **Stored Procedures**
- `get_patient_data_for_keywords()`: Retrieve patient data for processing
- `get_trial_data_for_matching()`: Retrieve trial data for processing
- `get_patients_needing_embeddings()`: Find patients requiring processing
- `get_trials_needing_embeddings()`: Find trials requiring processing

## 📊 Performance & Monitoring

### **Batch Processing**
- **Patient Batches**: Configurable batch sizes (default: 100)
- **Trial Batches**: Configurable batch sizes (default: 100)
- **Memory Management**: Efficient processing of large datasets
- **Error Recovery**: Graceful handling of batch failures

### **Progress Tracking**
- **Real-time Status**: Monitor automation progress
- **Error Reporting**: Detailed error logs and recovery
- **Performance Metrics**: Processing times and throughput
- **Resource Monitoring**: Memory and CPU usage

### **Logging**
- **Comprehensive Logs**: Detailed operation logs
- **Error Tracking**: Stack traces and error context
- **Performance Metrics**: Timing and resource usage
- **Audit Trail**: Complete processing history

## ⚙️ Configuration Options

### **OpenAI Configuration**
```env
OPENAI_API_KEY=your_api_key          # Required
OPENAI_MODEL=gpt-4o-mini             # Model to use
OPENAI_TEMPERATURE=0.2               # Response creativity (0-1)
OPENAI_MAX_TOKENS=4000               # Max response length
OPENAI_TIMEOUT=60                    # Request timeout (seconds)
OPENAI_MAX_RETRIES=3                 # Retry attempts
```

### **Automation Configuration**
```env
AUTOMATION_ENABLED=true              # Enable/disable automation
AUTOMATION_PATIENT_BATCH_SIZE=100    # Patients per batch
AUTOMATION_TRIAL_BATCH_SIZE=100      # Trials per batch
```

### **Matching Configuration**
```env
EMBEDDING_WEIGHT=0.7                 # Weight for semantic matching
BM25_WEIGHT=0.3                      # Weight for keyword matching
TOP_K_RESULTS=20                     # Number of top results to return
```

## 🧪 Testing

### **Integration Tests**
```bash
# Test OpenAI integration
python test_openai_integration.py

# Test automation system
python test_automation.py

# Test individual components
python -m services.patient_to_trial.keyword_generator
python -m services.patient_to_trial.patient_evaluator
python -m services.trial_to_patient.trial_evaluator
```

### **Manual Testing**
```python
# Test patient-to-trial matching
from services.patient_to_trial.patient_evaluator import PatientEvaluator
evaluator = PatientEvaluator()
results = evaluator.run_patient_trial_pipeline(patient_id=1)

# Test trial-to-patient matching
from services.trial_to_patient.trial_evaluator import TrialEvaluator
evaluator = TrialEvaluator()
results = evaluator.run_trial_matching_pipeline(trial_id="NCT12345678")
```

## 📅 Scheduled Tasks

### **Automation Mode Tasks**
- **Patient Embedding Generation**: Every 30 minutes
- **Trial Embedding Generation**: Every 30 minutes
- **Patient-Trial Matching**: Every 30 minutes
- **Trial-Patient Matching**: Every 30 minutes
- **Data Cleanup**: Daily at 2 AM

### **Manual Mode Tasks**
- **New Patient Processing**: Every 30 minutes
- **New Trial Processing**: Every 30 minutes
- **Trial Eligibility Updates**: Every hour
- **Data Cleanup**: Daily at 2 AM

## 🔍 Troubleshooting

### **Common Issues**

1. **OpenAI API Errors**
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   
   # Test connection
   python test_openai_integration.py
   ```

2. **Database Connection Issues**
   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Test connection
   python -c "from services.shared.database_utils import DatabaseUtils; db = DatabaseUtils(); print('Connected!' if db.test_connection() else 'Failed')"
   ```

3. **Memory Issues**
   ```bash
   # Reduce batch sizes
   export AUTOMATION_PATIENT_BATCH_SIZE=50
   export AUTOMATION_TRIAL_BATCH_SIZE=50
   ```

4. **Embedding Generation Failures**
   ```bash
   # Check MedCPT model availability
   python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('ncbi/MedCPT-Query-Encoder'); print('Model loaded successfully')"
   ```

### **Debug Mode**
```env
LOG_LEVEL=DEBUG
```

## 📚 Documentation

### **Additional Resources**
- `AUTOMATION_GUIDE.md`: Detailed automation setup guide
- `database/patient_trial_stored_procedures.sql`: Database schema
- `test_openai_integration.py`: OpenAI integration tests
- `test_automation.py`: Automation system tests

### **API Documentation**
- Patient-to-Trial API endpoints
- Trial-to-Patient API endpoints
- Automation status endpoints
- Health check endpoints

## 🚀 Deployment

### **Production Deployment**

1. **Environment Setup**
   ```bash
   # Create production environment
   python -m venv venv_prod
   source venv_prod/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   # Set production environment variables
   export AUTOMATION_ENABLED=true
   export LOG_LEVEL=INFO
   export OPENAI_API_KEY=your_production_key
   ```

3. **Process Management**
   ```bash
   # Use systemd or supervisor
   sudo systemctl enable clinical-trial-matcher
   sudo systemctl start clinical-trial-matcher
   ```

### **Docker Deployment**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 📈 Results & Analytics

### **Matching Results**
- **Patient-Trial Matches**: Stored in `patient_trial_matches` table
- **Trial-Patient Matches**: Stored in `trial_patient_matches` table
- **Evaluation Scores**: Confidence and priority scores
- **Detailed Reasoning**: LLM-generated explanations

### **Performance Metrics**
- **Processing Times**: Batch processing durations
- **Success Rates**: Matching success percentages
- **Error Rates**: Failure and retry statistics
- **Resource Usage**: Memory and CPU utilization

### **Monitoring Dashboard**
- **Real-time Status**: Current automation progress
- **Historical Data**: Processing trends and patterns
- **Error Analysis**: Common failure points
- **Performance Optimization**: Bottleneck identification

---

## 🤝 Support

For issues and questions:
1. Check the logs for detailed error information
2. Verify configuration settings
3. Test individual components
4. Monitor system resources
5. Review the troubleshooting guide

**System Status**: ✅ **Production Ready**  
**Last Updated**: January 2025  
**Version**: 2.0.0 (OpenAI Integration)