-- Automation Tables for Clinical Trial Matching System
-- These tables store comprehensive matching results for automation

-- Table to store patient-trial matching results
CREATE TABLE IF NOT EXISTS insightsedge.patient_trial_matches (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    patient_mrn VARCHAR(50) NOT NULL,
    trial_id VARCHAR(50) NOT NULL,
    hybrid_score DECIMAL(10,4) NOT NULL,
    embedding_score DECIMAL(10,4) NOT NULL,
    bm25_score DECIMAL(10,4) NOT NULL,
    llm_evaluation_score DECIMAL(10,4),
    llm_evaluation_text TEXT,
    match_rank INTEGER,
    processing_batch_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT fk_patient_trial_matches_patient FOREIGN KEY (patient_id) REFERENCES insightsedge.patient_medical_history(id),
    UNIQUE(patient_id, trial_id, processing_batch_id)
);

-- Table to store trial-patient matching results (reverse direction)
CREATE TABLE IF NOT EXISTS insightsedge.trial_patient_matches (
    id SERIAL PRIMARY KEY,
    trial_id VARCHAR(50) NOT NULL,
    patient_id INTEGER NOT NULL,
    patient_mrn VARCHAR(50) NOT NULL,
    hybrid_score DECIMAL(10,4) NOT NULL,
    embedding_score DECIMAL(10,4) NOT NULL,
    bm25_score DECIMAL(10,4) NOT NULL,
    llm_evaluation_score DECIMAL(10,4),
    llm_evaluation_text TEXT,
    match_rank INTEGER,
    processing_batch_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT fk_trial_patient_matches_patient FOREIGN KEY (patient_id) REFERENCES insightsedge.patient_medical_history(id),
    UNIQUE(trial_id, patient_id, processing_batch_id)
);

-- Table to track processing status and batches
CREATE TABLE IF NOT EXISTS insightsedge.automation_processing_log (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100) NOT NULL,
    processing_type VARCHAR(50) NOT NULL, -- 'patient_embedding', 'trial_embedding', 'patient_trial_matching', 'trial_patient_matching'
    total_items INTEGER NOT NULL,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    
    UNIQUE(batch_id, processing_type)
);

-- Table to store patient processing status
CREATE TABLE IF NOT EXISTS insightsedge.patient_processing_status (
    patient_id INTEGER PRIMARY KEY,
    embedding_generated BOOLEAN DEFAULT FALSE,
    keywords_generated BOOLEAN DEFAULT FALSE,
    last_embedding_update TIMESTAMP,
    last_keyword_update TIMESTAMP,
    processing_errors TEXT,
    
    CONSTRAINT fk_patient_processing_status FOREIGN KEY (patient_id) REFERENCES insightsedge.patient_medical_history(id)
);

-- Table to store trial processing status
CREATE TABLE IF NOT EXISTS insightsedge.trial_processing_status (
    trial_id VARCHAR(50) PRIMARY KEY,
    embedding_generated BOOLEAN DEFAULT FALSE,
    last_embedding_update TIMESTAMP,
    processing_errors TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patient_trial_matches_patient_id ON insightsedge.patient_trial_matches(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_trial_matches_trial_id ON insightsedge.patient_trial_matches(trial_id);
CREATE INDEX IF NOT EXISTS idx_patient_trial_matches_score ON insightsedge.patient_trial_matches(hybrid_score DESC);
CREATE INDEX IF NOT EXISTS idx_patient_trial_matches_batch ON insightsedge.patient_trial_matches(processing_batch_id);

CREATE INDEX IF NOT EXISTS idx_trial_patient_matches_trial_id ON insightsedge.trial_patient_matches(trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_patient_matches_patient_id ON insightsedge.trial_patient_matches(patient_id);
CREATE INDEX IF NOT EXISTS idx_trial_patient_matches_score ON insightsedge.trial_patient_matches(hybrid_score DESC);
CREATE INDEX IF NOT EXISTS idx_trial_patient_matches_batch ON insightsedge.trial_patient_matches(processing_batch_id);

CREATE INDEX IF NOT EXISTS idx_automation_log_batch ON insightsedge.automation_processing_log(batch_id);
CREATE INDEX IF NOT EXISTS idx_automation_log_status ON insightsedge.automation_processing_log(status);
CREATE INDEX IF NOT EXISTS idx_automation_log_type ON insightsedge.automation_processing_log(processing_type);

-- Stored procedures for automation

-- Procedure to get patients that need embedding generation
CREATE OR REPLACE FUNCTION insightsedge.get_patients_needing_embeddings()
RETURNS TABLE (
    patient_id INTEGER,
    mrn VARCHAR,
    age INTEGER,
    gender VARCHAR(20),
    combined_text TEXT,
    oncologist TEXT,
    date_of_visit DATE,
    created_at TIMESTAMP
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pmh.id as patient_id,
        pmh.mrn,
        pmh.age,
        pmh.gender,
        CONCAT(
            'Patient MRN: ', pmh.mrn, E'\n',
            'Age: ', COALESCE(pmh.age::TEXT, 'Not specified'), ', Gender: ', COALESCE(pmh.gender, 'Not specified'), E'\n',
            'Date of Visit: ', COALESCE(pmh.date_of_visit::TEXT, 'Not specified'), E'\n',
            'Oncologist: ', COALESCE(pmh.oncologist, 'Not specified'), E'\n\n',
            'Chief Complaint: ', COALESCE(pmh.chief_complaint, 'Not specified'), E'\n\n',
            'History of Present Illness: ', COALESCE(pmh.history_of_present_illness, 'Not specified'), E'\n\n',
            'Past Medical History: ', COALESCE(pmh.past_medical_history, 'Not specified'), E'\n\n',
            'Family History: ', COALESCE(pmh.family_history, 'Not specified'), E'\n\n',
            'Social History: ', COALESCE(pmh.social_history, 'Not specified'), E'\n\n',
            'Review of Systems: ', COALESCE(pmh.review_of_systems, 'Not specified'), E'\n\n',
            'Medications and Allergies: ', COALESCE(pmh.medications_allergies, 'Not specified'), E'\n\n',
            'Physical Examination: ', COALESCE(pmh.physical_examination, 'Not specified'), E'\n\n',
            'Laboratory and Imaging Results: ', COALESCE(pmh.laboratory_imaging_results, 'Not specified'), E'\n\n',
            'Imaging: ', COALESCE(pmh.imaging, 'Not specified'), E'\n\n',
            'Assessment: ', COALESCE(pmh.assessment, 'Not specified')
        ) as combined_text,
        pmh.oncologist,
        pmh.date_of_visit,
        pmh.created_at
    FROM insightsedge.patient_medical_history pmh
    LEFT JOIN insightsedge.patient_processing_status pps ON pmh.id = pps.patient_id
    WHERE pmh.age IS NOT NULL 
        AND pmh.gender IS NOT NULL
        AND pmh.gender IN ('Male', 'Female')
        AND (pps.patient_id IS NULL OR pps.embedding_generated = FALSE)
    ORDER BY pmh.created_at DESC;
END;
$$;

-- Procedure to get trials that need embedding generation
CREATE OR REPLACE FUNCTION insightsedge.get_trials_needing_embeddings()
RETURNS TABLE (
    trial_id TEXT,
    title TEXT,
    condition TEXT,
    phase TEXT,
    status TEXT,
    investigator TEXT,
    created_date TEXT,
    patients_matched INTEGER,
    matching_status TEXT,
    combined_trial_text TEXT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ctd.nct_id::TEXT as trial_id,
        ctd.study_title::TEXT as title,
        ctd.conditions::TEXT as condition,
        ctd.study_phase::TEXT as phase,
        ctd.overall_status::TEXT as status,
        ctd.lead_sponsor_name::TEXT as investigator,
        ctd.start_date::TEXT as created_date,
        0 as patients_matched,
        'pending'::TEXT as matching_status,
        CONCAT(
            'Trial ID: ', ctd.nct_id, E'\n',
            'Title: ', ctd.study_title, E'\n',
            'Condition: ', ctd.conditions, E'\n',
            'Phase: ', ctd.study_phase, E'\n',
            'Status: ', ctd.overall_status, E'\n',
            'Investigator: ', ctd.lead_sponsor_name, E'\n',
            'Start Date: ', ctd.start_date::TEXT, E'\n',
            'Age Range: ', COALESCE(ctd.minimum_age, 'Not specified'), ' - ', COALESCE(ctd.maximum_age, 'Not specified'), E'\n',
            'Gender: ', COALESCE(ctd.sex, 'Not specified'), E'\n\n',
            'Brief Summary: ', COALESCE(ctd.brief_summary, 'Not available'), E'\n\n',
            'Detailed Description: ', COALESCE(ctd.detailed_description, 'Not available'), E'\n\n',
            'Inclusion Criteria: ', COALESCE(ctd.inclusion_criteria, 'Not available'), E'\n\n',
            'Exclusion Criteria: ', COALESCE(ctd.exclusion_criteria, 'Not available'), E'\n\n',
            'Eligibility Criteria: ', COALESCE(ctd.eligibility_criteria, 'Not available')
        ) as combined_trial_text
    FROM insightsedge.clinical_trial_details ctd
    LEFT JOIN insightsedge.trial_processing_status tps ON ctd.nct_id = tps.trial_id
    WHERE ctd.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION', 'AVAILABLE')
        AND (tps.trial_id IS NULL OR tps.embedding_generated = FALSE)
    ORDER BY ctd.created_at DESC;
END;
$$;

-- Procedure to update patient processing status
CREATE OR REPLACE FUNCTION insightsedge.update_patient_processing_status(
    p_patient_id INTEGER,
    p_embedding_generated BOOLEAN DEFAULT NULL,
    p_keywords_generated BOOLEAN DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO insightsedge.patient_processing_status (
        patient_id, 
        embedding_generated, 
        keywords_generated, 
        last_embedding_update, 
        last_keyword_update,
        processing_errors
    )
    VALUES (
        p_patient_id,
        COALESCE(p_embedding_generated, FALSE),
        COALESCE(p_keywords_generated, FALSE),
        CASE WHEN p_embedding_generated = TRUE THEN CURRENT_TIMESTAMP ELSE NULL END,
        CASE WHEN p_keywords_generated = TRUE THEN CURRENT_TIMESTAMP ELSE NULL END,
        p_error_message
    )
    ON CONFLICT (patient_id) DO UPDATE SET
        embedding_generated = COALESCE(p_embedding_generated, patient_processing_status.embedding_generated),
        keywords_generated = COALESCE(p_keywords_generated, patient_processing_status.keywords_generated),
        last_embedding_update = CASE WHEN p_embedding_generated = TRUE THEN CURRENT_TIMESTAMP ELSE patient_processing_status.last_embedding_update END,
        last_keyword_update = CASE WHEN p_keywords_generated = TRUE THEN CURRENT_TIMESTAMP ELSE patient_processing_status.last_keyword_update END,
        processing_errors = COALESCE(p_error_message, patient_processing_status.processing_errors);
END;
$$;

-- Procedure to update trial processing status
CREATE OR REPLACE FUNCTION insightsedge.update_trial_processing_status(
    p_trial_id TEXT,
    p_embedding_generated BOOLEAN DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO insightsedge.trial_processing_status (
        trial_id, 
        embedding_generated, 
        last_embedding_update,
        processing_errors
    )
    VALUES (
        p_trial_id,
        COALESCE(p_embedding_generated, FALSE),
        CASE WHEN p_embedding_generated = TRUE THEN CURRENT_TIMESTAMP ELSE NULL END,
        p_error_message
    )
    ON CONFLICT (trial_id) DO UPDATE SET
        embedding_generated = COALESCE(p_embedding_generated, trial_processing_status.embedding_generated),
        last_embedding_update = CASE WHEN p_embedding_generated = TRUE THEN CURRENT_TIMESTAMP ELSE trial_processing_status.last_embedding_update END,
        processing_errors = COALESCE(p_error_message, trial_processing_status.processing_errors);
END;
$$;
