# Reference Data

This directory contains the reference datasets used by the **CDESS Communicable STI Disease Pipeline** for Orange County, New York.

This pipeline supports the existing Communicable Disease Surveillance analysis by incorporating sexually transmitted infection (STI) data into a separate analytical dataset and QuickSight dashboard sheet.

The reference datasets support STI disease classification, demographic stratification, and the calculation of annual STI incidence rates per 100,000 population.

## Reference Datasets

### 1. STI Disease Classification Mapping

**File:** `communicable_sti_disease_type_mapping.csv`

**Purpose:** Maps individual STI disease names from CDESS to standardized disease groups for reporting and visualization.

| Column | Description |
|---|---|
| `disease_name` | Disease name corresponding to the CDESS source dataset |
| `disease_group` | Standardized STI disease group |

The mapping contains 10 disease classifications organized into four reporting groups:

- Chlamydia
- Gonorrhea
- Syphilis
- Mpox

**Athena table:** `communicable_sti_db_reference.ref_communicable_sti_disease_mapping`

**S3 location:**

`s3://publichealth-project-data-lake-152125350281-us-east-2-an/reference/ny-state/sti-disease-classification/`

The STI classification mapping is joined to the raw CDESS dataset using `disease_name`.

It allows the QuickSight dashboard to group related STI diagnoses and compare disease distributions across reporting years.

The mapping should be reviewed whenever new STI disease names or classifications appear in CDESS extracts.

### 2. Demographic Population Reference

**File:** `demographic_reference_orange_county_2024.csv`

**Purpose:** Provides population denominators used to calculate annual STI incidence rates for Orange County, New York.

The dataset contains American Community Survey (ACS) 1-Year and 5-Year population estimates covering 2018–2024.

| Column | Description |
|---|---|
| `Geographic Area` | Geographic location, currently Orange County |
| `Year` | Population estimate year |
| `demographic_type` | Total, age, sex, or ethnicity |
| `demographic_group` | Specific demographic category |
| `population` | Estimated population |
| `source` | Source of the population estimate |
| `estimate_type` | ACS 1-Year or 5-Year |

**Athena table:** `communicable_db_reference.ref_demographics`

**S3 location:**

`s3://publichealth-project-data-lake-152125350281-us-east-2-an/reference/ny-state/demographics/geography=orange-county/`

This demographic reference dataset is shared with the original Communicable Disease Surveillance Pipeline.

The STI pipeline reuses the existing population reference rather than maintaining a duplicate demographic dataset.

Age groups used by the pipeline are:

- 0–4
- 5–14
- 15–24
- 25–44
- 45–64
- 65–84
- 85+

Sex categories are Female and Male. Ethnicity categories are Hispanic and Non-Hispanic.

## Incidence Rate Calculation

Annual STI incidence rates are calculated using:

**Incidence Rate = (Case Count / Population) × 100,000**

The pipeline includes confirmed and probable STI cases, corresponding to CDESS case status codes 1 and 2.

Separate incidence rates are calculated using ACS 1-Year and ACS 5-Year population denominators.

This allows comparisons across reporting years and demographic groups.

If a corresponding population denominator is unavailable, the incidence rate remains null.

## Reference Data Maintenance

Reference datasets are maintained separately from the raw CDESS STI case-level exports.

### Annual Demographic Update

1. Obtain updated ACS population estimates.
2. Prepare the demographic reference CSV using the existing column structure and demographic group definitions.
3. Verify that `Geographic Area` is populated with `Orange County`.
4. Validate population estimates and their corresponding years.
5. Update the shared demographic reference CSV in its existing S3 location, ensuring obsolete CSV versions are not left alongside the replacement.
6. Run the AWS Lambda pipeline refresh after updating the necessary source datasets.
7. Validate the resulting Athena STI incidence table and QuickSight SPICE refresh.

Because this demographic reference is shared with the original communicable disease pipeline, updates should be validated for compatibility with both analyses.

### STI Disease Classification Update

Review the STI disease mapping whenever new disease names appear in CDESS extracts.

Add or update classifications as necessary before running the pipeline.

The original `disease_name` values must match the corresponding CDESS source values.

## Data Quality Considerations

- STI disease names must match between the CDESS dataset and the disease classification mapping.
- Disease groups must accurately reflect the intended reporting classifications.
- Demographic categories must align with the categories used by the Athena transformation.
- Population estimates must correspond to the correct geographic area and reporting year.
- ACS 1-Year and 5-Year estimates must remain distinguishable.
- Missing population denominators should not be interpreted as zero incidence.
- Unmapped STI disease names should be investigated before interpreting results.
- Confirmed and probable case classifications must be applied consistently.
- The latest available CDESS extract should be used to prevent duplicate counting across cumulative extracts.

## Data Sources

- **Communicable Disease Electronic Surveillance System (CDESS):** STI surveillance records used by the pipeline.
- **U.S. Census Bureau — American Community Survey (ACS):** Population estimates used as incidence rate denominators.
- **STI disease classification mapping:** Project-maintained reference dataset for grouping STI diagnoses into standardized reporting categories.

## Related SQL Scripts

The SQL definitions and validation queries for the STI pipeline are maintained in the repository's `sql/` directory.

These scripts support:

- Creation of the raw CDESS STI table.
- Creation of STI reference tables.
- Transformation of raw surveillance records into curated incidence data.
- Validation of disease classifications, demographic denominators, and calculated incidence rates.

The reference datasets support the curated Athena table:

`communicable_sti_db_curated.communicable_sti_disease_incidence`

The curated dataset is used by the STI sheet within the existing Amazon QuickSight communicable disease analysis.
