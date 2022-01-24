# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.


def truncate_stg_table(table: str) -> str:
    return f"truncate table lms.stg_{table} restart identity;".lower()


def drop_staging_natural_key_index(table: str) -> str:
    return f"drop index if exists lms.ix_stg_{table}_natural_key;".lower()


def recreate_staging_natural_key_index(table: str) -> str:
    lowercase_table = table.lower()

    return (
        f"create index ix_stg_{lowercase_table}_natural_key on lms.stg_{lowercase_table} (sourcesystemidentifier, sourcesystem);"
        if lowercase_table == "assignmentsubmissiontype"
        else f"create index ix_stg_{lowercase_table}_natural_key on lms.stg_{lowercase_table} (sourcesystemidentifier, sourcesystem, lastmodifieddate);"
    )


def insert_new_records_to_production(table: str, column_string: str) -> str:
    lower_table = table.lower()
    lower_column_string = column_string.lower()

    return f"""
insert into
    lms.{lower_table}
({lower_column_string}
)
select {lower_column_string}
from
    lms.stg_{lower_table} as stg
where
    not exists (
        select
            1
        from
            lms.{lower_table}
        where
            sourcesystemidentifier = stg.sourcesystemidentifier
        and
            sourcesystem = stg.sourcesystem
    )
"""


def insert_new_records_to_production_for_user_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    lower_table = table.lower()
    lower_insert_columns = insert_columns.lower()
    lower_select_columns = select_columns.lower()

    return f"""
insert into
    lms.{lower_table}
(
    lmsuseridentifier,{lower_insert_columns}
)
select
    lmsuser.lmsuseridentifier,{lower_select_columns}
from
    lms.stg_{lower_table} as stg
inner join
    lms.lmsuser
on
    stg.lmsusersourcesystemidentifier = lmsuser.sourcesystemidentifier
and
    stg.sourcesystem = lmsuser.sourcesystem
where not exists (
  select
    1
  from
    lms.{lower_table}
  where
    sourcesystemidentifier = stg.sourcesystemidentifier
  and
    sourcesystem = stg.sourcesystem
)
"""


def insert_new_records_to_production_for_assignment_and_user_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    lower_table = table.lower()
    lower_insert_columns = insert_columns.lower()
    lower_select_columns = select_columns.lower()

    return f"""
insert into
    lms.{lower_table}
(
    assignmentidentifier,
    lmsuseridentifier,{lower_insert_columns}
)
select
    assignment.assignmentidentifier,
    lmsuser.lmsuseridentifier,{lower_select_columns}
from
    lms.stg_{lower_table} as stg
inner join
    lms.assignment
on
    stg.assignmentsourcesystemidentifier = assignment.sourcesystemidentifier
and
    stg.sourcesystem = assignment.sourcesystem
inner join
    lms.lmsuser
on
    stg.lmsusersourcesystemidentifier = lmsuser.sourcesystemidentifier
and
    stg.sourcesystem = lmsuser.sourcesystem
where not exists (
  select
    1
  from
    lms.{lower_table}
  where
    sourcesystemidentifier = stg.sourcesystemidentifier
  and
    sourcesystem = stg.sourcesystem
)
""".lower()
def insert_new_records_to_production_for_section_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    lower_table = table.lower()
    lower_insert_columns = insert_columns.lower()
    lower_select_columns = select_columns.lower()

    return f"""
insert into
    lms.{lower_table}
(
    lmssectionidentifier,{lower_insert_columns}
)
select
    lmssection.lmssectionidentifier,{lower_select_columns}
from
    lms.stg_{lower_table} as stg
inner join
    lms.lmssection
on
    stg.lmssectionsourcesystemidentifier = lmssection.sourcesystemidentifier
and
    stg.sourcesystem = lmssection.sourcesystem
where not exists (
  select
    1
  from
    lms.{lower_table}
  where
    sourcesystemidentifier = stg.sourcesystemidentifier
  and
    sourcesystem = stg.sourcesystem
)
"""


def insert_new_records_to_production_for_section_and_user_relation(
    table: str, insert_columns: str, select_columns: str
) -> str:
    lower_table = table.lower()
    lower_insert_columns = insert_columns.lower()
    lower_select_columns = select_columns.lower()

    return f"""
insert into
    lms.{lower_table}
(
    lmssectionidentifier,
    lmsuseridentifier,{lower_insert_columns}
)
select
    lmssection.lmssectionidentifier,
    lmsuser.lmsuseridentifier,{lower_select_columns}
from
    lms.stg_{lower_table} as stg
inner join
    lms.lmssection
on
    stg.lmssectionsourcesystemidentifier = lmssection.sourcesystemidentifier
and
    stg.sourcesystem = lmssection.sourcesystem
inner join
    lms.lmsuser
on
    stg.lmsusersourcesystemidentifier = lmsuser.sourcesystemidentifier
and
    stg.sourcesystem = lmsuser.sourcesystem
where not exists (
  select
    1
  from
    lms.{lower_table}
  where
    sourcesystemidentifier = stg.sourcesystemidentifier
  and
    sourcesystem = stg.sourcesystem
)




def insert_new_records_to_production_for_attendance_events(
    insert_columns: str, select_columns: str
) -> str:
    return f"""
INSERT INTO
    lms.LMSUserAttendanceEvent
(
    LMSSectionIdentifier,
    LMSUserIdentifier,
    LMSUserLMSSectionAssociationIdentifier,{insert_columns}
)
SELECT
    LMSSection.LMSSectionIdentifier,
    LMSUser.LMSUserIdentifier,
    LMSUserLMSSectionAssociation.LMSUserLMSSectionAssociationIdentifier,{select_columns}
FROM
    lms.stg_LMSUserAttendanceEvent as stg
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
INNER JOIN
    lms.LMSUserLMSSectionAssociation
ON
    LMSUser.LMSUserIdentifier = LMSUserLMSSectionAssociation.LMSUserIdentifier
AND
    LMSSection.LMSSectionIdentifier = LMSUserLMSSectionAssociation.LMSSectionIdentifier
WHERE NOT EXISTS (
  SELECT
    1
  FROM
    lms.LMSUserAttendanceEvent
  where
    sourcesystemidentifier = stg.sourcesystemidentifier
  and
    sourcesystem = stg.sourcesystem
)
"""


def copy_updates_to_production(table: str, update_columns: str) -> str:
    lower_table = table.lower()
    lower_update_columns = update_columns.lower()

    return f"""
update
    lms.{lower_table}
set {lower_update_columns}
from
    lms.{lower_table} t
inner join
    lms.stg_{lower_table} as stg
on
    t.sourcesystem = stg.sourcesystem
and
    t.sourcesystemidentifier = stg.sourcesystemidentifier
and
    t.lastmodifieddate <> stg.lastmodifieddate
where
    t.sourcesystemidentifier = lms.{lower_table}.sourcesystemidentifier
and
    t.sourcesystem = lms.{lower_table}.sourcesystem
"""


def soft_delete_from_production(table: str, source_system: str) -> str:
    lower_table = table.lower()

    return f"""
update
    lms.{lower_table}
set
    deletedat = now()
from
    lms.{lower_table} as t
where
    not exists (
        select
            1
        from
            lms.stg_{lower_table} as stg
        where
            t.sourcesystemidentifier = stg.sourcesystemidentifier
        and
            t.sourcesystem = stg.sourcesystem
    )
and
    t.deletedat is null
and
    t.sourcesystem = '{source_system}'
and
    lms.{lower_table}.sourcesystem = t.sourcesystem
and
    lms.{lower_table}.sourcesystemidentifier = t.sourcesystemidentifier
"""


def soft_delete_from_production_for_section_relation(
    table: str, source_system: str
) -> str:
    lower_table = table.lower()

    return f"""
update
    lms.{lower_table}
set
    deletedat = now()
from
    lms.{lower_table} as t
where
    t.lmssectionidentifier in (
        select
            s.lmssectionidentifier
        from
           lms.lmssection as s
        inner join
            lms.stg_{lower_table} as stg
        on
            stg.lmssectionsourcesystemidentifier = s.sourcesystemidentifier
        and
            stg.sourcesystem = s.sourcesystem
    )
and
    not exists (
        select
            1
        from
            lms.stg_{lower_table} as stg
        where
            t.sourcesystemidentifier = stg.sourcesystemidentifier
        and
            t.sourcesystem = stg.sourcesystem
    )
AND
    -- PostgreSQL self-join update statement needs to limit to the matching record
    lms.{lower_table}.{lower_table}Identifier = t.{lower_table}Identifier
AND
    t.DeletedAt IS NULL
AND
    t.SourceSystem = '{source_system}'
"""


def soft_delete_from_production_for_assignment_relation(
    table: str, source_system: str
) -> str:
    lower_table = table.lower()

    return f"""
update
    lms.{lower_table}
set
    deletedat = now()
from
    lms.{lower_table} as t
where
    t.assignmentidentifier in (
        select
            a.assignmentidentifier
        from
           lms.assignment as a
        inner join
            lms.stg_{lower_table} as stg
        on
            stg.assignmentsourcesystemidentifier = a.sourcesystemidentifier
        and
            stg.sourcesystem = a.sourcesystem
    )
and
    not exists (
        select
            1
        from
            lms.stg_{lower_table} as stg
        where
            t.sourcesystemidentifier = stg.sourcesystemidentifier
        and
            t.sourcesystem = stg.sourcesystem
    )
AND
    -- PostgreSQL self-join update statement needs to limit to the matching record
    lms.{lower_table}.{lower_table}Identifier = t.{lower_table}Identifier
AND
    t.DeletedAt IS NULL
AND
    t.SourceSystem = '{source_system}'
"""


def insert_new_submission_types() -> str:
    return """
insert into lms.assignmentsubmissiontype (
    assignmentidentifier,
    submissiontype
)
select
    lms.assignment.assignmentidentifier,
    lms.stg_assignmentsubmissiontype.submissiontype
from
    lms.stg_assignmentsubmissiontype
    inner join
        lms.assignment
    on
        lms.stg_assignmentsubmissiontype.sourcesystem = lms.assignment.sourcesystem
    and
        lms.stg_assignmentsubmissiontype.sourcesystemidentifier = lms.assignment.sourcesystemidentifier
where
    not exists (
        select
            1
        from
            lms.assignmentsubmissiontype
        where
            assignmentidentifier = lms.assignment.assignmentidentifier
        and
            submissiontype = lms.stg_assignmentsubmissiontype.submissiontype
    )
"""


def soft_delete_removed_submission_types(source_system: str) -> str:
    return f"""
update
    lms.assignmentsubmissiontype as upd
set
    deletedat = now()
from
    lms.assignmentsubmissiontype
inner join
    lms.assignment
on
    lms.assignmentsubmissiontype.assignmentidentifier = lms.assignment.assignmentidentifier
where
    sourcesystem = '{source_system}'
and
    not exists (
        select
            1
        from
            lms.stg_assignmentsubmissiontype
        where
            stg_assignmentsubmissiontype.sourcesystem = assignment.sourcesystem
        and
            stg_assignmentsubmissiontype.sourcesystemidentifier = assignment.sourcesystemidentifier
        and
            stg_assignmentsubmissiontype.submissiontype = assignmentsubmissiontype.submissiontype
    )
-- postgresql self-join update statement needs to limit to the matching record
and
    upd.assignmentidentifier = lms.assignmentsubmissiontype.assignmentidentifier
and
    upd.submissiontype = lms.assignmentsubmissiontype.submissiontype
"""


def unsoft_delete_returned_submission_types(source_system: str) -> str:
    return f"""
update
    lms.assignmentsubmissiontype as upd
set
    deletedat = null
from
    lms.assignmentsubmissiontype
inner join
    lms.assignment
on
    lms.assignmentsubmissiontype.assignmentidentifier = lms.assignment.assignmentidentifier
where
    sourcesystem = '{source_system}'
and
    exists (
        select
            1
        from
            lms.stg_assignmentsubmissiontype
        where
            lms.stg_assignmentsubmissiontype.sourcesystem = lms.assignment.sourcesystem
        and
            lms.stg_assignmentsubmissiontype.sourcesystemidentifier = lms.assignment.sourcesystemidentifier
        and
            lms.stg_assignmentsubmissiontype.submissiontype = lms.assignmentsubmissiontype.submissiontype
    )
-- postgresql self-join update statement needs to limit to the matching record
and
    upd.assignmentidentifier = lms.assignmentsubmissiontype.assignmentidentifier
and
    upd.submissiontype = lms.assignmentsubmissiontype.submissiontype
"""


def get_processed_files(resource_name: str) -> str:
    return f"""
select
    fullpath
from
    lms.processedfiles
where
    resourcename = '{resource_name}'
"""


def add_processed_file(path: str, resource_name: str, rows: int) -> str:
    return f"""
insert into
    lms.processedfiles
(
    fullpath,
    resourcename,
    numberofrows
)
values
(
    '{path}',
    '{resource_name}',
    {rows}
)
"""
