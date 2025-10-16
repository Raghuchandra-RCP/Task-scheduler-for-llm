# Evaluation Results Database Implementation

This folder contains the database implementation for storing LLM evaluation results from the Clinical Trial Matching System.

## 📁 Folder Structure

```
evaluation_results_db/
├── sql/                           # SQL schema files
│   └── 01_create_evaluation_tables.sql
├── utils/                         # Database utility functions
│   └── evaluation_results_db.py
├── tests/                         # Test files (to be added)
└── README.md                      # This file
```

## 🗄️ Database Tables

### 1. `patient_to_trial_evaluations`
Stores results when evaluating trials for a specific patient.

**Key Columns:**
- `patient_id`, `patient_mrn` - Patient identifiers
- `evaluation_timestamp` - When the evaluation was performed
- `total_trials_found`, `total_trials_evaluated` - Counts
- `evaluation_method` - 'batch' or 'individual'
- `eligible_trials_count`, `not_eligible_trials_count`, `need_more_info_trials_count` - Results summary
- `average_confidence_score` - Average confidence across all evaluations
- `trial_evaluations` - JSONB array of individual trial evaluations
- `batch_summary` - JSONB object with batch-level statistics

### 2. `trial_to_patient_evaluations`
Stores results when evaluating patients for a specific trial.

**Key Columns:**
- `trial_id`, `trial_title` - Trial identifiers
- `evaluation_timestamp` - When the evaluation was performed
- `total_patients_found`, `total_patients_evaluated` - Counts
- `evaluation_method` - 'batch' or 'individual'
- `eligible_patients_count`, `not_eligible_patients_count`, `need_more_info_patients_count` - Results summary
- `average_confidence_score` - Average confidence across all evaluations
- `patient_evaluations` - JSONB array of individual patient evaluations
- `batch_summary` - JSONB object with batch-level statistics

## 🚀 Usage

### 1. Create Tables
```bash
# Run the SQL script to create tables
psql -d your_database -f sql/01_create_evaluation_tables.sql
```

### 2. Use Database Utilities
```python
from evaluation_results_db.utils.evaluation_results_db import EvaluationResultsDB

# Initialize database connection
db = EvaluationResultsDB()

# Save patient-to-trial evaluation results
evaluation_id = db.save_patient_to_trial_evaluation(evaluation_data)

# Save trial-to-patient evaluation results
evaluation_id = db.save_trial_to_patient_evaluation(evaluation_data)

# Get evaluation history
patient_history = db.get_patient_evaluation_history(patient_id=1, limit=10)
trial_history = db.get_trial_evaluation_history(trial_id="NCT04929223", limit=10)

# Get overall statistics
stats = db.get_evaluation_statistics()
```

## 📊 JSONB Structure Examples

### Individual Trial Evaluation (Patient-to-Trial)
```json
{
  "trial_id": "NCT04929223",
  "trial_title": "A Phase I/Ib Global...",
  "condition": "Metastatic Colorectal Cancer",
  "phase": "PHASE1",
  "eligibility_status": "ELIGIBLE",
  "confidence_score": 85,
  "priority_score": 90,
  "reasoning": "Patient meets all inclusion criteria...",
  "key_criteria_met": ["criteria1", "criteria2"],
  "key_criteria_missed": ["criteria3"],
  "recommendations": "Proceed with enrollment",
  "hybrid_score": 4.91
}
```

### Individual Patient Evaluation (Trial-to-Patient)
```json
{
  "patient_id": 1,
  "mrn": "70906771",
  "age": 51,
  "gender": "Male",
  "oncologist": "Dr. Sarah Mitchell, MD",
  "eligibility_status": "ELIGIBLE",
  "confidence_score": 85,
  "priority_score": 90,
  "reasoning": "Patient meets all inclusion criteria...",
  "key_criteria_met": ["criteria1", "criteria2"],
  "key_criteria_missed": ["criteria3"],
  "recommendations": "Proceed with enrollment",
  "hybrid_score": 4.91
}
```

### Batch Summary
```json
{
  "total_trials_evaluated": 20,
  "eligible_count": 5,
  "not_eligible_count": 10,
  "need_more_info_count": 5,
  "average_confidence": 78.5,
  "top_recommendations": [
    "Trial 1 - Best match due to...",
    "Trial 2 - Good alternative because...",
    "Trial 3 - Consider if..."
  ],
  "generated_at": "2025-10-16T15:12:30.815778"
}
```

## 🔍 Indexes and Performance

The tables include optimized indexes for:
- Patient ID lookups
- Trial ID lookups
- Timestamp-based queries
- Evaluation counts for analytics

## 🔄 Triggers

- Auto-update `updated_at` timestamp on record modifications
- Data validation constraints for data integrity

## 📈 Analytics Queries

### Top Performing Patients (Most Eligible Trials)
```sql
SELECT 
    patient_mrn,
    COUNT(*) as total_evaluations,
    SUM(eligible_trials_count) as total_eligible_trials,
    AVG(average_confidence_score) as avg_confidence
FROM insightsedge.patient_to_trial_evaluations
GROUP BY patient_mrn
ORDER BY total_eligible_trials DESC;
```

### Top Performing Trials (Most Eligible Patients)
```sql
SELECT 
    trial_id,
    trial_title,
    COUNT(*) as total_evaluations,
    SUM(eligible_patients_count) as total_eligible_patients,
    AVG(average_confidence_score) as avg_confidence
FROM insightsedge.trial_to_patient_evaluations
GROUP BY trial_id, trial_title
ORDER BY total_eligible_patients DESC;
```

### Evaluation Trends Over Time
```sql
SELECT 
    DATE(evaluation_timestamp) as evaluation_date,
    COUNT(*) as daily_evaluations,
    SUM(eligible_trials_count) as daily_eligible_trials
FROM insightsedge.patient_to_trial_evaluations
GROUP BY DATE(evaluation_timestamp)
ORDER BY evaluation_date DESC;
```

## 🧪 Testing

Run tests to verify the implementation:
```bash
python evaluation_results_db/utils/evaluation_results_db.py
```

## 🔧 Integration

To integrate with existing evaluators:

1. Import the database utility
2. Call save methods after evaluation completion
3. Handle database errors gracefully
4. Log successful saves for monitoring

## 📝 Notes

- All timestamps are stored in UTC
- JSONB fields allow for flexible querying and indexing
- Foreign key relationships maintain data integrity
- Batch processing results are preserved for analytics
- Individual evaluation details are stored for detailed analysis
