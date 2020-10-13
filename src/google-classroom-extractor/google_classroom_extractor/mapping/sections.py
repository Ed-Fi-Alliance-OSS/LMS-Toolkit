# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from pandas import DataFrame
from google_classroom_extractor.mapping.constants import (
    SOURCE_SYSTEM,
    ENTITY_STATUS_ACTIVE,
)


def courses_to_sections_df(courses_df: DataFrame) -> DataFrame:
    """
    Convert a Courses API DataFrame to an LMSSections UDM DataFrame

    Parameters
    ----------
    courses_df: DataFrame
        is a Courses API DataFrame

    Returns
    -------
    DataFrame
        a LMSSections DataFrame based on the given Courses API DataFrame

    DataFrame columns are:
        EntityStatus: The status of the record
        LMSSectionStatus: The section status from the source system
        SISSectionIdentifier: The section identifier defined in the Student Information System
        SectionDescription: The section description
        SourceSystem: The system code or name providing the section data
        SourceSystemIdentifier: A unique number or alphanumeric code assigned to a user by the source system
        Term: The enrollment term for the section
        Title: The section title or name
        CreateDate: Date this record was created
        LastModifiedDate: Date this record was last updated
    """
    assert isinstance(courses_df, DataFrame)
    assert "id" in courses_df.columns
    assert "courseState" in courses_df.columns
    assert "descriptionHeading" in courses_df.columns
    assert "name" in courses_df.columns

    result: DataFrame = courses_df[
        [
            "id",
            "courseState",
            "descriptionHeading",
            "name",
            "creationTime",
            "updateTime",
        ]
    ]
    result = result.rename(
        columns={
            "id": "SourceSystemIdentifier",
            "courseState": "LMSSectionStatus",
            "descriptionHeading": "SectionDescription",
            "name": "Title",
            "creationTime": "CreateDate",
            "updateTime": "LastModifiedDate",
        }
    )

    result["SourceSystem"] = SOURCE_SYSTEM
    result["EntityStatus"] = ENTITY_STATUS_ACTIVE
    result["SISSectionIdentifier"] = ""  # No SIS id available from API
    result["Term"] = ""  # No term available from API

    return result
