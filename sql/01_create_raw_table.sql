
-- ============================================================
-- Communicable STI Disease Surveillance Pipeline
-- 01 - Create Raw CDESS STI Table
-- ============================================================
--
-- Description:
-- Creates the external Athena table for raw CDESS STI data
-- for Orange County, New York.
--
-- The table reads CSV files stored in Amazon S3 and is
-- partitioned by county, extraction year, and extraction month.
--
-- Source: Communicable Disease Electronic Surveillance System
-- Database: communicable_sti_db_raw
-- Region: us-east-2 (Ohio)
--
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS
communicable_sti_db_raw.raw_cdess_sti_opencsv (
    serialno STRING,
    caseyear STRING,
    zipcode STRING,
    diseasename STRING,
    age STRING,
    ageunits STRING,
    raceco STRING,
    white STRING,
    black STRING,
    amerind STRING,
    asian STRING,
    pacific STRING,
    othrace STRING,
    unkrace STRING,
    ethnicitycode STRING,
    ethnicity STRING,
    sexcode STRING,
    gender STRING,
    casestatus STRING,
    geographic_area STRING
)
PARTITIONED BY (
    county_name STRING,
    extract_year STRING,
    extract_month STRING
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
    's3://publichealth-project-data-lake-152125350281-us-east-2-an/raw/ny-state/cdess/data_type=sti/'
TBLPROPERTIES (
    'skip.header.line.count' = '1'
);
