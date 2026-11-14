# ============================================================
# Communicable STI Disease Surveillance Pipeline
# AWS Lambda Automation
# ============================================================
#
# Description:
# Automates the refresh of the Orange County, NY Communicable
# STI Disease Surveillance Pipeline.
#
# The function:
# 1. Repairs raw CDESS STI partitions in Amazon Athena.
# 2. Removes the previous curated incidence dataset.
# 3. Rebuilds the curated Parquet table with updated STI data.
# 4. Calculates incidence rates using ACS population estimates.
# 5. Initiates an Amazon QuickSight SPICE dataset refresh.
#
# AWS Services: Lambda, S3, Athena, QuickSight
# Region: us-east-2 (Ohio)
#
# ============================================================

import time
import uuid
import boto3

REGION = "us-east-2"
ACCOUNT_ID = "152125350281"

BUCKET = "publichealth-project-data-lake-152125350281-us-east-2-an"
ATHENA_DATABASE = "communicable_sti_db_curated"
ATHENA_WORKGROUP = "primary"
ATHENA_OUTPUT = f"s3://{BUCKET}/cdess/sti/athena-results/"

QUICKSIGHT_DATASET_ID = "f028536e-4458-4ff1-ad7a-3ae3c6cb1fe4"

CURATED_PREFIX = "curated/ny-state/cdess/data_type=sti/incidence/"


athena = boto3.client("athena", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
quicksight = boto3.client("quicksight", region_name=REGION)


COMMUNICABLE_STI_DISEASE_SQL = f"""
CREATE TABLE communicable_sti_db_curated.communicable_sti_disease_incidence
WITH (
    format = 'PARQUET',
    external_location = 's3://publichealth-project-data-lake-152125350281-us-east-2-an/curated/ny-state/cdess/data_type=sti/incidence/',
    partitioned_by = ARRAY['geographic_area', 'case_year']
)
AS

WITH latest_extract AS (

    SELECT
        MAX(
            TRY_CAST(extract_year AS INTEGER) * 100
            + TRY_CAST(extract_month AS INTEGER)
        ) AS latest_extract_yyyymm

    FROM communicable_sti_db_raw.raw_cdess_sti_opencsv
),

eligible_cases AS (

    SELECT
        TRIM(c.geographic_area) AS geographic_area,
        TRY_CAST(c.caseyear AS INTEGER) AS case_year,
        TRIM(c.diseasename) AS disease_name,
        TRIM(d.disease_group) AS disease_group,

        -- Age groups
        CASE
            WHEN TRY_CAST(c.age AS INTEGER) BETWEEN 0 AND 4
                THEN '0-4'
            WHEN TRY_CAST(c.age AS INTEGER) BETWEEN 5 AND 14
                THEN '5-14'
            WHEN TRY_CAST(c.age AS INTEGER) BETWEEN 15 AND 24
                THEN '15-24'
            WHEN TRY_CAST(c.age AS INTEGER) BETWEEN 25 AND 44
                THEN '25-44'
            WHEN TRY_CAST(c.age AS INTEGER) BETWEEN 45 AND 64
                THEN '45-64'
            WHEN TRY_CAST(c.age AS INTEGER) BETWEEN 65 AND 84
                THEN '65-84'
            WHEN TRY_CAST(c.age AS INTEGER) BETWEEN 85 AND 110
                THEN '85+'
            ELSE NULL
        END AS age_group,

        -- Corrected gender mapping
        CASE
            WHEN LOWER(TRIM(c.gender)) = 'female'
                THEN 'Female'
            WHEN LOWER(TRIM(c.gender)) = 'male'
                THEN 'Male'
            ELSE NULL
        END AS sex_group,

        -- Corrected ethnicity mapping
        CASE
            WHEN LOWER(TRIM(c.ethnicity)) = 'hispanic or latino'
                THEN 'Hispanic'
            WHEN LOWER(TRIM(c.ethnicity)) = 'non-hispanic or latino'
                THEN 'Non-Hispanic'
            ELSE NULL
        END AS ethnicity_group

    FROM communicable_sti_db_raw.raw_cdess_sti_opencsv c

    CROSS JOIN latest_extract le

    LEFT JOIN
        communicable_sti_db_reference.ref_communicable_sti_disease_mapping d
        ON TRIM(c.diseasename) = TRIM(d.disease_name)

    WHERE
        TRY_CAST(c.casestatus AS INTEGER) IN (1, 2)
        AND (
            TRY_CAST(c.extract_year AS INTEGER) * 100
            + TRY_CAST(c.extract_month AS INTEGER)
        ) = le.latest_extract_yyyymm
),

stratified_counts AS (

    -- Total cases
    SELECT
        disease_name,
        disease_group,
        'Total' AS demographic_type,
        'Total' AS demographic_group,
        COUNT(*) AS case_count,
        geographic_area,
        case_year

    FROM eligible_cases

    GROUP BY
        disease_name,
        disease_group,
        geographic_area,
        case_year

    UNION ALL

    -- Age-specific cases
    SELECT
        disease_name,
        disease_group,
        'age' AS demographic_type,
        age_group AS demographic_group,
        COUNT(*) AS case_count,
        geographic_area,
        case_year

    FROM eligible_cases

    WHERE age_group IS NOT NULL

    GROUP BY
        disease_name,
        disease_group,
        age_group,
        geographic_area,
        case_year

    UNION ALL

    -- Sex-specific cases
    SELECT
        disease_name,
        disease_group,
        'sex' AS demographic_type,
        sex_group AS demographic_group,
        COUNT(*) AS case_count,
        geographic_area,
        case_year

    FROM eligible_cases

    WHERE sex_group IS NOT NULL

    GROUP BY
        disease_name,
        disease_group,
        sex_group,
        geographic_area,
        case_year

    UNION ALL

    -- Ethnicity-specific cases
    SELECT
        disease_name,
        disease_group,
        'ethnicity' AS demographic_type,
        ethnicity_group AS demographic_group,
        COUNT(*) AS case_count,
        geographic_area,
        case_year

    FROM eligible_cases

    WHERE ethnicity_group IS NOT NULL

    GROUP BY
        disease_name,
        disease_group,
        ethnicity_group,
        geographic_area,
        case_year
),

denominators AS (

    SELECT
        LOWER(TRIM(geographic_area)) AS geographic_area,
        TRY_CAST(year AS INTEGER) AS year,
        LOWER(TRIM(demographic_type)) AS demographic_type,
        LOWER(TRIM(demographic_group)) AS demographic_group,

        MAX(
            CASE
                WHEN LOWER(TRIM(estimate_type)) LIKE '%1%year%'
                    THEN TRY_CAST(population AS BIGINT)
            END
        ) AS population_1_year,

        MAX(
            CASE
                WHEN LOWER(TRIM(estimate_type)) LIKE '%5%year%'
                    THEN TRY_CAST(population AS BIGINT)
            END
        ) AS population_5_year

    FROM communicable_db_reference.ref_demographics

    GROUP BY
        LOWER(TRIM(geographic_area)),
        TRY_CAST(year AS INTEGER),
        LOWER(TRIM(demographic_type)),
        LOWER(TRIM(demographic_group))
),

wide_rates AS (

    SELECT
        c.disease_name,

        CONCAT(
            c.disease_name,
            ' Incidence Rate per 100,000'
        ) AS indicator_title,

        c.disease_group,
        c.demographic_type,
        c.demographic_group,
        c.case_count,

        d.population_1_year,

        ROUND(
            (
                CAST(c.case_count AS DOUBLE)
                /
                NULLIF(CAST(d.population_1_year AS DOUBLE), 0)
            ) * 100000,
            2
        ) AS incidence_rate_1_year,

        d.population_5_year,

        ROUND(
            (
                CAST(c.case_count AS DOUBLE)
                /
                NULLIF(CAST(d.population_5_year AS DOUBLE), 0)
            ) * 100000,
            2
        ) AS incidence_rate_5_year,

        c.geographic_area,
        c.case_year

    FROM stratified_counts c

    LEFT JOIN denominators d
        ON LOWER(TRIM(c.geographic_area)) = d.geographic_area
        AND c.case_year = d.year
        AND LOWER(TRIM(c.demographic_type)) = d.demographic_type
        AND LOWER(TRIM(c.demographic_group)) = d.demographic_group
),

long_rates AS (

    -- ACS 1-Year estimates
    SELECT
        disease_name,
        indicator_title,
        disease_group,
        demographic_type,
        demographic_group,
        case_count,

        '1-Year' AS estimate_type,
        population_1_year AS population,
        incidence_rate_1_year AS incidence_rate,

        geographic_area,
        case_year

    FROM wide_rates

    UNION ALL

    -- ACS 5-Year estimates
    SELECT
        disease_name,
        indicator_title,
        disease_group,
        demographic_type,
        demographic_group,
        case_count,

        '5-Year' AS estimate_type,
        population_5_year AS population,
        incidence_rate_5_year AS incidence_rate,

        geographic_area,
        case_year

    FROM wide_rates
)

SELECT
    disease_name,
    indicator_title,
    disease_group,
    demographic_type,
    demographic_group,
    case_count,
    estimate_type,
    population,
    incidence_rate,
    geographic_area,
    case_year

FROM long_rates

"""


def delete_prefix(bucket, prefix):
    paginator = s3.get_paginator("list_objects_v2")
    to_delete = []

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            to_delete.append({"Key": obj["Key"]})

            if len(to_delete) == 1000:
                s3.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": to_delete}
                )
                to_delete = []

    if to_delete:
        s3.delete_objects(
            Bucket=bucket,
            Delete={"Objects": to_delete}
        )


def run_athena_query(query):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            "Database": ATHENA_DATABASE
        },
        ResultConfiguration={
            "OutputLocation": ATHENA_OUTPUT
        },
        WorkGroup=ATHENA_WORKGROUP,
    )

    query_execution_id = response["QueryExecutionId"]

    while True:
        result = athena.get_query_execution(
            QueryExecutionId=query_execution_id
        )

        state = result["QueryExecution"]["Status"]["State"]

        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break

        time.sleep(3)

    if state != "SUCCEEDED":
        reason = result["QueryExecution"]["Status"].get(
            "StateChangeReason", "Unknown"
        )

        raise RuntimeError(
            f"Athena query failed: {state}. Reason: {reason}"
        )

    return query_execution_id


def refresh_quicksight_dataset():
    ingestion_id = f"refresh-{uuid.uuid4()}"

    return quicksight.create_ingestion(
        AwsAccountId=ACCOUNT_ID,
        DataSetId=QUICKSIGHT_DATASET_ID,
        IngestionId=ingestion_id,
    )


def lambda_handler(event, context):

    print("Starting Communicable STI Disease Pipeline refresh")

    print("Repairing raw COMMUNICABLE_STI table partitions")
    run_athena_query(
        "MSCK REPAIR TABLE communicable_sti_db_raw.raw_cdess_sti_opencsv"
    )
    print("Raw Communicable_STI partitions repaired")

    print("Dropping OLD communicable_sti_disease_incidence table")
    run_athena_query(
    "DROP TABLE IF EXISTS communicable_sti_db_curated.communicable_sti_disease_incidence"
    )

    print(f"Deleting S3 prefix: s3://{BUCKET}/{CURATED_PREFIX}")
    delete_prefix(BUCKET, CURATED_PREFIX)

    print("Creating NEW communicable_sti_disease_incidence table")
    run_athena_query(COMMUNICABLE_STI_DISEASE_SQL)
    print("communicable_sti_disease_incidence table created")

    print("Starting QuickSight dataset refresh")
    ingestion_response = refresh_quicksight_dataset()
    print("QuickSight dataset refresh started")

    print("Communicable STI Disease Public Health Pipeline refresh complete")

    return {
        "status": "success",
        "message": "Public health pipeline refreshed successfully.",
        "quicksight_ingestion": ingestion_response.get("Ingestion", {}),
    }
