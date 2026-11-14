
-- ============================================================
-- Communicable STI Disease Surveillance Pipeline
-- 05 - Validation Queries
-- ============================================================
--
-- Description:
-- Validates raw CDESS STI data, disease classifications,
-- demographic distributions, ACS population denominators,
-- and calculated incidence rates.
--
-- These queries can be executed individually in Amazon Athena
-- after a pipeline refresh.
--
-- Region: us-east-2 (Ohio)
--
-- ============================================================


-- ------------------------------------------------------------
-- 1. Inspect raw STI data
-- ------------------------------------------------------------

SELECT *
FROM communicable_sti_db_raw.raw_cdess_sti_opencsv
LIMIT 10;


-- ------------------------------------------------------------
-- 2. Verify raw table partitions
-- ------------------------------------------------------------

SHOW PARTITIONS
communicable_sti_db_raw.raw_cdess_sti_opencsv;


-- ------------------------------------------------------------
-- 3. Inspect STI disease classification reference
-- ------------------------------------------------------------

SELECT *
FROM communicable_sti_db_reference.ref_communicable_sti_disease_mapping
ORDER BY disease_group, disease_name;


-- ------------------------------------------------------------
-- 4. Identify unmapped STI disease names
-- ------------------------------------------------------------

SELECT DISTINCT
    TRIM(c.diseasename) AS disease_name
FROM communicable_sti_db_raw.raw_cdess_sti_opencsv c

LEFT JOIN
    communicable_sti_db_reference.ref_communicable_sti_disease_mapping d
    ON TRIM(c.diseasename) = TRIM(d.disease_name)

WHERE d.disease_name IS NULL
ORDER BY disease_name;


-- ------------------------------------------------------------
-- 5. Inspect curated STI incidence data
-- ------------------------------------------------------------

SELECT *
FROM communicable_sti_db_curated.communicable_sti_disease_incidence
LIMIT 10;


-- ------------------------------------------------------------
-- 6. Verify curated table partitions
-- ------------------------------------------------------------

SHOW PARTITIONS
communicable_sti_db_curated.communicable_sti_disease_incidence;


-- ------------------------------------------------------------
-- 7. Validate annual STI case counts by disease
-- Use Total demographic rows and one ACS estimate type
-- to avoid double-counting repeated case counts.
-- ------------------------------------------------------------

SELECT
    case_year,
    disease_name,
    disease_group,
    SUM(case_count) AS total_cases

FROM communicable_sti_db_curated.communicable_sti_disease_incidence

WHERE demographic_type = 'Total'
    AND demographic_group = 'Total'
    AND estimate_type = '1-Year'

GROUP BY
    case_year,
    disease_name,
    disease_group

ORDER BY
    case_year,
    disease_group,
    disease_name;


-- ------------------------------------------------------------
-- 8. Validate annual STI case counts by demographic group
-- ------------------------------------------------------------

SELECT
    case_year,
    demographic_type,
    demographic_group,
    SUM(case_count) AS total_cases

FROM communicable_sti_db_curated.communicable_sti_disease_incidence

WHERE estimate_type = '1-Year'

GROUP BY
    case_year,
    demographic_type,
    demographic_group

ORDER BY
    case_year,
    demographic_type,
    demographic_group;


-- ------------------------------------------------------------
-- 9. Identify missing ACS population denominators
-- ------------------------------------------------------------

SELECT
    case_year,
    estimate_type,
    demographic_type,
    COUNT(*) AS total_rows,
    COUNT(population) AS rows_with_population,
    SUM(
        CASE
            WHEN population IS NULL THEN 1
            ELSE 0
        END
    ) AS missing_population_rows

FROM communicable_sti_db_curated.communicable_sti_disease_incidence

GROUP BY
    case_year,
    estimate_type,
    demographic_type

ORDER BY
    case_year,
    estimate_type,
    demographic_type;


-- ------------------------------------------------------------
-- 10. Validate incidence rate calculations
-- Recalculate rates and compare with stored values.
-- ------------------------------------------------------------

SELECT
    case_year,
    disease_name,
    demographic_type,
    demographic_group,
    estimate_type,
    case_count,
    population,
    incidence_rate,

    ROUND(
        CAST(case_count AS DOUBLE)
        / NULLIF(CAST(population AS DOUBLE), 0)
        * 100000,
        2
    ) AS recalculated_incidence_rate

FROM communicable_sti_db_curated.communicable_sti_disease_incidence

WHERE population IS NOT NULL
    AND population > 0

ORDER BY
    case_year,
    disease_name,
    demographic_type,
    demographic_group,
    estimate_type;
