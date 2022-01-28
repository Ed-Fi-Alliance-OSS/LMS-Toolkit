# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from tests_integration_pgsql.pgsql_loader import (
    insert_lms_assignment,
    insert_lms_section,
    insert_edfi_section,
    insert_descriptor,
    insert_lmsx_sourcesystem_descriptor,
    insert_lmsx_assignmentcategory_descriptor,
)
from tests_integration_pgsql.pgsql_connection import PgsqlConnection, query
from tests_integration_pgsql.pgsql_server_config import PgsqlServerConfig
from tests_integration_pgsql.pgsql_orchestrator import run_harmonizer


SOURCE_SYSTEM = 'Canvas'

QUERY_FOR_ASSIGNMENT_EXCEPTIONS = """
select
    count(*) as count
from
    lmsx.assignments_exceptions
"""


def descriptor_namespace_for(source_system: str) -> str:
    return f"uri://ed-fi.org/edfilms/AssignmentCategoryDescriptor/{source_system}"


def describe_when_lms_and_ods_tables_are_both_empty():
    def it_should_return_zero(test_db_config: PgsqlServerConfig):
        result = None
        # act
        run_harmonizer(test_db_config)
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:
            result = query(connection, QUERY_FOR_ASSIGNMENT_EXCEPTIONS)

        # assert
        assert result[0]['count'] == 0


def describe_when_there_are_inserted_assignments():
    SIS_SECTION_ID = "sis_section_id"
    ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER = "assignment_identifier"
    ASSIGNMENT_CATEGORY = "test_category"

    def it_should_return_zero_when_there_are_no_exceptions(
        test_db_config: PgsqlServerConfig
    ):
        descriptor_namespace = descriptor_namespace_for(SOURCE_SYSTEM)
        category_descriptor_id = 1
        source_system_descriptor_id = 2
        section_identifier = 1

        # arrange
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:

            insert_descriptor(connection, descriptor_namespace, ASSIGNMENT_CATEGORY)
            insert_lmsx_assignmentcategory_descriptor(
                connection, category_descriptor_id
            )

            insert_descriptor(connection, descriptor_namespace, SOURCE_SYSTEM)
            insert_lmsx_sourcesystem_descriptor(connection, source_system_descriptor_id)

            insert_lms_section(connection, SIS_SECTION_ID, SOURCE_SYSTEM)
            insert_edfi_section(connection, SIS_SECTION_ID)
            connection.execute(
                """update lms.lmssection set
                    edfisectionid = (select id from edfi.section limit 1)"""
            )

            insert_lms_assignment(
                connection,
                ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER,
                SOURCE_SYSTEM,
                section_identifier,
                ASSIGNMENT_CATEGORY,
            )

        # act
        run_harmonizer(test_db_config)

        # assert
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:
            result = query(connection, QUERY_FOR_ASSIGNMENT_EXCEPTIONS)

        assert result[0]['count'] == 0

    def it_should_return_one_exception_when_theres_one_exception(
        test_db_config: PgsqlServerConfig
    ):
        descriptor_namespace = descriptor_namespace_for(SOURCE_SYSTEM)
        category_descriptor_id = 1
        source_system_descriptor_id = 2
        section_identifier = 1

        # arrange
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:

            insert_descriptor(connection, descriptor_namespace, ASSIGNMENT_CATEGORY)
            insert_lmsx_assignmentcategory_descriptor(
                connection, category_descriptor_id
            )

            insert_descriptor(connection, descriptor_namespace, SOURCE_SYSTEM)
            insert_lmsx_sourcesystem_descriptor(connection, source_system_descriptor_id)

            insert_lms_section(connection, SIS_SECTION_ID, SOURCE_SYSTEM)
            insert_edfi_section(connection, SIS_SECTION_ID)
            connection.execute(
                """update lms.lmssection set
                    edfisectionid = (select id from edfi.section limit 1)"""
            )

            insert_lms_assignment(
                connection,
                ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER,
                SOURCE_SYSTEM,
                section_identifier,
                ASSIGNMENT_CATEGORY,
            )

        # act
        run_harmonizer(test_db_config)
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:
            connection.execute(
                """delete from lmsx.assignment"""
            )

        # assert
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:
            result = query(connection, QUERY_FOR_ASSIGNMENT_EXCEPTIONS)

        assert result[0]['count'] == 1


def describe_when_there_are_deleted_assignments():
    SIS_SECTION_ID = "sis_section_id"
    ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER = "assignment_identifier"
    ASSIGNMENT_CATEGORY = "test_category"

    def it_should_not_count_it_as_an_exception(
        test_db_config: PgsqlServerConfig
    ):
        # arrange
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:
            insert_descriptor(
                connection, descriptor_namespace_for(SOURCE_SYSTEM), ASSIGNMENT_CATEGORY
            )
            insert_lmsx_assignmentcategory_descriptor(connection, 1)

            insert_descriptor(
                connection, descriptor_namespace_for(SOURCE_SYSTEM), SOURCE_SYSTEM
            )
            insert_lmsx_sourcesystem_descriptor(connection, 2)

            insert_lms_section(connection, SIS_SECTION_ID, SOURCE_SYSTEM)
            insert_edfi_section(connection, SIS_SECTION_ID)
            connection.execute(
                """update lms.lmssection set
                    edfisectionid = (select id from edfi.section limit 1)"""
            )

            insert_lms_assignment(
                connection,
                ASSIGNMENT_SOURCE_SYSTEM_IDENTIFIER,
                SOURCE_SYSTEM,
                1,
                ASSIGNMENT_CATEGORY,
            )

        run_harmonizer(test_db_config)

        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:
            connection.execute(
                "update lms.assignment set lastmodifieddate = now(), deletedat = now()"
            )

        # act
        run_harmonizer(test_db_config)

        # assert
        with PgsqlConnection(test_db_config).pyodbc_conn() as connection:
            result = query(connection, QUERY_FOR_ASSIGNMENT_EXCEPTIONS)

        assert result[0]['count'] == 0
