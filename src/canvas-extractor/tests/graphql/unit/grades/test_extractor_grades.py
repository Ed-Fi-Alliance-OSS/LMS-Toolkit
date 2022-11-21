# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import logging
import pytest
import pytest

from pandas import DataFrame
from typing import cast, Dict, List

from edfi_canvas_extractor.client_graphql import (
    extract_grades,
)
from edfi_canvas_extractor.extract_graphql import (
    _get_sections,
    _get_enrollments,
    results_store
)


@pytest.mark.skip
def test_gql_grades_not_empty(
    mock_gql,
    test_db_fixture
):
    sections = _get_sections(mock_gql, test_db_fixture)

    assert sections is not None

    enrollments = _get_enrollments(mock_gql, test_db_fixture)

    assert enrollments is not None

    logging.info("Extracting Grades from Canvas API")
    (enrollments, udm_enrollments) = results_store["enrollments"]
    (sections, _, _) = results_store["sections"]
    udm_grades: Dict[str, DataFrame] = extract_grades(
        enrollments, cast(Dict[str, DataFrame], udm_enrollments), sections
    )

    assert udm_grades is not None


def test_gql_grades_duplicates(
    mock_gql,
    test_db_fixture
):
    sections = _get_sections(mock_gql, test_db_fixture)
    # assert sections is not None

    enrollments = _get_enrollments(mock_gql, test_db_fixture)
    # assert enrollments is not None

    logging.info("Extracting Grades from Canvas API")
    (enrollments, udm_enrollments) = results_store["enrollments"]
    (sections, _, all_section_ids) = results_store["sections"]

    for section in sections:
        current_grades: List[dict] = []
        section_id: str = str(section["id"])
        if section_id not in udm_enrollments:
            logging.info(
                "Skipping enrollments for section id %s - None found", section_id
            )
            continue
        udm_enrollments_list: List[dict] = udm_enrollments[section_id].to_dict(
            "records"
        )
        for enrollment in [
            enrollment
            for enrollment in enrollments
            if enrollment["type"] == "StudentEnrollment"
            and enrollment["course_section_id"] == section["id"]
        ]:
            grade: dict = enrollment["grades"]  # type: ignore
            current_udm_enrollment = [
                first_enrollment
                for first_enrollment in udm_enrollments_list
                if first_enrollment["SourceSystemIdentifier"] == str(enrollment["id"])
            ][0]
            enrollment_id = enrollment["id"]
            grade["SourceSystemIdentifier"] = f"g#{enrollment_id}"
            grade["LMSUserLMSSectionAssociationSourceSystemIdentifier"] = str(
                enrollment_id
            )
            grade["LMSSectionIdentifier"] = section_id
            grade["CreateDate"] = current_udm_enrollment["CreateDate"]
            grade["LastModifiedDate"] = current_udm_enrollment["LastModifiedDate"]

            for grades in current_grades:
                if grades.get('SourceSystemIdentifier') == f"g#{enrollment_id}":
                    continue

            current_grades.append(grade)

        # output[section_id] = gradesMap.map_to_udm_grades(DataFrame(current_grades))
        # logging.info(DataFrame(current_grades))
