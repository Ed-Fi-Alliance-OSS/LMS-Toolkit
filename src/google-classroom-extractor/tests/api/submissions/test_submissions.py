# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from typing import Dict
from unittest.mock import patch
import pandas as pd
from google_classroom_extractor.api.submissions import request_all_submissions_as_df
from tests.helper import merged_dict


def dataframe_row_count(dataframe) -> int:
    return dataframe.shape[0]


def db_row_count(test_db) -> int:
    return test_db.engine.execute(
        "SELECT COUNT(rowid) from StudentSubmissions"
    ).scalar()


def db_ending_user_id(test_db) -> int:
    return test_db.engine.execute(
        "SELECT userId from StudentSubmissions WHERE rowid = (SELECT MAX(rowid) from StudentSubmissions)"
    ).scalar()


def db_assigned_grade_by_id(test_db, submission_id) -> int:
    return test_db.engine.execute(
        f"SELECT assignedGrade from StudentSubmissions WHERE id = '{submission_id}'"
    ).scalar()


DUMMY_COURSE_IDS = ["1", "2"]


def describe_when_overlap_removal_is_needed():
    @patch(
        "google_classroom_extractor.api.submissions.request_latest_submissions_as_df"
    )
    def it_should_load_three_pulls_in_a_row_with_overlap_correctly(
        mock_latest_submissions_df, test_db_fixture
    ):
        # 1st pull: 17 rows
        mock_latest_submissions_df.return_value = pd.read_csv(
            "tests/api/submissions/submissions-1st.csv"
        )
        first_submissions_df = request_all_submissions_as_df(
            None, DUMMY_COURSE_IDS, test_db_fixture
        )
        assert dataframe_row_count(first_submissions_df) == 17
        assert db_row_count(test_db_fixture) == 17
        assert db_ending_user_id(test_db_fixture) == 60912479

        # 2nd pull: 58 rows, overlaps 7
        mock_latest_submissions_df.return_value = pd.read_csv(
            "tests/api/submissions/submissions-2nd-overlaps-1st.csv"
        )
        second_submissions_df = request_all_submissions_as_df(
            None, DUMMY_COURSE_IDS, test_db_fixture
        )
        assert dataframe_row_count(second_submissions_df) == 49
        assert (
            db_row_count(test_db_fixture) == 59
        )  # 58 new + 8 existing - 7 overlapping
        assert db_ending_user_id(test_db_fixture) == 57180732

        # 3rd pull: 98 rows, overlaps 43
        mock_latest_submissions_df.return_value = pd.read_csv(
            "tests/api/submissions/submissions-3rd-overlaps-1st-and-2nd.csv"
        )
        third_submissions_df = request_all_submissions_as_df(
            None, DUMMY_COURSE_IDS, test_db_fixture
        )
        assert dataframe_row_count(third_submissions_df) == 98
        assert (
            db_row_count(test_db_fixture) == 99
        )  # 98 new + 44 existing - 43 overlapping
        assert db_ending_user_id(test_db_fixture) == 42125460


def describe_when_pulls_of_same_submission_differ_in_assigned_grade():
    submission_id = "5583344"
    consistent_rows: Dict[str, str] = {
        "courseId": "93706414",
        "courseWorkId": "34575706",
        "id": submission_id,
        "userId": "61057789",
        "creationTime": "2020-03-27 11:48:27",
        "updateTime": "2020-09-11 17:15:15",
        "state": "CREATED",
        "draftGrade": "0",
        "assignedGrade": "0",
        "courseWorkType": "ASSIGNMENT",
    }
    initial_grade = "0"
    update_grade = "100"

    @patch(
        "google_classroom_extractor.api.submissions.request_latest_submissions_as_df"
    )
    def it_should_replace_old_grade_with_new(
        mock_latest_submissions_df, test_db_fixture
    ):
        mock_latest_submissions_df.return_value = pd.DataFrame.from_dict(
            [merged_dict(consistent_rows, {"assignedGrade": initial_grade})]
        )

        # initial pull
        first_submissions_df = request_all_submissions_as_df(
            None, DUMMY_COURSE_IDS, test_db_fixture
        )
        assert dataframe_row_count(first_submissions_df) == 1
        assert db_row_count(test_db_fixture) == 1
        assert db_assigned_grade_by_id(test_db_fixture, submission_id) == initial_grade

        # same submission, with grade updated
        mock_latest_submissions_df.return_value = pd.DataFrame.from_dict(
            [merged_dict(consistent_rows, {"assignedGrade": update_grade})]
        )

        # overwrite pull
        overwrite_submissions_df = request_all_submissions_as_df(
            None, DUMMY_COURSE_IDS, test_db_fixture
        )
        assert dataframe_row_count(overwrite_submissions_df) == 1
        assert db_row_count(test_db_fixture) == 1
        assert db_assigned_grade_by_id(test_db_fixture, submission_id) == update_grade
