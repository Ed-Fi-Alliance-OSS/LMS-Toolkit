# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from logging import Logger
from typing import Tuple

import pandas as pd
from pandas.core.frame import DataFrame
import pytest
from unittest.mock import Mock
import sqlalchemy

from schoology_extractor.schoology_extract_facade import SchoologyExtractFacade
from schoology_extractor.api.request_client import RequestClient
from schoology_extractor.api.paginated_result import PaginatedResult
from schoology_extractor.mapping import users as usersMap
from schoology_extractor.mapping import sections as sectionsMap
from schoology_extractor.helpers import sync


def describe_when_getting_users():
    def describe_given_one_user():
        @pytest.fixture
        def result() -> pd.DataFrame:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 22

            users = {
                "user": [{"uid": 1234, "role_id": 321}],
                "total": 1,
                "links": {"self": "ignore"},
            }
            users_page = PaginatedResult(
                request_client, page_size, users, "user", "ignore me"
            )

            roles = {"role": [{"id": 321, "title": "estudiante"}]}
            roles_page = PaginatedResult(
                request_client, page_size, roles, "role", "ignore me"
            )

            # Arrange
            request_client.get_users.return_value = users_page
            request_client.get_roles.return_value = roles_page

            # Also want to mock the UDM mapper function, since it is well-tested elsewhere
            usersMap.map_to_udm = Mock()
            usersMap.map_to_udm.return_value = pd.DataFrame()

            # This method will be tested in a different test
            sync.sync_resource = Mock(side_effect=lambda v, w, x, y='', z='': DataFrame(x))

            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            result = service.get_users()

            return result

        def it_should_return_a_data_frame(result):
            assert isinstance(result, pd.DataFrame)

    def describe_given_two_pages_of_users():
        @pytest.fixture
        def system() -> Tuple[pd.DataFrame, Mock]:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 1

            users = {
                "user": [{"uid": 1234, "role_id": 321}],
                "total": 1,
                "links": {"self": "ignore", "next": "url"},
            }
            users_2 = {
                "user": [{"uid": 1235, "role_id": 321}],
                "total": 1,
                "links": {"self": "ignore"},
            }
            users_page = PaginatedResult(
                request_client, page_size, users, "user", "ignore me"
            )

            roles = {"role": [{"id": 321, "title": "estudiante"}]}
            roles_page = PaginatedResult(
                request_client, page_size, roles, "role", "ignore me"
            )

            request_client.get_users.return_value = users_page
            request_client.get_roles.return_value = roles_page
            request_client.base_url = ""

            request_client.get.return_value = users_2

            # Also want to mock the UDM mapper function, since it is well-tested
            # elsewhere
            usersMap.map_to_udm = Mock()
            usersMap.map_to_udm.return_value = pd.DataFrame()

            # Arrange
            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            result = service.get_users()

            return result, usersMap.map_to_udm

        def it_should_return_the_user_in_a_data_frame(system):
            result, _ = system

            assert isinstance(result, pd.DataFrame)

        def it_should_use_first_users_page_when_mapping_to_udm(system):
            _, mock_map_to_udm = system

            args, _ = mock_map_to_udm.call_args
            assert args[0]["uid"][0] == 1234

        def it_should_use_second_users_page_when_mapping_to_udm(system):
            _, mock_map_to_udm = system

            args, _ = mock_map_to_udm.call_args
            assert args[0]["uid"][1] == 1235

        def it_should_use_the_given_roles_when_mapping_to_udm(system):
            _, mock_map_to_udm = system

            args, _ = mock_map_to_udm.call_args
            assert args[1]["id"][0] == 321


def describe_when_getting_sections():
    def describe_given_one_course_with_one_section():
        @pytest.fixture
        def system() -> Tuple[pd.DataFrame, Mock]:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 22

            courses = {
                "course": [{"id": 3333}],
                "total": 1,
                "links": {"self": "ignore"},
            }
            courses_page = PaginatedResult(
                request_client, page_size, courses, "course", "ignore me"
            )
            request_client.get_courses.return_value = courses_page

            # Also want to mock the UDM mapper function, since it is well-tested
            # elsewhere
            sectionsMap.map_to_udm = Mock()
            sectionsMap.map_to_udm.return_value = pd.DataFrame()

            sections = [{"id": 1234}]
            get_sections_mock = request_client.get_section_by_course_ids
            get_sections_mock.return_value = sections

            # Arrange
            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            result = service.get_sections()

            return result, sectionsMap.map_to_udm

        def it_should_return_a_data_frame(system):
            result, _ = system

            assert isinstance(result, pd.DataFrame)

        def it_should_map_to_the_udm(system):
            _, map_to_udm = system

            map_to_udm.assert_called_once()

    def describe_given_two_pages_of_courses():
        @pytest.fixture
        def system() -> Tuple[pd.DataFrame, Mock]:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 1

            courses = {
                "course": [{"id": 3333}],
                "total": 1,
                "links": {"self": "ignore", "next": "next"},
            }
            courses_page = PaginatedResult(
                request_client, page_size, courses, "course", "ignore me"
            )
            request_client.get_courses.return_value = courses_page

            courses_2 = {
                "course": [{"id": 3334}],
                "total": 1,
                "links": {"self": "ignore"},
            }
            request_client.base_url = ""
            request_client.get.return_value = courses_2

            # Also want to mock the UDM mapper function, since it is well-tested
            # elsewhere
            sectionsMap.map_to_udm = Mock()
            sectionsMap.map_to_udm.return_value = pd.DataFrame()

            sections = [{"id": 1234}]
            get_sections_mock = request_client.get_section_by_course_ids
            get_sections_mock.return_value = sections

            # Arrange
            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            result = service.get_sections()

            return result, get_sections_mock

        def it_should_use_first_course_when_getting_sections(system):
            _, get_sections_mock = system

            args = get_sections_mock.call_args
            assert 3333 in args[0][0]

        def it_should_use_second_course_when_getting_sections(system):
            _, get_sections_mock = system

            args = get_sections_mock.call_args
            assert 3334 in args[0][0]


def describe_when_getting_assignments():
    def describe_given_a_section_has_one_assignment():
        @pytest.fixture
        def system() -> Tuple[pd.DataFrame, Mock]:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 22
            section_id = 1234

            assignments = [
                {
                    "id": 3333,
                    "due": "1/2/3456 01:23:45 PM",
                    "description": "",
                    "max_points": 4,
                    "title": "1",
                    "type": "assignment",
                    "section_id": section_id,
                }
            ]
            get_assignments_mock = request_client.get_assignments
            get_assignments_mock.return_value = assignments

            # Arrange
            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            result = service.get_assignments(section_id)
            mapped_result = service.map_assignments_to_udm(result, section_id)

            return mapped_result, get_assignments_mock

        def it_should_query_for_the_given_section(system):
            _, get_assignments_mock = system

            args = get_assignments_mock.call_args
            assert 1234 == args[0][0]


def describe_when_mapping_assignments():
    def describe_given_a_section_has_one_assignment():
        @pytest.fixture
        def system() -> Tuple[pd.DataFrame, Mock]:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 22
            section_id = 1234

            assignments = [
                {
                    "id": 3333,
                    "due": "1/2/3456 01:23:45 PM",
                    "description": "",
                    "max_points": 4,
                    "title": "1",
                    "type": "assignment",
                    "section_id": section_id,
                }
            ]
            get_assignments_mock = request_client.get_assignments
            get_assignments_mock.return_value = assignments

            # Arrange
            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            mapped_result = service.map_assignments_to_udm(
                pd.DataFrame(assignments), section_id
            )

            return mapped_result, get_assignments_mock

        def it_should_return_the_assignments_list_as_data_frame(system):
            result, _ = system

            assert result["SourceSystemIdentifier"][0] == 3333


def describe_when_getting_submissions():
    def describe_given_one_assignment_and_one_submission():
        @pytest.fixture
        def result() -> list:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 22

            assignments = pd.DataFrame([{"section_id": 123, "grade_item_id": 345}])
            submissions = {
                "revision": [{"id": 1234}],
                "total": 1,
                "links": {"self": "ignore"},
            }
            submissions_page = PaginatedResult(
                request_client, page_size, submissions, "revision", "ignore me"
            )

            # Arrange
            request_client.get_submissions_by_section_id_and_grade_item_id.return_value = (
                submissions_page
            )

            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            result = service.get_submissions(assignments)

            return result

        def it_should_return_the_submission(result):
            assert result[0]["id"] == 1234

    def describe_given_two_assignment_and_one_submission_each():
        @pytest.fixture
        def result() -> list:
            logger = Mock(spec=Logger)
            request_client = Mock(spec=RequestClient)
            db_engine = Mock(spec=sqlalchemy.engine.base.Engine)
            page_size = 22

            assignments = pd.DataFrame(
                [
                    {"section_id": 123, "grade_item_id": 345},
                    {"section_id": 124, "grade_item_id": 346},
                ]
            )
            submissions_1 = {
                "revision": [{"id": 1234}],
                "total": 1,
                "links": {"self": "ignore"},
            }
            submissions_page_1 = PaginatedResult(
                request_client, page_size, submissions_1, "revision", "ignore me"
            )
            submissions_2 = {
                "revision": [{"id": 1235}],
                "total": 1,
                "links": {"self": "ignore"},
            }
            submissions_page_2 = PaginatedResult(
                request_client, page_size, submissions_2, "revision", "ignore me"
            )
            submissions_queue = [submissions_page_1, submissions_page_2]

            # Arrange
            request_client.get_submissions_by_section_id_and_grade_item_id.side_effect = (
                submissions_queue
            )

            service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)

            # Act
            result = service.get_submissions(assignments)

            return result

        def it_should_return_the_submission_for_assignment_1(result):
            assert result[0]["id"] == 1234

        def it_should_return_the_submission_for_assignment_2(result):
            assert result[1]["id"] == 1235
