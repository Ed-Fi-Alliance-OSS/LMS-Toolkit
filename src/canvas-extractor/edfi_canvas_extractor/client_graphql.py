# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import sqlalchemy

from pandas import DataFrame
from typing import List, Tuple

from canvasapi.course import Course
from canvasapi.section import Section
from edfi_canvas_extractor.graphql.extract import Extract
from edfi_canvas_extractor.graphql import (
    courses as coursesGQL,
    sections as sectionsGQL,
)

from edfi_canvas_extractor.mapping import (
    sections as sectionsMap,
)


def extract_courses(
    gql: Extract,
    sync_db: sqlalchemy.engine.base.Engine,
) -> Tuple[List[Course], DataFrame]:
    """
    Gets all Canvas courses for the given date range, in the Ed-Fi UDM format.

    Parameters
    ----------
    canvas: Canvas
        Canvas object.
    start_date: str
        Retrieve Courses starting on or after this date.
    end_date:
        Retrieve Courses ending on or before this date.
    sync_db: sqlalchemy.engine.base.Engine
        Sync database connection.

    Returns
    -------
    Tuple[List[Course], DataFrame]
        A tuple with the list of Canvas Course objects and the udm_courses dataframe.
    """
    courses: List[Course] = gql.courses
    courses_df: DataFrame = coursesGQL.courses_synced_as_df(courses, sync_db)

    return (courses, courses_df)


def extract_sections(
    gql: Extract,
    sync_db: sqlalchemy.engine.base.Engine
) -> Tuple[List[Section], DataFrame, List[str]]:
    """
    Gets all Canvas sections, in the Ed-Fi UDM format.

    Parameters
    ----------
    sync_db: sqlalchemy.engine.base.Engine
        Sync database connection.

    Returns
    -------
    Tuple[List[Section], DataFrame, List[str]]
        A tuple with the list of Canvas Section objects, the udm_sections dataframe,
        and a list of all section ids as strings.
    """
    sections: List[Section] = gql.sections
    sections_df: DataFrame = sectionsGQL.sections_synced_as_df(sections, sync_db)
    udm_sections_df: DataFrame = sectionsMap.map_to_udm_sections(sections_df)
    section_ids = udm_sections_df["SourceSystemIdentifier"].astype("string").tolist()
    return (sections, udm_sections_df, section_ids)
