# Communicable STI Disease Pipeline

An AWS-based data engineering and public health surveillance project that processes sexually transmitted infection (STI) data from the Communicable Disease Electronic Surveillance System (CDESS) for **Orange County, New York**.

This project extends and supports the previously developed **CDESS Communicable Disease Surveillance Pipeline**, providing additional surveillance indicators and analysis for sexually transmitted infections.

The pipeline uses **Amazon S3, Amazon Athena, AWS Lambda, and Amazon QuickSight (SPICE)** to calculate annual STI case counts and incidence rates per 100,000 population using American Community Survey (ACS) 1-Year and 5-Year population estimates.

## Pipeline Classification

**Serverless AWS ETL Pipeline for Communicable STI Disease Surveillance**

This project implements an on-demand, automated batch ETL pipeline built on an Amazon S3 data lake.

County-level CDESS STI extracts, disease classification reference data, and ACS population estimates are processed through Amazon Athena to produce curated, population-adjusted incidence rates stored in Parquet format.

AWS Lambda orchestrates the Athena transformation and initiates a QuickSight SPICE refresh.

The pipeline is:

- **Serverless:** Uses managed AWS services without dedicated servers.
- **Batch-based:** Processes periodic CDESS extracts rather than streaming data.
- **Manually triggered:** Runs when updated surveillance data is available.
- **Automated downstream:** Rebuilds the curated dataset and initiates the dashboard refresh after source preparation.

## Relationship to the Original Communicable Disease Pipeline

The Communicable STI Disease Pipeline was developed as a supporting component of the original CDESS communicable disease analysis.

The original project established the infrastructure for processing communicable disease surveillance records, calculating annual incidence rates, and presenting public health indicators through Amazon QuickSight.

The STI pipeline builds upon that foundation while maintaining a separate processing workflow because STI source data has a different structure and disease classification requirements.

Both pipelines:

- Use the same AWS region and underlying S3 data lake.
- Follow the same Athena-based transformation methodology.
- Calculate confirmed and probable case counts.
- Calculate incidence rates per 100,000 population.
- Reuse the existing ACS demographic population reference table.
- Use Lambda to automate dataset rebuilding and QuickSight refresh initiation.

The STI dataset is incorporated into the existing QuickSight analysis as a **separate STI sheet**, allowing users to explore STI surveillance alongside the broader communicable disease analysis.

This approach expands the analytical capabilities of the original project without combining datasets with different source structures.

## Project Objectives

1. Process county-level CDESS STI surveillance data.
2. Calculate annual confirmed and probable STI case counts.
3. Classify individual STI diagnoses into broader disease groups.
4. Analyze cases by age, sex, and ethnicity.
5. Calculate incidence rates per 100,000 using ACS 1-Year and 5-Year population estimates.
6. Provide interactive STI surveillance charts, tables, and comparisons.
7. Automate curated dataset rebuilding and QuickSight SPICE refresh initiation.
8. Extend the existing communicable disease surveillance analysis.

## Architecture

```text
CDESS STI Extract
       |
       v
Amazon S3 Raw Data
       |
       +-------------------------+
       |                         |
       v                         v
STI Disease Mapping       ACS Demographics
       |                         |
       +------------+------------+
                    |
                    v
           Amazon Athena
        Raw and Reference Tables
                    |
                    v
              AWS Lambda
          Manual Refresh Trigger
                    |
        +-----------+-----------+
        |                       |
        v                       v
   Repair Partitions       Rebuild Curated
                           Athena CTAS Table
                                |
                                v
                       Curated Parquet Data
                                |
                                v
                       QuickSight SPICE
                                |
                                v
                     Existing QuickSight
                         Analysis
                                |
                                v
                       Separate STI Sheet
```

The Lambda function initiates the QuickSight ingestion. Successful Lambda execution does not necessarily mean that SPICE ingestion has completed; completion must be verified separately in QuickSight.

## AWS Components

| AWS Service | Purpose |
|---|---|
| Amazon S3 | Stores raw STI extracts, reference data, and curated Parquet output |
| Amazon Athena | Queries and transforms surveillance data |
| AWS Glue Data Catalog | Maintains database, table, and partition metadata |
| AWS Lambda | Orchestrates the automated refresh process |
| Amazon QuickSight | Provides interactive public health visualizations |
| QuickSight SPICE | Stores the refreshed analytical dataset |

**AWS Region:** `us-east-2` (Ohio)

## Athena Databases and Tables

| Database | Table | Purpose |
|---|---|---|
| `communicable_sti_db_raw` | `raw_cdess_sti_opencsv` | Raw CDESS STI surveillance records |
| `communicable_sti_db_reference` | `ref_communicable_sti_disease_mapping` | STI disease classification |
| `communicable_db_reference` | `ref_demographics` | Shared ACS population estimates |
| `communicable_sti_db_curated` | `communicable_sti_disease_incidence` | Curated annual STI counts and incidence rates |

The STI pipeline reuses the demographic reference table from the original communicable disease project rather than creating a duplicate.

## Amazon S3 Data Organization

The following illustrates the main STI data locations:

```text
s3://<bucket>/
|
+-- raw/ny-state/cdess/
|   +-- data_type=sti/
|       +-- county_name=orange/
|           +-- extract_year=YYYY/
|               +-- extract_month=MM/
|
+-- reference/ny-state/
|   +-- sti-disease-classification/
|   +-- demographics/
|       +-- geography=orange-county/
|
+-- curated/ny-state/cdess/
|   +-- data_type=sti/
|       +-- incidence/
|
+-- cdess/sti/
    +-- athena-results/
```

The latest extract is selected using the maximum combination of `extract_year` and `extract_month`, preventing repeated counting of historical cases across successive source snapshots.

## Data Preparation and Transformation Rules

### Case Inclusion

Only cases with the following CDESS status codes are included:

| Code | Classification |
|---|---|
| 1 | Confirmed |
| 2 | Probable |

### Disease Classification

Individual STI diagnoses are grouped into broader disease categories:

- Chlamydia
- Gonorrhea
- Syphilis
- Mpox

Disease classifications are maintained in a separate reference mapping table.

### Demographic Categories

**Age groups:** 0–4, 5–14, 15–24, 25–44, 45–64, 65–84, and 85+ (ages 85–110).

**Sex:** Male and Female.

**Ethnicity:** Hispanic and Non-Hispanic.

Missing or unrecognized demographic values are excluded from the corresponding demographic-specific counts but remain included in overall case totals.

### Incidence Calculation

Annual incidence rates are calculated as:

**Incidence Rate = (Annual Case Count / Population Estimate) × 100,000**

Both ACS 1-Year and ACS 5-Year estimates are retained so users can compare incidence rates calculated using different population denominators.

Missing population estimates result in unavailable incidence rates rather than assumed population values.

## Curated Dataset

The Athena CTAS transformation produces a Parquet dataset containing:

| Field | Description |
|---|---|
| `disease_name` | Individual STI diagnosis |
| `indicator_title` | Disease incidence indicator |
| `disease_group` | Broader STI classification |
| `demographic_type` | Total, age, sex, or ethnicity |
| `demographic_group` | Specific demographic category |
| `case_count` | Annual number of eligible cases |
| `estimate_type` | ACS 1-Year or 5-Year |
| `population` | Corresponding population denominator |
| `incidence_rate` | Cases per 100,000 population |
| `geographic_area` | Orange County |
| `case_year` | Year of surveillance case |

The curated dataset is partitioned by `geographic_area` and `case_year`.

## AWS Lambda Automation

**Lambda Function:** `communicable-sti-disease-pipeline-refresh`

The Lambda function automates the following sequence:

1. Repair raw STI table partitions using `MSCK REPAIR TABLE`.
2. Drop the existing curated STI incidence table.
3. Delete the previous curated Parquet objects from S3.
4. Execute the Athena CTAS query to recreate the curated dataset.
5. Initiate a QuickSight SPICE ingestion.

The Lambda uses Python and the AWS SDK for Python (`boto3`).

**Operational caution:** The current refresh procedure deletes the previous curated table and S3 output before recreating them. A failed rebuild can temporarily make the curated dataset unavailable.

## Amazon QuickSight Analysis

The STI surveillance dataset is incorporated into the existing communicable disease QuickSight analysis as a separate sheet.

The STI sheet includes:

- Annual incidence rate line charts.
- Disease and demographic filtering controls.
- ACS 1-Year and 5-Year estimate comparisons.
- Surveillance summary tables.
- Year-by-year pivot tables.
- Disease distribution charts showing each STI disease group's percentage of overall STI cases.
- Data sources and methodology documentation.

The disease distribution chart uses overall case totals and a single ACS estimate selection to avoid double-counting cases in the long-format dataset.

This integrated dashboard structure supports the original communicable disease analysis while extending surveillance reporting to STIs.

## Manual Update Procedure

The pipeline is currently refreshed manually when new surveillance data becomes available.

1. Obtain the updated county-level CDESS STI extract.
2. Confirm that the `geographic_area` field is populated with `Orange County`.
3. Validate the CSV structure and upload it to the appropriate S3 extract partition.
4. Update the STI disease classification mapping if necessary.
5. Update the shared ACS demographic reference data when new estimates become available.
6. Validate the source and reference tables in Athena.
7. Invoke the STI Lambda function using the saved test event `CommSTIPipelineRefresh` with `{}`.
8. Confirm successful Lambda execution in CloudWatch logs.
9. Verify that QuickSight SPICE ingestion completes successfully.
10. Review the refreshed STI visuals and confirm that counts and incidence calculations are consistent.

## Latest Verified Execution

**November 14, 2026 — Initial end-to-end automation test**

The STI Lambda pipeline executed successfully, including the Athena curated table rebuild and initiation of the QuickSight refresh.

Recorded Lambda performance:

- Execution duration: approximately 14.7 seconds.
- Configured memory: 128 MB.
- Maximum memory used: 105 MB.
- Lambda execution status: Succeeded.

The QuickSight SPICE ingestion subsequently completed, and the refreshed STI dashboard graphs were visually verified.

Earlier Athena validation of the source extract identified **9,690 eligible confirmed and probable cases**, covering surveillance years 2020–2025.

These validation totals describe the tested source extract and should not be interpreted as permanent dataset totals.

## Repository Structure

Planned repository organization:

```text
CDESS_Communicable_STI_Pipeline/
|
+-- README.md
|
+-- sql/
|   +-- Athena table definitions
|   +-- STI curated CTAS query
|   +-- Validation queries
|
+-- lambda/
|   +-- STI pipeline automation script
|
+-- docs/
|   +-- Architecture and methodology
|
+-- screenshots/
    +-- Approved dashboard images
```

The repository contains code and documentation only. Restricted surveillance datasets are not included.

## Limitations and Future Enhancements

- The pipeline depends on the availability and quality of CDESS extracts.
- Demographic-specific counts may be affected by missing or incomplete source values.
- ACS population estimates may not be available for the latest surveillance year.
- The pipeline currently requires manual invocation.
- QuickSight ingestion is initiated by Lambda but is not monitored through completion by the current script.
- Future enhancements may include automated validation, improved failure recovery, narrower IAM permissions, and scheduled refreshes when appropriate.

## Data Privacy

This repository is public and is intended to document the technical implementation of the surveillance pipeline.

**No identifiable patient information, restricted CDESS line lists, AWS credentials, access keys, or sensitive source datasets should be committed to the repository.**

Only approved source code, documentation, non-sensitive reference materials, and reviewed dashboard screenshots should be published.

## Data Sources and Methodology

- **CDESS:** County-specific communicable STI surveillance extracts.
- **American Community Survey:** ACS 1-Year and 5-Year population estimates.
- **STI Disease Classification Reference:** Project-maintained disease grouping table.

This project is designed to support public health surveillance analysis and reporting. Incidence estimates should be interpreted in the context of case reporting practices, demographic completeness, and population estimate availability.

---

**Project relationship:** Supporting extension of the CDESS Communicable Disease Surveillance Pipeline for Orange County, New York.
