# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import logging
from os import path, scandir
from typing import List

from sqlalchemy.exc import ProgrammingError
from sqlparse import split

from edfi_sql_adapter.sql_adapter import Adapter, Statement
from edfi_lms_ds_loader.helpers.constants import DbEngine


logger = logging.getLogger(__name__)


def _get_file_names(adapter: Adapter) -> List[str]:
    script_dir = path.join(path.dirname(__file__), "scripts", adapter.engine.name)
    files: List[str] = []
    with scandir(script_dir) as all_files:
        for file in all_files:
            if file.path.endswith('.sql'):
                files.append(file.path)

    files.sort()

    return files


def _read_statements_from_file(full_path: str) -> List[str]:
    raw_sql: str
    with open(full_path) as f:
        raw_sql = f.read()

    statements: List[str] = split(raw_sql)
    return statements


def _script_has_been_run(adapter: Adapter, migration: str) -> bool:
    try:
        statement = f"SELECT 1 FROM lms.migrationjournal WHERE script = '{migration}';"
        response = adapter.get_int(statement)

        return bool(response == 1)
    except ProgrammingError as error:
        if (
            # PostgreSLQ error
            "psycopg2.errors.UndefinedTable" in error.args[0]
            or
            # SQL Server error
            "Invalid object name" in error.args[0]
        ):
            # This means it is a fresh database where the migrationjournal table
            # has not been installed yet.
            return False

        raise


def _record_migration_in_journal(adapter: Adapter, migration: str) -> None:
    statement = Statement(
        f"INSERT INTO lms.migrationjournal (script) values ('{migration}');",
        "Updating migration journal table",
    )

    adapter.execute([statement])


def _mssql_lms_schema_exists(adapter: Adapter) -> bool:
    statement = """
select case when exists (
    select 1 from INFORMATION_SCHEMA.SCHEMATA where schema_name = 'lms'
) then 1 else 0 end
""".strip()

    return adapter.get_int(statement) == 1


def _pgsql_lms_schema_exists(adapter: Adapter) -> bool:
    statement = (
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'lms';"
    )

    return adapter.get_int(statement) == 1


def _run_migration_script(adapter: Adapter, migration_script: str) -> None:

    migration = migration_script.split(path.sep)[-1]

    logger.debug(f"Running migration {migration}...")

    statements = _read_statements_from_file(migration_script)
    adapter.execute_script(statements)

    _record_migration_in_journal(adapter, migration)

    logger.debug(f"Done with migration {migration}.")


def migrate(adapter: Adapter, engine: str = DbEngine.MSSQL) -> None:
    """
    Runs database migration scripts for installing LMS table schema into the
    destination database.

    Parameters
    ----------
    adapter: sql_adapter
        SQL Alchemy database engine object.
    """
    logger.info("Begin database auto-migration...")

    for migration in _get_file_names(adapter):
        # The following block of code does not belong in _run_migration_script
        # because it will throw an exception if the migration journal does not
        # exist, and therefore is not appropriate when initializing the LMS
        # database.
        if _script_has_been_run(adapter, migration):
            logger.debug(
                f"Migration {migration} has already run and will not be re-run."
            )
            continue

        _run_migration_script(adapter, migration)

    logger.info("Done with database auto-migration.")
