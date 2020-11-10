# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from typing import Callable
import pandas as pd

from . import constants


def _flatten_into_dataframe(attendance: list,) -> pd.DataFrame:
    df = pd.DataFrame(columns=["enrollment_id", "EventDate", "AttendanceStatus"])

    for date_node in attendance:
        if "statuses" not in date_node or "status" not in date_node["statuses"]:
            continue

        for item in date_node["statuses"]["status"]:
            if "attendances" not in item or "attendance" not in item["attendances"]:
                continue

            reshape = pd.DataFrame(
                [
                    {
                        "enrollment_id": a["enrollment_id"],
                        "EventDate": date_node["date"],
                        "AttendanceStatus": a["status"],
                    }
                    for a in item["attendances"]["attendance"]
                ]
            )

            df = df.append(reshape)

    return df.convert_dtypes()


def _get_status(status_code: int) -> str:
    switcher = {1: "present", 2: "absent", 3: "late", 4: "excused"}
    return switcher.get(status_code, f"Unknown status: {status_code}")


def map_to_udm(attendance: list, section_associations: pd.DataFrame, additional_mapping : Callable = None) -> pd.DataFrame:
    """
    Maps a DataFrame containing Schoology attendance events into the Ed-Fi LMS
    Unified Data Model (UDM) format.

    Parameters
    ----------
    attendance: list
        List containing the API response from Schoology
    section_associations: DataFrame
        DataFrame containing UDM-mapped section associations

    Returns
    -------
    DataFrame
        A new DataFrame in the UDM attendance events format

    Notes
    -----
    DataFrame columns are:
        SourceSystemIdentifier: A unique number or alphanumeric code assigned to a user by the source system
        SourceSystem: The system code or name providing the user data
        Date: Attendance date, formatted as YYYY-mm-dd
        AttendanceStatus: one of (present, absent, late, excused)
        LMSUserSourceSystemIdentifier: source system identifier for the user
        LMSUserLMSSectionAssociationSourceSystemIdentifier: source system identifier for the section association
        EntityStatus: The status of the record
        CreateDate: datetime at which the record was first retrieved
        LastModifieDate: datetime when the record was modified, or when first retrieved
    """
    if len(attendance) == 0:
        return pd.DataFrame()

    df = _flatten_into_dataframe(attendance)

    df["SourceSystem"] = constants.SOURCE_SYSTEM
    df["EntityStatus"] = constants.ACTIVE
    df["SourceSystemIdentifier"] = df.apply(
        lambda row: f"{row['enrollment_id']}#{row['EventDate']}", axis=1
    )

    df["AttendanceStatus"] = df["AttendanceStatus"].apply(_get_status)

    sa = section_associations[
        [
            "SourceSystemIdentifier",
            "LMSUserSourceSystemIdentifier",
            "LMSSectionSourceSystemIdentifier",
        ]
    ].copy()
    # This data type conversion was required because Schoology is returning
    # enrollment Id as an integer in the Attendance endpoint, but as a string
    # with the Enrollment endpoint.
    sa = sa.astype({'SourceSystemIdentifier': 'int64'})

    df = df.merge(
        sa,
        how="inner",
        left_on="enrollment_id",
        right_on="SourceSystemIdentifier",
        suffixes=("", "_r"),
    )

    df = df[
        [
            "SourceSystem",
            "SourceSystemIdentifier",
            "EntityStatus",
            "AttendanceStatus",
            "EventDate",
            "LMSUserSourceSystemIdentifier",
            "LMSSectionSourceSystemIdentifier"
        ]
    ]

    if additional_mapping is not None:
        additional_mapping(df)

    return df
