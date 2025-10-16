# Windows Task Scheduler for Clinical Trials Data Fetching

A robust Python-based scheduler that automatically fetches clinical trials data from ClinicalTrials.gov API and populates a PostgreSQL database. Designed specifically for Windows Task Scheduler integration to run automated data collection tasks.

## 🎯 Overview

This application is part of the InsightsEdge UI system and provides automated data collection for clinical trials information. It fetches trials data based on specific criteria (colorectal cancer conditions, geographic location, trial status) and stores the information in a PostgreSQL database for further analysis.

## ✨ Features

- **Automated Data Collection**: Fetches clinical trials from ClinicalTrials.gov API v2
- **Geographic Filtering**: Focuses on trials within a specified radius of San Francisco
- **Condition-Specific Search**: Targets colorectal cancer-related trials
- **Status Filtering**: Collects trials with specific statuses (RECRUITING, AVAILABLE, ENROLLING_BY_INVITATION)
- **Database Integration**: Stores data in PostgreSQL with proper schema
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Windows Integration**: Designed for Windows Task Scheduler automation
- **Error Handling**: Robust error handling with retry mechanisms
- **Duplicate Prevention**: Only inserts new trials, skips existing ones

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Windows       │    │   Python         │    │   PostgreSQL    │
│   Task          │───▶│   Scheduler      │───▶│   Database      │
│   Scheduler     │    │   Application    │    │   (InsightsEdge)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ ClinicalTrials   │
                       │ .gov API v2      │
                       └──────────────────┘
```

## 📋 Prerequisites

- **Python 3.11+**
- **PostgreSQL Database** (InsightsEdge schema)
- **Windows Operating System**
- **Internet Connection** (for API access)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Task-scheduler-for-llm
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# Optional: Override default settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 5. Database Setup

Ensure your PostgreSQL database has the `insightsedge.clinical_trial_details` table with the following structure:

```sql
CREATE SCHEMA IF NOT EXISTS insightsedge;

CREATE TABLE insightsedge.clinical_trial_details (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(50) UNIQUE NOT NULL,
    study_title TEXT,
    brief_title TEXT,
    official_title TEXT,
    overall_status VARCHAR(100),
    study_phase VARCHAR(100),
    start_date DATE,
    completion_date DATE,
    conditions JSONB,
    interventions JSONB,
    brief_summary TEXT,
    detailed_description TEXT,
    enrollment_count INTEGER,
    study_type VARCHAR(100),
    sex VARCHAR(50),
    minimum_age VARCHAR(50),
    maximum_age VARCHAR(50),
    eligibility_criteria TEXT,
    inclusion_criteria JSONB,
    exclusion_criteria JSONB,
    locations JSONB,
    primary_outcomes JSONB,
    secondary_outcomes JSONB,
    lead_sponsor_name VARCHAR(500),
    source_api VARCHAR(100),
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚙️ Configuration

The application uses `config.py` for configuration management. Key settings include:

### API Configuration
- **API Base URL**: ClinicalTrials.gov API v2 endpoint
- **Target Statuses**: Trial statuses to collect
- **Geographic Filter**: San Francisco area with configurable radius
- **Condition Filters**: Colorectal cancer-related conditions

### Database Configuration
- **Connection Settings**: Host, port, database name, credentials
- **Batch Processing**: Configurable batch sizes for data insertion

### Rate Limiting
- **Request Delay**: Delay between API requests (default: 1 second)
- **Timeout Settings**: API request timeout (default: 30 seconds)

## 🎮 Usage

### Manual Execution

```bash
# Activate virtual environment
venv\Scripts\activate

# Run the scheduler
python trial_scheduler.py
```

### Windows Task Scheduler Setup

1. **Open Task Scheduler** (taskschd.msc)

2. **Create Basic Task**
   - Name: "Clinical Trials Data Collection"
   - Description: "Automated collection of clinical trials data"

3. **Set Trigger**
   - Choose frequency (Daily, Weekly, Monthly)
   - Set start time and date

4. **Set Action**
   - Action: "Start a program"
   - Program/script: `C:\path\to\your\project\run_scheduler.bat`
   - Start in: `C:\path\to\your\project`

5. **Configure Settings**
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges
   - ✅ Configure for: Windows 10/11

### PowerShell Script Execution

```powershell
# Run using PowerShell script
.\run_scheduler.ps1
```

### Batch File Execution

```batch
# Run using batch file
run_scheduler.bat
```

## 📊 Data Collection Process

1. **API Connection**: Establishes connection to ClinicalTrials.gov API v2
2. **Condition Iteration**: Searches for each colorectal cancer condition
3. **Status Filtering**: Collects trials with target statuses
4. **Geographic Filtering**: Filters trials within specified radius
5. **Data Processing**: Extracts and formats trial information
6. **Database Storage**: Inserts new trials into PostgreSQL database
7. **Logging**: Records execution statistics and any errors

## 📈 Monitoring and Logging

### Log Files
- **Location**: `logs/trial_scheduler.log`
- **Format**: Timestamp, logger name, level, message
- **Rotation**: Automatic log rotation (configure in logging settings)

### Execution Statistics
- Total trials fetched
- Total trials saved
- Execution time
- Error count
- Execution ID for tracking

### Sample Log Output
```
2024-01-15 10:30:00 - __main__ - INFO - Starting Windows Trial Scheduler - Execution ID: exec_20240115_103000
2024-01-15 10:30:01 - __main__ - INFO - Database connection established successfully
2024-01-15 10:30:02 - __main__ - INFO - Fetching RECRUITING trials for 'metastatic colorectal cancer' in San Francisco...
2024-01-15 10:30:05 - __main__ - INFO - API returned 25 RECRUITING studies on page 1 for condition 'metastatic colorectal cancer'
2024-01-15 10:30:08 - __main__ - INFO - Processed 25 RECRUITING trials from page 1 for condition 'metastatic colorectal cancer'
2024-01-15 10:35:00 - __main__ - INFO - Database population completed - 150 trials saved
2024-01-15 10:35:01 - __main__ - INFO - EXECUTION SUMMARY
2024-01-15 10:35:01 - __main__ - INFO - Execution Time: 301.25 seconds
2024-01-15 10:35:01 - __main__ - INFO - Total Trials Fetched: 150
2024-01-15 10:35:01 - __main__ - INFO - Total Trials Saved: 150
```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Failed
```
Error: Database connection failed: connection refused
```
**Solution**: Verify database credentials and network connectivity

#### API Request Timeout
```
Error: API request failed: timeout
```
**Solution**: Check internet connection and increase timeout settings

#### Permission Denied
```
Error: Permission denied when creating log file
```
**Solution**: Ensure write permissions for logs directory

### Debug Mode

Enable debug logging by setting environment variable:
```bash
set LOG_LEVEL=DEBUG
python trial_scheduler.py
```

### Test Configuration

Run configuration validation:
```bash
python test_setup.py
```

## 📁 Project Structure

```
Task-scheduler-for-llm/
├── config.py                 # Configuration management
├── trial_scheduler.py        # Main scheduler application
├── test_setup.py            # Configuration testing
├── requirements.txt         # Python dependencies
├── run_scheduler.bat        # Windows batch execution script
├── run_scheduler.ps1        # PowerShell execution script
├── env_template.txt         # Environment variables template
├── logs/                    # Log files directory
│   └── trial_scheduler.log  # Main log file
├── venv/                    # Virtual environment
└── README.md               # This file
```

## 🔒 Security Considerations

- **Database Credentials**: Store in environment variables, never in code
- **API Keys**: No API keys required for ClinicalTrials.gov
- **Network Security**: Ensure secure database connections
- **Log Security**: Avoid logging sensitive information

## 🚀 Performance Optimization

### Recommended Settings

- **Production**: `REQUEST_DELAY = 2.0`, `MAX_PAGES = 5`
- **Development**: `REQUEST_DELAY = 0.5`, `MAX_PAGES = 50`
- **Testing**: `REQUEST_DELAY = 0.1`, `MAX_PAGES = 1`

### Monitoring Performance

- Monitor execution time trends
- Track API response times
- Monitor database insertion rates
- Watch for memory usage patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the InsightsEdge UI system. Please refer to your organization's licensing terms.

## 📞 Support

For technical support or questions:
- Check the logs for error details
- Review the configuration settings
- Contact your system administrator
- Refer to the ClinicalTrials.gov API documentation

## 🔄 Version History

- **v1.0.0**: Initial release with basic functionality
- **v1.1.0**: Added geographic filtering and condition-specific search
- **v1.2.0**: Enhanced error handling and logging
- **v1.3.0**: Added Windows Task Scheduler integration scripts

---

**Note**: This application is designed for automated data collection and should be run as a scheduled task rather than manually for production use.