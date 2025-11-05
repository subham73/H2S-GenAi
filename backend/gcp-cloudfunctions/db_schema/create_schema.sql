-- BigQuery Table Schemas for Healthcare Testing System

-- This script creates all necessary tables, primary keys, and views.
-- It is idempotent and can be run multiple times.

-- Create Issues Table
CREATE TABLE IF NOT EXISTS `h2shackathon.healthcare_data.issues` (
  issue_id STRING NOT NULL,
  issue_type STRING NOT NULL,
  title STRING NOT NULL,
  description STRING,
  priority STRING,
  status STRING,
  assignee STRING,
  created_date TIMESTAMP,
  updated_date TIMESTAMP,
  sync_timestamp TIMESTAMP,
  compliance_validated BOOLEAN DEFAULT FALSE,
  compliance_notes STRING
);

-- Create Test Cases Table
CREATE TABLE IF NOT EXISTS `h2shackathon.healthcare_data.test_cases` (
  test_case_id STRING NOT NULL,
  issue_id STRING NOT NULL,
  test_name STRING NOT NULL,
  test_desc STRING,
  test_type STRING, -- 'functional', 'compliance', 'integration'
  preconditions STRING,
  test_steps STRING,
  expected_result STRING,
  priority STRING,
  hipaa_compliance_level STRING, -- 'required', 'recommended', 'optional'
  created_by STRING, -- 'gcp_agent', 'manual'
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  status STRING -- 'active', 'deprecated', 'pending_review', 'in qa', 'done'
);

-- Create Test Results Table
CREATE TABLE IF NOT EXISTS `h2shackathon.healthcare_data.test_results` (
  test_result_id STRING NOT NULL,
  test_case_id STRING NOT NULL,
  exec_id STRING,
  status STRING, -- 'PASSED', 'FAILED', 'SKIPPED', 'ERROR'
  actual_result STRING,
  expected_result STRING,
  failure_reason STRING,
  execution_timestamp TIMESTAMP,
  execution_duration_ms INT64,
  environment STRING,
  executed_by STRING, -- 'gcp_agent', 'manual'
  defect_id STRING, -- ALM defect key if created
  defect_created_timestamp TIMESTAMP,
  compliance_issues ARRAY<STRING>,
  screenshots_urls ARRAY<STRING>,
  logs_url STRING
);

-- Create Compliance Reports Table
CREATE TABLE IF NOT EXISTS `h2shackathon.healthcare_data.compliance_reports` (
  report_id STRING NOT NULL,
  test_case_id STRING,
  issue_id STRING,
  compliance_standard STRING, -- 'HIPAA', 'FDA', 'HL7'
  compliance_rule STRING,
  validation_result STRING, -- 'COMPLIANT', 'NON_COMPLIANT', 'NEEDS_REVIEW'
  violation_details STRING,
  remediation_suggestions STRING,
  validated_timestamp TIMESTAMP,
  validator_agent_id STRING,
  severity_level STRING -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
);

-- Create Execution Matrix Table
CREATE TABLE IF NOT EXISTS `h2shackathon.healthcare_data.execution_matrix` (
  exec_id STRING NOT NULL,
  issue_id STRING NOT NULL,
  total_test_cases INT64,
  passed_tests INT64,
  failed_tests INT64,
  skipped_tests INT64,
  execution_start_time TIMESTAMP,
  execution_end_time TIMESTAMP,
  execution_status STRING, -- 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'
  triggered_by STRING, -- 'requirement_update', 'scheduled', 'manual'
  environment STRING,
  compliance_score FLOAT64, -- percentage of compliance tests passed
  overall_result STRING -- 'PASS', 'FAIL', 'PARTIAL'
);

-- Create Agents Log Table
CREATE TABLE IF NOT EXISTS `h2shackathon.healthcare_data.agents_log` (
  log_id STRING NOT NULL,
  agent_type STRING, -- 'test_generator', 'compliance_validator', 'test_executor'
  agent_id STRING,
  action STRING, -- 'generate_tests', 'validate_compliance', 'execute_tests'
  related_issue_id STRING,
  related_test_case_id STRING,
  input_data STRING,
  output_data STRING,
  execution_timestamp TIMESTAMP,
  status STRING, -- 'SUCCESS', 'FAILED', 'PARTIAL'
  error_message STRING,
  processing_time_ms INT64
);

-- Create JIRA Sync Status Table
CREATE TABLE IF NOT EXISTS `h2shackathon.healthcare_data.jira_sync_status` (
  sync_id STRING NOT NULL,
  entity_type STRING, -- 'requirement', 'defect', 'feature'
  entity_id STRING, -- issue_id or test_result_id
  jira_key STRING,
  sync_direction STRING, -- 'jira_to_bigquery', 'bigquery_to_jira'
  sync_timestamp TIMESTAMP,
  sync_status STRING, -- 'SUCCESS', 'FAILED', 'PENDING'
  error_message STRING,
  retry_count INT64
);

-- Primary keys and indexes for performance
ALTER TABLE `h2shackathon.healthcare_data.issues` ADD PRIMARY KEY (issue_id) NOT ENFORCED;
ALTER TABLE `h2shackathon.healthcare_data.test_cases` ADD PRIMARY KEY (test_case_id) NOT ENFORCED;
ALTER TABLE `h2shackathon.healthcare_data.test_results` ADD PRIMARY KEY (test_result_id) NOT ENFORCED;

-- Create views for common queries
CREATE OR REPLACE VIEW `h2shackathon.healthcare_data.failed_tests_without_defects` AS
SELECT
  tr.*,
  tc.test_name,
  i.issue_id as issue_id
FROM `h2shackathon.healthcare_data.test_results` tr
JOIN `h2shackathon.healthcare_data.test_cases` tc ON tr.test_case_id = tc.test_case_id
JOIN `h2shackathon.healthcare_data.issues` i ON tc.issue_id = i.issue_id
WHERE tr.status = 'FAILED'
AND (tr.defect_id IS NULL OR tr.defect_id = '');

CREATE OR REPLACE VIEW `h2shackathon.healthcare_data.compliance_summary` AS
SELECT
  i.issue_id,
  i.title,
  COUNT(tc.test_case_id) as total_tests,
  COUNT(CASE WHEN tr.status = 'PASSED' THEN 1 END) as passed_tests,
  COUNT(CASE WHEN tr.status = 'FAILED' THEN 1 END) as failed_tests,
  COUNT(CASE WHEN cr.validation_result = 'COMPLIANT' THEN 1 END) as compliant_tests,
  COUNT(CASE WHEN cr.validation_result = 'NON_COMPLIANT' THEN 1 END) as non_compliant_tests
FROM `h2shackathon.healthcare_data.issues` i
LEFT JOIN `h2shackathon.healthcare_data.test_cases` tc ON i.issue_id = tc.issue_id
LEFT JOIN `h2shackathon.healthcare_data.test_results` tr ON tc.test_case_id = tr.test_case_id
LEFT JOIN `h2shackathon.healthcare_data.compliance_reports` cr ON tc.test_case_id = cr.test_case_id
GROUP BY i.issue_id, i.title;
