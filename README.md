# Task Scheduler for LLM Service

A standalone task scheduler service for processing LLM-based patient-trial matching tasks.

## Overview

This service runs independently to:
- Process patient-to-trial matching tasks
- Process trial-to-patient matching tasks  
- Update trial eligibility assessments
- Clean up old results and temporary data

## Features

- **Scheduled Processing**: Automatically processes pending tasks at regular intervals
- **LLM Integration**: Uses Google Gemini API for intelligent matching
- **Database Integration**: Connects to PostgreSQL database for data persistence
- **Robust Error Handling**: Continues processing even if individual tasks fail
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Configurable**: Easy configuration through environment variables

## Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   Create a `.env` file with your configuration:
   ```env
   # Database
   DATABASE_URL=postgresql+psycopg2://user:password@host:port/database
   
   # Gemini API
   GEMINI_API_KEY=your_gemini_api_key
   
   # Scheduler Settings
   SCHEDULER_INTERVAL_MINUTES=30
   MAX_CONCURRENT_TASKS=5
   TASK_TIMEOUT_SECONDS=300
   
   # Logging
   LOG_LEVEL=INFO
   LOG_FILE=task_scheduler.log
   ```

## Usage

### Running the Service

```bash
python main.py
```

The service will start and begin processing scheduled tasks automatically.

### Service Status

The service provides status information including:
- Running status
- Scheduled jobs and their next run times
- Service initialization status

## Scheduled Tasks

### 1. Patient-Trial Matching (Every 30 minutes)
- Processes pending patient-to-trial matching requests
- Uses LLM to analyze patient data against trial criteria
- Saves results to database for frontend consumption

### 2. Trial-Patient Matching (Every 30 minutes)
- Processes pending trial-to-patient matching requests
- Uses LLM to analyze trial criteria against patient data
- Saves results to database for frontend consumption

### 3. Trial Eligibility Updates (Every hour)
- Updates trial eligibility assessments
- Refreshes trial criteria and requirements
- Ensures data accuracy and consistency

### 4. Cleanup (Daily at 2 AM)
- Removes old results and temporary data
- Maintains database performance
- Prevents storage bloat

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `GEMINI_API_KEY` | - | Google Gemini API key |
| `SCHEDULER_INTERVAL_MINUTES` | 30 | Interval between task runs |
| `MAX_CONCURRENT_TASKS` | 5 | Maximum concurrent tasks |
| `TASK_TIMEOUT_SECONDS` | 300 | Task timeout in seconds |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FILE` | task_scheduler.log | Log file path |

### Service Configuration

The service can be configured through the `config.py` file:
- Database connection settings
- LLM API configuration
- Task scheduling parameters
- Logging configuration

## Architecture

```
Task Scheduler Service
├── main.py                 # Entry point
├── task_scheduler.py      # Main scheduler logic
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── database/              # Database services
│   ├── patient_db.py
│   ├── trial_database_service.py
│   └── stored_procedure_service.py
├── services/              # Business logic services
│   ├── trial_llm_service.py
│   ├── comprehensive_eligibility_service.py
│   ├── patient_to_trial_service.py
│   └── trial_to_patient_service.py
├── models/                # Data models
├── utils/                 # Utility functions
└── schemas.py             # Data schemas
```

## Monitoring

### Logs

The service generates detailed logs including:
- Task execution status
- Error messages and stack traces
- Performance metrics
- Database connection status

### Health Checks

Monitor the service health through:
- Log file monitoring
- Process status checking
- Database connection verification

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL configuration
   - Verify database server is running
   - Check network connectivity

2. **LLM API Errors**
   - Verify GEMINI_API_KEY is valid
   - Check API quota and limits
   - Monitor API response times

3. **Task Timeouts**
   - Increase TASK_TIMEOUT_SECONDS
   - Check system resources
   - Monitor task complexity

### Debug Mode

Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

## Development

### Adding New Tasks

1. Create task method in `task_scheduler.py`
2. Add job to `_add_scheduled_jobs()`
3. Implement database queries for pending tasks
4. Add error handling and logging

### Testing

Run individual task methods for testing:
```python
# Test patient-trial matching
await scheduler.process_patient_trial_matches()

# Test trial eligibility update
await scheduler.update_trial_eligibility()
```

## Deployment

### Production Deployment

1. **Use process manager** (e.g., systemd, supervisor)
2. **Set up monitoring** and alerting
3. **Configure log rotation**
4. **Set up health checks**
5. **Use environment-specific configuration**

### Docker Deployment

Create a Dockerfile for containerized deployment:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Support

For issues and questions:
1. Check the logs for error details
2. Verify configuration settings
3. Test database connectivity
4. Monitor system resources
