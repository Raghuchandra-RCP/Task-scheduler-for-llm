# Clinical Trial Matching System - Automation Guide

## Overview

The Clinical Trial Matching System now supports **full automation** that processes ALL patients and ALL trials in your database, creating a comprehensive matching matrix.

## Automation Modes

### 1. **Automation Enabled** (`AUTOMATION_ENABLED=true`)
- Processes **ALL patients** and **ALL trials** in the database
- Generates embeddings for every patient and trial
- Creates comprehensive patient-trial and trial-patient matching results
- Stores all results in database tables for fast retrieval
- Runs on scheduled intervals (every 30 minutes by default)

### 2. **Manual Mode** (`AUTOMATION_ENABLED=false`)
- Processes only **new patients/trials** that haven't been processed yet
- Limited batch processing (10 items per run)
- Suitable for incremental updates

## Configuration

### Environment Variables

```bash
# Enable/disable automation
AUTOMATION_ENABLED=true

# Batch sizes for automation processing
AUTOMATION_PATIENT_BATCH_SIZE=100
AUTOMATION_TRIAL_BATCH_SIZE=100

# Scheduler settings
SCHEDULER_INTERVAL_MINUTES=30
MAX_CONCURRENT_TASKS=5
```

### Configuration File (`config.py`)

```python
AUTOMATION_ENABLED = os.getenv("AUTOMATION_ENABLED", "false").lower() == "true"
AUTOMATION_PATIENT_BATCH_SIZE = int(os.getenv("AUTOMATION_PATIENT_BATCH_SIZE", "100"))
AUTOMATION_TRIAL_BATCH_SIZE = int(os.getenv("AUTOMATION_TRIAL_BATCH_SIZE", "100"))
```

## Database Setup

### 1. Create Automation Tables

Run the SQL script to create required tables:

```bash
psql -h your_host -U your_user -d your_database -f database/automation_tables.sql
```

### 2. Tables Created

- `patient_trial_matches` - Stores patient-to-trial matching results
- `trial_patient_matches` - Stores trial-to-patient matching results  
- `automation_processing_log` - Tracks processing batches and status
- `patient_processing_status` - Tracks patient processing status
- `trial_processing_status` - Tracks trial processing status

## Usage

### 1. Start the Task Scheduler

```bash
# Set automation enabled
export AUTOMATION_ENABLED=true

# Start the scheduler
python main.py
```

### 2. Monitor Automation Status

The scheduler provides status information including:
- Automation enabled/disabled status
- Recent processing batches
- Processing progress and errors
- Service initialization status

### 3. Test Automation

```bash
# Run the test script
python test_automation.py
```

## Automation Process Flow

### When `AUTOMATION_ENABLED=true`:

1. **Patient Embedding Generation**
   - Gets ALL patients from database
   - Generates MedCPT embeddings for each patient
   - Updates processing status

2. **Trial Embedding Generation**
   - Gets ALL trials from database
   - Generates MedCPT embeddings for each trial
   - Updates processing status

3. **Patient Keyword Generation** (if LLM enabled)
   - Generates medical keywords for all patients
   - Uses Google Gemini API

4. **Patient-to-Trial Matching**
   - For EVERY patient: finds matches against ALL trials
   - Uses hybrid scoring (embeddings + BM25)
   - Stores top 50 matches per patient

5. **Trial-to-Patient Matching**
   - For EVERY trial: finds matches against ALL patients
   - Uses hybrid scoring (embeddings + BM25)
   - Stores top 50 matches per trial

## Results Storage

### Database Tables

**Patient-Trial Matches:**
```sql
SELECT patient_id, trial_id, hybrid_score, embedding_score, bm25_score, match_rank
FROM insightsedge.patient_trial_matches
WHERE patient_id = 123
ORDER BY hybrid_score DESC;
```

**Trial-Patient Matches:**
```sql
SELECT trial_id, patient_id, hybrid_score, embedding_score, bm25_score, match_rank
FROM insightsedge.trial_patient_matches
WHERE trial_id = 'NCT12345678'
ORDER BY hybrid_score DESC;
```

### Processing Logs

```sql
SELECT batch_id, processing_type, status, total_items, processed_items, failed_items
FROM insightsedge.automation_processing_log
ORDER BY started_at DESC;
```

## Performance Considerations

### Batch Processing
- Patients processed in batches of 100 (configurable)
- Trials processed in batches of 100 (configurable)
- Progress tracked and logged

### Memory Management
- Embeddings cached in `persist/embeddings/` directory
- FAISS indices for fast similarity search
- Batch processing prevents memory overflow

### Error Handling
- Individual failures don't stop batch processing
- Errors logged in processing status tables
- Failed items tracked separately

## Monitoring

### Log Files
- `task_scheduler.log` - Main scheduler logs
- `results/automation_results_*.json` - Detailed automation results

### Database Monitoring
```sql
-- Check processing status
SELECT 
    COUNT(*) as total_patients,
    SUM(CASE WHEN embedding_generated THEN 1 ELSE 0 END) as with_embeddings,
    SUM(CASE WHEN keywords_generated THEN 1 ELSE 0 END) as with_keywords
FROM insightsedge.patient_processing_status;

-- Check recent processing
SELECT processing_type, status, COUNT(*) as count
FROM insightsedge.automation_processing_log
WHERE started_at > NOW() - INTERVAL '24 hours'
GROUP BY processing_type, status;
```

## Troubleshooting

### Common Issues

1. **Automation Not Starting**
   - Check `AUTOMATION_ENABLED=true` in environment
   - Verify database connection
   - Check service initialization logs

2. **Processing Failures**
   - Check `processing_errors` in status tables
   - Verify API keys (Gemini API)
   - Check disk space for embeddings

3. **Memory Issues**
   - Reduce batch sizes in config
   - Monitor system memory usage
   - Check for memory leaks in logs

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py
```

## API Integration

The automation system can be integrated with REST APIs:

```python
# Get automation status
GET /api/automation/status

# Trigger manual automation run
POST /api/automation/run

# Get matching results
GET /api/matches/patient/{patient_id}
GET /api/matches/trial/{trial_id}
```

## Best Practices

1. **Start Small**: Test with automation disabled first
2. **Monitor Resources**: Watch CPU, memory, and disk usage
3. **Regular Cleanup**: Old results are cleaned up automatically
4. **Backup Data**: Regular database backups recommended
5. **API Rate Limits**: Monitor Gemini API usage

## Support

For issues or questions:
1. Check logs in `task_scheduler.log`
2. Review database processing status tables
3. Test with `test_automation.py`
4. Verify configuration settings
