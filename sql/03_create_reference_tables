
-- ============================================================
-- Communicable STI Disease Surveillance Pipeline
-- 03 - Create STI Reference Tables
-- ============================================================
--
-- Description:
-- Creates the Athena reference database and external table
-- used to classify CDESS STI diseases into standardized
-- reporting groups.
--
-- The disease mapping is stored as a CSV file in Amazon S3
-- and contains two columns:
--   disease_name  - Original CDESS disease name
--   disease_group - Standardized STI reporting category
--
-- The pipeline reuses the existing ACS demographic reference
-- table from the original Communicable Disease Pipeline:
--   communicable_db_reference.ref_demographics
--
-- Database: communicable_sti_db_reference
-- Region: us-east-2 (Ohio)
--
-- ============================================================

-- Create reference database
CREATE DATABASE IF NOT EXISTS communicable_sti_db_reference;


-- Create STI disease classification reference table
CREATE EXTERNAL TABLE IF NOT EXISTS
communicable_sti_db_reference.ref_communicable_sti_disease_mapping (
    disease_name STRING,
    disease_group STRING
)
ROW FORMAT SERDE
    'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"',
    'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION
    's3://publichealth-project-data-lake-152125350281-us-east-2-an/reference/ny-state/sti-disease-classification/'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);
