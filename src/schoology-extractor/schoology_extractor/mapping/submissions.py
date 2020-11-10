# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from datetime import datetime

import pandas as pd

from . import constants


def map_to_udm(submissions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps a DataFrame containing Schoology submissions into the Ed-Fi LMS Unified Data
    Model (UDM) format.

    Parameters
    ----------
    assignments_df: DataFrame
        Pandas DataFrame containing Schoology submissions for a section

    Returns
    -------
    DataFrame
        A LMSUsers-formatted DataFrame

    Notes
    -----
    DataFrame columns are:
        SourceSystemIdentifier: A unique number or alphanumeric code assigned to a submission by the source system
        SourceSystem: The system code or name providing the user data
        SubmissionStatus: The status of the submission
        SubmissionDateTime: Datetime of the submission
        EarnedPoints: Earned points for the submission
        Grade: Grade for the submission
        AssignmentSourceSystemIdentifier: Unique identifier for the assignment
        LMSUserSourceSystemIdentifier: Unique identifier of the LMSUser
        EntityStatus: Status of the entity
        CreateDate: Created date
        LastModifiedDate: Last modified date
    """

    if submissions_df.empty:
        return submissions_df

    df = submissions_df[
        [
            "id",
            "created",
            "late",
            "draft",
            "uid",
            "CreateDate",
            "LastModifiedDate"
        ]
    ].copy()

    df["SourceSystem"] = constants.SOURCE_SYSTEM
    df["EntityStatus"] = constants.ACTIVE
    df["SubmissionStatus"] = 'on-time'
    for index, row in df.iterrows():
        row["SubmissionStatus"] = 'late' if row["late"] == 1 else row["SubmissionStatus"]
        row["SubmissionStatus"] = 'draft' if row["draft"] == 1 else row["SubmissionStatus"]

    df.drop(columns=["late", "draft"], inplace=True)

    df["AssignmentSourceSystemIdentifier"] = df["id"].apply(lambda x: x.split('#')[1])
    df["EarnedPoints"] = None
    df["Grade"] = None

    df.rename(
        columns={
            "id": "SourceSystemIdentifier",
            "created": "SubmissionDateTime",
            "uid": "LMSUserSourceSystemIdentifier"
        },
        inplace=True,
    )

    df["SubmissionDateTime"] = df["SubmissionDateTime"].apply(lambda x: datetime.strftime(datetime.fromtimestamp(x), "%Y-%m-%d %H:%M:%S"))

    return df
