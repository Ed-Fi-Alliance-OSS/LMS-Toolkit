# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.
from typing import Iterator
from os import environ

import pytest
from dotenv import load_dotenv

from tests_integration_mssql.mssql_orchestrator import (
    create_snapshot,
    delete_snapshot,
    initialize_database,
    restore_snapshot,
)
from tests_integration_mssql.mssql_server_config import MssqlServerConfig

load_dotenv()


def pytest_addoption(parser):
    """
    Injects command line options mirroring the harmonizer itself
    """
    parser.addoption(
        "--server",
        action="store",
        default="localhost",
        help="Database server name or IP address",
    )
    parser.addoption(
        "--port",
        action="store",
        default=environ.get("DB_PORT", 1433),
        help="Database server port number",
    )
    parser.addoption(
        "--db_name",
        action="store",
        default=environ.get("DB_NAME", "test_harmonizer_lms_toolkit"),
        help="Name of the test database",
    )
    parser.addoption(
        "--useintegratedsecurity",
        action="store",
        default=environ.get("USE_INTEGRATED_SECURITY", True),
        help="Use Integrated Security for the database connection",
    )
    parser.addoption(
        "--username",
        action="store",
        default=environ.get("DB_USER", "sa"),
        help="Database username when not using integrated security",
    )
    parser.addoption(
        "--password",
        action="store",
        default=environ.get("DB_PASSWORD", ""),
        help="Database user password, when not using integrated security",
    )
    parser.addoption(
        "--skip-teardown",
        type=bool,
        action="store",
        default=environ.get("SKIP_TEARDOWN", False),
        help="Skip the teardown of the database. Potentially useful for debugging.",
    )


def _server_config_from(request) -> MssqlServerConfig:
    return MssqlServerConfig(
        useintegratedsecurity=request.config.getoption("--useintegratedsecurity"),
        server=request.config.getoption("--server"),
        port=request.config.getoption("--port"),
        db_name=request.config.getoption("--db_name"),
        username=request.config.getoption("--username"),
        password=request.config.getoption("--password"),
        skip_teardown=request.config.getoption("--skip-teardown"),
    )


@pytest.fixture(scope="session")
def mssql_db_config(request) -> Iterator[MssqlServerConfig]:
    """
    Fixture that wraps an engine to use with snapshot
    creation and deletion
    """
    config: MssqlServerConfig = _server_config_from(request)
    initialize_database(config)
    create_snapshot(config)

    yield config

    delete_snapshot(config)


@pytest.fixture(autouse=True)
def test_db_config(mssql_db_config: MssqlServerConfig, request) -> MssqlServerConfig:
    """
    Fixture that takes the wrapped engine and passes it along, while
    providing a finalizer hook to rollback via snapshotting after each test.
    """

    # Rollback via snapshotting in finalizer when test is done
    def finalizer():
        restore_snapshot(mssql_db_config)

    if not mssql_db_config.skip_teardown:
        request.addfinalizer(finalizer)

    return mssql_db_config
