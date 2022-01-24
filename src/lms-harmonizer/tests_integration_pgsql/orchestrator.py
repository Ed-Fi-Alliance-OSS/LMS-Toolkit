# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import subprocess
from os import environ, path, listdir
from platform import uname
from tests_integration_pgsql.server_config import ServerConfig
from typing import List


TEMPORARY_DATABASE = "harmonizer_temp"


# TODO: consider unifying some of this code between the two test libraries.
def _run(config: ServerConfig, command: List[str]):

    command_as_string: str = " ".join(command)
    print(f"\033[95m{command_as_string}\033[0m")

    # Some system configurations on Windows-based CI servers have trouble
    # finding poetry, others do not. Explicitly calling "cmd /c" seems to help,
    # though unsure why. Using `uname` instead of `os.name` because it correctly
    # recognizes Windows Subsystem for Linux (whereas `os.name` reports "nt").
    if uname().system == "Windows":
        command = ["cmd", "/c", *command]

    # TODO: make sure that .pgpass file can be used instead, since postgresql doesn't recommend
    # using an environment variable, and .pgpass is the only other option for unattended
    # execution of `psql`
    env = environ.copy()
    env["PGPASSWORD"] = config.password

    result = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
    )
    stdout, stderr = result.communicate()

    if result.returncode != 0:
        raise Exception("Command failed %d %a %a" % (result.returncode, stdout, stderr))


def run_harmonizer(config: ServerConfig):
    _run(
        config,
        [
            "poetry",
            "run",
            "python",
            "edfi_lms_harmonizer",
            "--server",
            config.server,
            "--port",
            config.port,
            "--dbname",
            config.db_name,
            "--username",
            config.username,
            "--password",
            config.password,
            "--engine",
            "postgresql",
        ],
    )


def _psql_parameters_from(config: ServerConfig) -> List[str]:
    return [
        "-b",  # Print failed SQL commands to standard error output.
        "-h",
        config.server,
        "-p",
        config.port,
        "-U",
        config.username,
        "",
    ]


def _execute_sql_against_master(config: ServerConfig, sql: str):
    _run(
        config,
        [config.psql_cli, *_psql_parameters_from(config), "-d", "postgres" "-c", sql],
    )


def _execute_sql_file_against_database(config: ServerConfig, filename: str):
    _run(
        config,
        [
            config.psql_cli,
            *_psql_parameters_from(config),
            "-d",
            config.db_name,
            "-f",
            filename,
        ],
    )


def _edfi_script_path(script_name: str) -> str:
    return path.normpath(
        path.join(
            path.dirname(__file__),
            "..",
            "..",
            "..",
            "utils",
            "ods-core-sql-5.2",
            "postgresql",
            script_name,
        )
    )


def _load_edfi_scripts(config: ServerConfig):
    _execute_sql_file_against_database(config, _edfi_script_path("0010-Schemas.sql"))
    _execute_sql_file_against_database(config, _edfi_script_path("0020-Tables.sql"))
    # Note - intentionally not running foreign key scripts


def _lms_extension_script_path(script_name: str) -> str:
    return path.normpath(
        path.join(
            path.dirname(__file__),
            "..",
            "..",
            "..",
            "extension",
            "EdFi.Ods.Extensions.LMSX",
            "Artifacts",
            "PgSql",
            "Structure",
            "Ods",
            script_name,
        )
    )


def _load_lms_extension_scripts(config: ServerConfig):
    _execute_sql_file_against_database(
        config,
        _lms_extension_script_path("0010-EXTENSION-LMSX-Schemas.sql"),
    )
    _execute_sql_file_against_database(
        config,
        _lms_extension_script_path("0020-EXTENSION-LMSX-Tables.sql"),
    )
    # Note - intentionally not running foreign key scripts


def _load_ordered_scripts(config: ServerConfig, script_path: str):
    files_in_path: List[str] = [
        f
        for f in listdir(script_path)
        if path.isfile(path.join(script_path, f))
    ]
    scripts: List[str] = list(
        map(lambda script: path.join(script_path, script), files_in_path)
    )
    for script in sorted(scripts):
        _execute_sql_file_against_database(config, script)


def _lms_migration_script_path() -> str:
    return path.normpath(
        path.join(
            path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "lms-ds-loader",
            "edfi_lms_ds_loader",
            "scripts",
            "postgresql",
        )
    )


def _load_lms_migration_scripts(config: ServerConfig):
    _load_ordered_scripts(config, _lms_migration_script_path())


def delete_snapshot(config: ServerConfig):
    _execute_sql_against_master(config, "drop database if exists {TEMPORARY_DATABASE}")


def _create_temporary_db_from_template(config):
    _execute_sql_against_master(
        config, f"create database {TEMPORARY_DATABASE} from template {config.db_name}"
    )


def initialize_database(config: ServerConfig):
    _execute_sql_against_master(
        config,
        "drop database if exists {config.db_name};"
        f"drop database if exists {TEMPORARY_DATABASE};"
        f"create database {config.db_name};",
    )
    # These commands are loading scripts into a template database
    _load_edfi_scripts(config)
    _load_lms_extension_scripts(config)
    _load_lms_migration_scripts(config)

    # Now we create a temporary database from the template, so that
    # we can easily tear it down and create another from the template
    # later on.
    _create_temporary_db_from_template(config)
