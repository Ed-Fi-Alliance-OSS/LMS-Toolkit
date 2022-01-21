# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.


def truncate_stg_table(table: str) -> str:
    return f"TRUNCATE TABLE lms.stg_{table} RESTART IDENTITY;".lower()


def drop_staging_natural_key_index(table: str) -> str:
    return f"DROP INDEX IF EXISTS lms.ix_stg_{table}_natural_key;".lower()


def recreate_staging_natural_key_index(table: str) -> str:
    lowercase_table = table.lower()

    return (
        f"CREATE INDEX ix_stg_{lowercase_table}_natural_key ON lms.stg_{lowercase_table} (SourceSystemIdentifier, SourceSystem);"
        if lowercase_table == "assignmentsubmissiontype"
        else f"CREATE INDEX ix_stg_{lowercase_table}_natural_key ON lms.stg_{lowercase_table} (SourceSystemIdentifier, SourceSystem, LastModifiedDate);"
    )


def insert_new_records_to_production(table: str, column_string: str) -> str:
    return f"""
INSERT INTO
    lms.{table}
({column_string}
)
SELECT{column_string}
FROM
    lms.stg_{table} as stg
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            lms.{table}
        WHERE
            SourceSystemIdentifier = stg.SourceSystemIdentifier
        AND
            SourceSystem = stg.SourceSystem
    )
""".lower()


def insert_new_records_to_production_for_user_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    return f"""
INSERT INTO
    lms.{table}
(
    LMSUserIdentifier,{insert_columns}
)
SELECT
    LMSUser.LMSUserIdentifier,{select_columns}
FROM
    lms.stg_{table} as stg
INNER JOIN
    lms.LMSUser
ON
    stg.LMSUserSourceSystemIdentifier = LMSUser.SourceSystemIdentifier
AND
    stg.SourceSystem = LMSUser.SourceSystem
WHERE NOT EXISTS (
  SELECT
    1
  FROM
    lms.{table}
  WHERE
    SourceSystemIdentifier = stg.SourceSystemIdentifier
  AND
    SourceSystem = stg.SourceSystem
)
""".lower()


def insert_new_records_to_production_for_assignment_and_user_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    return f"""
INSERT INTO
    lms.{table}
(
    AssignmentIdentifier,
    LMSUserIdentifier,{insert_columns}
)
SELECT
    Assignment.AssignmentIdentifier,
    LMSUser.LMSUserIdentifier,{select_columns}
FROM
    lms.stg_{table} as stg
INNER JOIN
    lms.Assignment
ON
    stg.AssignmentSourceSystemIdentifier = Assignment.SourceSystemIdentifier
AND
    stg.SourceSystem = Assignment.SourceSystem
INNER JOIN
    lms.LMSUser
ON
    stg.LMSUserSourceSystemIdentifier = LMSUser.SourceSystemIdentifier
AND
    stg.SourceSystem = LMSUser.SourceSystem
WHERE NOT EXISTS (
  SELECT
    1
  FROM
    lms.{table}
  WHERE
    SourceSystemIdentifier = stg.SourceSystemIdentifier
  AND
    SourceSystem = stg.SourceSystem
)
""".lower()


def insert_new_records_to_production_for_section_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    return f"""
INSERT INTO
    lms.{table}
(
    LMSSectionIdentifier,{insert_columns}
)
SELECT
    LMSSection.LMSSectionIdentifier,{select_columns}
FROM
    lms.stg_{table} as stg
INNER JOIN
    lms.LMSSection
ON
    stg.LMSSectionSourceSystemIdentifier = LMSSection.SourceSystemIdentifier
AND
    stg.SourceSystem = LMSSection.SourceSystem
WHERE NOT EXISTS (
  SELECT
    1
  FROM
    lms.{table}
  WHERE
    SourceSystemIdentifier = stg.SourceSystemIdentifier
  AND
    SourceSystem = stg.SourceSystem
)
""".lower()


def insert_new_records_to_production_for_section_and_user_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    return f"""
INSERT INTO
    lms.{table}
(
    LMSSectionIdentifier,
    LMSUserIdentifier,{insert_columns}
)
SELECT
    LMSSection.LMSSectionIdentifier,
    LMSUser.LMSUserIdentifier,{select_columns}
FROM
    lms.stg_{table} as stg
INNER JOIN
    lms.LMSSection
ON
    stg.LMSSectionSourceSystemIdentifier = LMSSection.SourceSystemIdentifier
AND
    stg.SourceSystem = LMSSection.SourceSystem
INNER JOIN
    lms.LMSUser
ON
    stg.LMSUserSourceSystemIdentifier = LMSUser.SourceSystemIdentifier
AND
    stg.SourceSystem = LMSUser.SourceSystem
WHERE NOT EXISTS (
  SELECT
    1
  FROM
    lms.{table}
  WHERE
    SourceSystemIdentifier = stg.SourceSystemIdentifier
  AND
    SourceSystem = stg.SourceSystem
)
""".lower()


def copy_updates_to_production(table: str, update_columns: str) -> str:
    return f"""
UPDATE
    lms.{table}
SET{update_columns}
FROM
    lms.{table} t
INNER JOIN
    lms.stg_{table} as stg
ON
    t.SourceSystem = stg.SourceSystem
AND
    t.SourceSystemIdentifier = stg.SourceSystemIdentifier
AND
    t.LastModifiedDate <> stg.LastModifiedDate
WHERE
    t.SourceSystemIdentifier = lms.{table}.SourceSystemIdentifier
AND
    t.SourceSystem = lms.{table}.SourceSystem
""".lower()


def soft_delete_from_production(table: str, source_system: str) -> str:
    return f"""
UPDATE
    lms.{table}
SET
    DeletedAt = Now()
FROM
    lms.{table} as t
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            lms.stg_{table} as stg
        WHERE
            t.SourceSystemIdentifier = stg.SourceSystemIdentifier
        AND
            t.SourceSystem = stg.SourceSystem
    )
AND
    t.DeletedAt IS NULL
AND
    t.SourceSystem = '{source_system}'
AND
    lms.{table}.SourceSystem = t.SourceSystem
AND
    lms.{table}.SourceSystemIdentifier= t.SourceSystemIdentifier
""".lower()


def soft_delete_from_production_for_section_relation(
    table: str, source_system: str
) -> str:
    return f"""
UPDATE
    lms.{table}
SET
    DeletedAt = now()
FROM
    lms.{table} as t
WHERE
    t.LMSSectionIdentifier IN (
        SELECT
            s.LMSSectionIdentifier
        FROM
           lms.LMSSection as s
        INNER JOIN
            lms.stg_{table} as stg
        ON
            stg.LMSSectionSourceSystemIdentifier = s.SourceSystemIdentifier
        AND
            stg.SourceSystem = s.SourceSystem
    )
AND
    NOT EXISTS (
        SELECT
            1
        FROM
            lms.stg_{table} as stg
        WHERE
            t.SourceSystemIdentifier = stg.SourceSystemIdentifier
        AND
            t.SourceSystem = stg.SourceSystem
    )
AND
    -- PostgreSQL self-join update statement needs to limit to the matching record
    lms.{table}.{table}Identifier = t.{table}Identifier
AND
    t.DeletedAt IS NULL
AND
    t.SourceSystem = '{source_system}'
""".lower()


def soft_delete_from_production_for_assignment_relation(
    table: str, source_system: str
) -> str:
    return f"""
UPDATE
    lms.{table}
SET
    DeletedAt = now()
FROM
    lms.{table} as t
WHERE
    t.AssignmentIdentifier IN (
        SELECT
            a.AssignmentIdentifier
        FROM
           lms.Assignment as a
        INNER JOIN
            lms.stg_{table} as stg
        ON
            stg.AssignmentSourceSystemIdentifier = a.SourceSystemIdentifier
        AND
            stg.SourceSystem = a.SourceSystem
    )
AND
    NOT EXISTS (
        SELECT
            1
        FROM
            lms.stg_{table} as stg
        WHERE
            t.SourceSystemIdentifier = stg.SourceSystemIdentifier
        AND
            t.SourceSystem = stg.SourceSystem
    )
AND
    -- PostgreSQL self-join update statement needs to limit to the matching record
    lms.{table}.{table}Identifier = t.{table}Identifier
AND
    t.DeletedAt IS NULL
AND
    t.SourceSystem = '{source_system}'
""".lower()


def insert_new_submission_types() -> str:
    return """
INSERT INTO lms.AssignmentSubmissionType (
    AssignmentIdentifier,
    SubmissionType
)
SELECT
    lms.Assignment.AssignmentIdentifier,
    lms.stg_AssignmentSubmissionType.SubmissionType
FROM
    lms.stg_AssignmentSubmissionType
    INNER JOIN
        lms.Assignment
    ON
        lms.stg_AssignmentSubmissionType.SourceSystem = lms.Assignment.SourceSystem
    AND
        lms.stg_AssignmentSubmissionType.SourceSystemIdentifier = lms.Assignment.SourceSystemIdentifier
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            lms.AssignmentSubmissionType
        WHERE
            AssignmentIdentifier = lms.Assignment.AssignmentIdentifier
        AND
            SubmissionType = lms.stg_AssignmentSubmissionType.SubmissionType
    )
""".lower()


def soft_delete_removed_submission_types(source_system: str) -> str:
    return f"""
UPDATE
    lms.AssignmentSubmissionType as upd
SET
    DeletedAt = now()
FROM
    lms.AssignmentSubmissionType
INNER JOIN
    lms.Assignment
ON
    lms.AssignmentSubmissionType.AssignmentIdentifier = lms.Assignment.AssignmentIdentifier
WHERE
    SourceSystem = '{source_system}'
AND
    NOT EXISTS (
        SELECT
            1
        FROM
            lms.stg_AssignmentSubmissionType
        WHERE
            stg_AssignmentSubmissionType.SourceSystem = Assignment.SourceSystem
        AND
            stg_AssignmentSubmissionType.SourceSystemIdentifier = Assignment.SourceSystemIdentifier
        AND
            stg_AssignmentSubmissionType.SubmissionType = AssignmentSubmissionType.SubmissionType
    )
-- PostgreSQL self-join update statement needs to limit to the matching record
AND
    upd.AssignmentIdentifier = lms.AssignmentSubmissionType.AssignmentIdentifier
AND
    upd.SubmissionType = lms.AssignmentSubmissionType.SubmissionType
"""


def unsoft_delete_returned_submission_types(source_system: str) -> str:
    return f"""
UPDATE
    lms.AssignmentSubmissionType as upd
SET
    DeletedAt = NULL
FROM
    lms.AssignmentSubmissionType
INNER JOIN
    lms.Assignment
ON
    lms.AssignmentSubmissionType.AssignmentIdentifier = lms.Assignment.AssignmentIdentifier
WHERE
    SourceSystem = '{source_system}'
AND
    EXISTS (
        SELECT
            1
        FROM
            lms.stg_AssignmentSubmissionType
        WHERE
            lms.stg_AssignmentSubmissionType.SourceSystem = lms.Assignment.SourceSystem
        AND
            lms.stg_AssignmentSubmissionType.SourceSystemIdentifier = lms.Assignment.SourceSystemIdentifier
        AND
            lms.stg_AssignmentSubmissionType.SubmissionType = lms.AssignmentSubmissionType.SubmissionType
    )
-- PostgreSQL self-join update statement needs to limit to the matching record
AND
    upd.AssignmentIdentifier = lms.AssignmentSubmissionType.AssignmentIdentifier
AND
    upd.SubmissionType = lms.AssignmentSubmissionType.SubmissionType
"""


def get_processed_files(resource_name: str) -> str:
    return f"""
SELECT
    fullpath
FROM
    lms.ProcessedFiles
WHERE
    ResourceName = '{resource_name}'
""".lower()


def add_processed_file(path: str, resource_name: str, rows: int) -> str:
    return f"""
INSERT INTO
    lms.ProcessedFiles
(
    FullPath,
    ResourceName,
    NumberOfRows
)
VALUES
(
    '{path}',
    '{resource_name}',
    {rows}
)
""".lower()
