-- =====================================================
-- Clinical Trial Matching System - Evaluation Results Tables
-- =====================================================
-- This script creates tables to store LLM evaluation results
-- for both Patient-to-Trial and Trial-to-Patient flows
-- =====================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Table 1: Patient-to-Trial Evaluations
-- =====================================================
-- Stores results when evaluating trials for a specific patient
CREATE TABLE IF NOT EXISTS insightsedge.patient_to_trial_evaluations (
    -- Primary Key & Identifiers
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    patient_mrn VARCHAR(50) NOT NULL,
    evaluation_timestamp TIMESTAMP NOT NULL,
    
    -- Patient Information
    patient_age INTEGER,
    patient_gender VARCHAR(10),
    patient_oncologist TEXT,
    
    -- Evaluation Metadata
    total_trials_found INTEGER DEFAULT 0,
    total_trials_evaluated INTEGER DEFAULT 0,
    evaluation_method VARCHAR(20) DEFAULT 'batch', -- 'batch' or 'individual'
    batch_summary JSONB, -- Store the batch_summary object
    
    -- Results Summary
    eligible_trials_count INTEGER DEFAULT 0,
    not_eligible_trials_count INTEGER DEFAULT 0,
    need_more_info_trials_count INTEGER DEFAULT 0,
    average_confidence_score DECIMAL(5,2) DEFAULT 0.00,
    
    -- Individual Trial Evaluations (JSONB array)
    trial_evaluations JSONB, -- Array of individual trial evaluations
    
    -- System Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_patient_gender CHECK (patient_gender IN ('Male', 'Female')),
    CONSTRAINT chk_evaluation_method CHECK (evaluation_method IN ('batch', 'individual')),
    CONSTRAINT chk_confidence_score CHECK (average_confidence_score >= 0 AND average_confidence_score <= 100)
);

-- =====================================================
-- Table 2: Trial-to-Patient Evaluations
-- =====================================================
-- Stores results when evaluating patients for a specific trial
CREATE TABLE IF NOT EXISTS insightsedge.trial_to_patient_evaluations (
    -- Primary Key & Identifiers
    id SERIAL PRIMARY KEY,
    trial_id VARCHAR(50) NOT NULL,
    trial_title TEXT,
    evaluation_timestamp TIMESTAMP NOT NULL,
    
    -- Trial Information
    trial_condition TEXT,
    trial_phase VARCHAR(20),
    trial_status VARCHAR(20),
    trial_investigator TEXT,
    
    -- Evaluation Metadata
    total_patients_found INTEGER DEFAULT 0,
    total_patients_evaluated INTEGER DEFAULT 0,
    evaluation_method VARCHAR(20) DEFAULT 'batch', -- 'batch' or 'individual'
    batch_summary JSONB, -- Store the batch_summary object
    
    -- Results Summary
    eligible_patients_count INTEGER DEFAULT 0,
    not_eligible_patients_count INTEGER DEFAULT 0,
    need_more_info_patients_count INTEGER DEFAULT 0,
    average_confidence_score DECIMAL(5,2) DEFAULT 0.00,
    
    -- Individual Patient Evaluations (JSONB array)
    patient_evaluations JSONB, -- Array of individual patient evaluations
    
    -- System Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_trial_phase CHECK (trial_phase IN ('PHASE1', 'PHASE2', 'PHASE3', 'PHASE4', 'Not specified')),
    CONSTRAINT chk_trial_status CHECK (trial_status IN ('RECRUITING', 'ACTIVE', 'COMPLETED', 'SUSPENDED', 'TERMINATED', 'Not specified')),
    CONSTRAINT chk_evaluation_method_t2p CHECK (evaluation_method IN ('batch', 'individual')),
    CONSTRAINT chk_confidence_score_t2p CHECK (average_confidence_score >= 0 AND average_confidence_score <= 100)
);

-- =====================================================
-- Indexes for Performance (Created after tables)
-- =====================================================

-- Patient-to-Trial Evaluations Indexes
CREATE INDEX IF NOT EXISTS idx_p2t_patient_id ON insightsedge.patient_to_trial_evaluations(patient_id);

CREATE INDEX IF NOT EXISTS idx_p2t_patient_mrn ON insightsedge.patient_to_trial_evaluations(patient_mrn);

CREATE INDEX IF NOT EXISTS idx_p2t_evaluation_timestamp ON insightsedge.patient_to_trial_evaluations(evaluation_timestamp);

CREATE INDEX IF NOT EXISTS idx_p2t_created_at ON insightsedge.patient_to_trial_evaluations(created_at);

CREATE INDEX IF NOT EXISTS idx_p2t_eligible_count ON insightsedge.patient_to_trial_evaluations(eligible_trials_count);

-- Trial-to-Patient Evaluations Indexes
CREATE INDEX IF NOT EXISTS idx_t2p_trial_id ON insightsedge.trial_to_patient_evaluations(trial_id);

CREATE INDEX IF NOT EXISTS idx_t2p_evaluation_timestamp ON insightsedge.trial_to_patient_evaluations(evaluation_timestamp);

CREATE INDEX IF NOT EXISTS idx_t2p_created_at ON insightsedge.trial_to_patient_evaluations(created_at);

CREATE INDEX IF NOT EXISTS idx_t2p_eligible_count ON insightsedge.trial_to_patient_evaluations(eligible_patients_count);

-- =====================================================
-- Triggers for Auto-Update Timestamps
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION insightsedge.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for patient_to_trial_evaluations
DROP TRIGGER IF EXISTS update_p2t_evaluations_updated_at ON insightsedge.patient_to_trial_evaluations;
CREATE TRIGGER update_p2t_evaluations_updated_at
    BEFORE UPDATE ON insightsedge.patient_to_trial_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION insightsedge.update_updated_at_column();

-- Trigger for trial_to_patient_evaluations
DROP TRIGGER IF EXISTS update_t2p_evaluations_updated_at ON insightsedge.trial_to_patient_evaluations;
CREATE TRIGGER update_t2p_evaluations_updated_at
    BEFORE UPDATE ON insightsedge.trial_to_patient_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION insightsedge.update_updated_at_column();

-- =====================================================
-- Comments for Documentation
-- =====================================================

COMMENT ON TABLE insightsedge.patient_to_trial_evaluations IS 'Stores LLM evaluation results when finding trials for a specific patient';
COMMENT ON TABLE insightsedge.trial_to_patient_evaluations IS 'Stores LLM evaluation results when finding patients for a specific trial';

COMMENT ON COLUMN insightsedge.patient_to_trial_evaluations.batch_summary IS 'JSONB object containing batch-level statistics and recommendations';
COMMENT ON COLUMN insightsedge.patient_to_trial_evaluations.trial_evaluations IS 'JSONB array of individual trial evaluation results';

COMMENT ON COLUMN insightsedge.trial_to_patient_evaluations.batch_summary IS 'JSONB object containing batch-level statistics and recommendations';
COMMENT ON COLUMN insightsedge.trial_to_patient_evaluations.patient_evaluations IS 'JSONB array of individual patient evaluation results';

-- =====================================================
-- Success Message
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Evaluation results tables created successfully!';
    RAISE NOTICE '📊 Tables created:';
    RAISE NOTICE '   - insightsedge.patient_to_trial_evaluations';
    RAISE NOTICE '   - insightsedge.trial_to_patient_evaluations';
    RAISE NOTICE '🔍 Indexes and triggers configured for optimal performance';
END $$;
