# Clinical Trial Matching System - Task Scheduler

A sophisticated **AI-powered Clinical Trial Matching System** that uses advanced machine learning techniques to match patients with suitable clinical trials and vice versa. The system combines traditional database queries with modern AI techniques including embeddings, vector search, and LLM processing.

## 🚀 **Key Features**

### **🤖 Full Automation Support**
- **Complete Processing**: Processes ALL patients and ALL trials in your database
- **Comprehensive Matching**: Creates complete patient-trial matching matrix
- **Batch Processing**: Handles large datasets efficiently with configurable batch sizes
- **Real-time Monitoring**: Progress tracking and status monitoring

### **🧠 Advanced AI/ML Integration**
- **MedCPT Embeddings**: Medical-specific embeddings for clinical text understanding
- **Hybrid Matching**: Combines semantic (FAISS) and keyword (BM25) search
- **Google Gemini Integration**: LLM-powered evaluation and keyword generation
- **Vector Search**: Fast similarity search using FAISS indices

### **📊 Dual Processing Modes**
- **Automation Mode**: Processes entire database automatically
- **Manual Mode**: Incremental processing for new patients/trials
- **Scheduled Tasks**: Automated processing every 30 minutes
- **Flexible Configuration**: Easy switching between modes

## 🏗️ **System Architecture**

```
Clinical Trial Matching System
├── 🤖 Automation Engine
│   ├── Batch Processing (ALL patients & trials)
│   ├── Progress Tracking & Monitoring
│   └── Error Handling & Recovery
├── 🧠 AI/ML Pipeline
│   ├── MedCPT Embeddings (Medical Text Understanding)
│   ├── FAISS Vector Search (Fast Similarity)
│   ├── BM25 Keyword Matching (Text Search)
│   └── Google Gemini LLM (Evaluation & Keywords)
├── 🗄️ Database Layer
│   ├── PostgreSQL with Custom Schema
│   ├── Stored Procedures (Optimized Queries)
│   ├── Automation Tables (Results Storage)
│   └── Processing Status Tracking
└── ⚡ Task Scheduler
    ├── APScheduler (Background Processing)
    ├── Configurable Intervals
    ├── Concurrent Task Management
    └── Health Monitoring
```

## 🚀 **Quick Start**

### **1. Environment Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Database Setup**
```bash
# Create automation tables
psql -h your_host -U your_user -d your_database -f database/automation_tables.sql
```

### **3. Configuration**
Create a `.env` file:
```env
# Database
DATABASE_URL=postgresql+psycopg2://user:password@host:port/database

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Automation Settings
AUTOMATION_ENABLED=true
AUTOMATION_PATIENT_BATCH_SIZE=100
AUTOMATION_TRIAL_BATCH_SIZE=100

# Scheduler Settings
SCHEDULER_INTERVAL_MINUTES=30
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=task_scheduler.log
```

### **4. Run the System**
```bash
# Start with automation enabled
export AUTOMATION_ENABLED=true
python main.py
```

## 🔧 **Automation Modes**

### **🤖 Full Automation** (`AUTOMATION_ENABLED=true`)
- **Processes ALL patients** in your database
- **Processes ALL trials** in your database
- **Generates embeddings** for every patient and trial
- **Creates comprehensive matching matrix** (every patient ↔ every trial)
- **Stores results in database** for fast retrieval
- **Runs automatically** every 30 minutes

### **👤 Manual Mode** (`AUTOMATION_ENABLED=false`)
- Processes only **new patients/trials** that haven't been processed
- Limited batch processing (10 items per run)
- Suitable for incremental updates
- Manual control over processing

## 📊 **Processing Pipeline**

### **Patient Processing**
1. **Data Retrieval**: Get patient medical history from database
2. **Text Processing**: Combine patient data into searchable text
3. **Embedding Generation**: Create MedCPT embedding for patient
4. **Keyword Generation**: Extract relevant medical keywords using LLM
5. **Hybrid Matching**: 
   - Semantic search using FAISS index
   - Keyword search using BM25
   - Combine scores with configurable weights
6. **LLM Evaluation**: Use Gemini to evaluate match quality
7. **Result Storage**: Save results to database

### **Trial Processing**
1. **Trial Data**: Get trial details and eligibility criteria
2. **Text Processing**: Combine trial information
3. **Embedding Generation**: Create trial embedding
4. **Patient Search**: Find matching patients using hybrid approach
5. **Eligibility Check**: Verify patient meets trial criteria
6. **Ranking**: Sort patients by match quality
7. **Results**: Store comprehensive matching results

## 🗄️ **Database Schema**

### **Core Tables**
- `patient_medical_history` - Patient medical records
- `clinical_trial_details` - Clinical trial information

### **Automation Tables**
- `patient_trial_matches` - Patient-to-trial matching results
- `trial_patient_matches` - Trial-to-patient matching results
- `automation_processing_log` - Processing batches and status
- `patient_processing_status` - Patient processing tracking
- `trial_processing_status` - Trial processing tracking

### **Query Examples**
```sql
-- Get top matches for a patient
SELECT trial_id, hybrid_score, embedding_score, bm25_score, match_rank
FROM insightsedge.patient_trial_matches
WHERE patient_id = 123
ORDER BY hybrid_score DESC
LIMIT 10;

-- Get top matches for a trial
SELECT patient_id, hybrid_score, embedding_score, bm25_score, match_rank
FROM insightsedge.trial_patient_matches
WHERE trial_id = 'NCT12345678'
ORDER BY hybrid_score DESC
LIMIT 10;

-- Check processing status
SELECT 
    COUNT(*) as total_patients,
    SUM(CASE WHEN embedding_generated THEN 1 ELSE 0 END) as with_embeddings,
    SUM(CASE WHEN keywords_generated THEN 1 ELSE 0 END) as with_keywords
FROM insightsedge.patient_processing_status;
```

## 📈 **Performance & Monitoring**

### **Batch Processing**
- Patients processed in configurable batches (default: 100)
- Trials processed in configurable batches (default: 100)
- Progress tracked and logged in real-time
- Individual failures don't stop batch processing

### **Memory Management**
- Embeddings cached in `persist/embeddings/` directory
- FAISS indices for fast similarity search
- Batch processing prevents memory overflow
- Automatic cleanup of old results

### **Monitoring**
```bash
# Check automation status
python -c "
from services.automation_service import AutomationService
service = AutomationService()
print(service.get_automation_status())
"

# Test the system
python test_automation.py
```

## 🔍 **Configuration Options**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTOMATION_ENABLED` | false | Enable/disable full automation |
| `AUTOMATION_PATIENT_BATCH_SIZE` | 100 | Batch size for patient processing |
| `AUTOMATION_TRIAL_BATCH_SIZE` | 100 | Batch size for trial processing |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `GEMINI_API_KEY` | - | Google Gemini API key |
| `SCHEDULER_INTERVAL_MINUTES` | 30 | Interval between task runs |
| `MAX_CONCURRENT_TASKS` | 5 | Maximum concurrent tasks |
| `TASK_TIMEOUT_SECONDS` | 300 | Task timeout in seconds |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FILE` | task_scheduler.log | Log file path |

### **Hybrid Matching Weights**
- **Embedding Score**: 60% (semantic similarity)
- **BM25 Score**: 40% (keyword matching)
- **Combined Score**: `hybrid_score = embedding_score * 0.6 + bm25_score * 0.4`

## 🧪 **Testing**

### **Test Automation System**
```bash
# Run comprehensive tests
python test_automation.py

# Test specific components
python -c "
from services.automation_service import AutomationService
import asyncio

async def test():
    service = AutomationService()
    results = await service.run_full_automation()
    print(f'Automation Status: {results[\"status\"]}')

asyncio.run(test())
"
```

### **Manual Testing**
```bash
# Test patient-to-trial pipeline
python patient_to_trial_pipeline.py

# Test trial-to-patient pipeline
python trial_to_patient_pipeline.py
```

## 📋 **Scheduled Tasks**

### **1. Patient-Trial Matching** (Every 30 minutes)
- **Automation Mode**: Processes ALL patients against ALL trials
- **Manual Mode**: Processes only new patients
- Uses hybrid matching (embeddings + BM25)
- Stores top 50 matches per patient

### **2. Trial-Patient Matching** (Every 30 minutes)
- **Automation Mode**: Processes ALL trials against ALL patients
- **Manual Mode**: Processes only new trials
- Uses hybrid matching (embeddings + BM25)
- Stores top 50 matches per trial

### **3. Trial Eligibility Updates** (Every hour)
- Updates trial eligibility assessments
- Refreshes trial criteria and requirements
- Ensures data accuracy and consistency

### **4. Cleanup** (Daily at 2 AM)
- Removes old results and temporary data
- Maintains database performance
- Prevents storage bloat

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Automation Not Starting**
   ```bash
   # Check configuration
   echo $AUTOMATION_ENABLED
   
   # Check database connection
   python -c "from services.shared.database_utils import DatabaseUtils; db = DatabaseUtils(); print('DB OK' if db.get_connection() else 'DB Error')"
   ```

2. **Processing Failures**
   ```sql
   -- Check processing errors
   SELECT patient_id, processing_errors 
   FROM insightsedge.patient_processing_status 
   WHERE processing_errors IS NOT NULL;
   ```

3. **Memory Issues**
   ```bash
   # Reduce batch sizes
   export AUTOMATION_PATIENT_BATCH_SIZE=50
   export AUTOMATION_TRIAL_BATCH_SIZE=50
   ```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py
```

## 📚 **Documentation**

- **[Automation Guide](AUTOMATION_GUIDE.md)** - Comprehensive automation documentation
- **[Database Schema](database/)** - Database structure and stored procedures
- **[Service Architecture](services/)** - Service layer documentation
- **[Test Suite](test_automation.py)** - Testing and validation

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Use process manager (systemd example)
sudo systemctl enable clinical-trial-matcher
sudo systemctl start clinical-trial-matcher

# Monitor logs
tail -f task_scheduler.log
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

## 📊 **Results & Analytics**

### **Matching Results**
- **Patient-Trial Matches**: Stored in `patient_trial_matches` table
- **Trial-Patient Matches**: Stored in `trial_patient_matches` table
- **Hybrid Scores**: Combined semantic and keyword scores
- **LLM Evaluations**: Detailed clinical reasoning for matches

### **Performance Metrics**
- **Processing Time**: ~2-3 minutes per patient/trial
- **Match Quality**: Hybrid scores 4.7-5.0 for relevant matches
- **Coverage**: Complete database processing
- **Accuracy**: LLM evaluation provides detailed clinical reasoning

## 🤝 **Support**

For issues and questions:
1. Check logs in `task_scheduler.log`
2. Review database processing status tables
3. Test with `test_automation.py`
4. Verify configuration settings
5. Check the [Automation Guide](AUTOMATION_GUIDE.md)

---

**🎯 This system provides comprehensive clinical trial matching capabilities, processing your entire patient and trial database to create a complete matching matrix using advanced AI/ML techniques.**
