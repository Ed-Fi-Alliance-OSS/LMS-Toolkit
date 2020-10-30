# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import logging
import os
from typing import Callable, Dict, Optional
import sys

from dotenv import load_dotenv
import pandas as pd

from schoology_extractor.helpers import export_data
from schoology_extractor.api.request_client import RequestClient
from schoology_extractor.helpers import arg_parser
from schoology_extractor.schoology_extract_facade import SchoologyExtractFacade
import schoology_extractor.lms_filesystem as lms

from schoology_extractor.helpers.sync import get_sync_db_engine

# Load configuration
load_dotenv()

arguments = arg_parser.parse_main_arguments(sys.argv[1:])
# Parameters are validated in the parse_main_arguments function
schoology_key = arguments.client_key
schoology_secret = arguments.client_secret
schoology_output_path = arguments.output_directory
schoology_grading_periods = arguments.grading_periods
log_level = arguments.log_level
page_size = arguments.page_size

# Configure logging
logFormatter = "%(asctime)s - %(levelname)s - %(message)s"

logging.basicConfig(
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
    format=logFormatter,
    level=log_level,
)

logger = logging.getLogger(__name__)

grading_periods = schoology_grading_periods.split(",")
request_client = RequestClient(schoology_key, schoology_secret)
db_engine = get_sync_db_engine()

service = SchoologyExtractFacade(logger, request_client, page_size, db_engine)


def _create_file_from_dataframe(action: Callable, file_name) -> bool:
    logger.info(f"Exporting {file_name}")
    try:
        data: pd.DataFrame = action()
        if data is not None:
            export_data.df_to_csv(data, file_name)
        return True
    except Exception as ex:
        logger.error(
            f"An exception of type %s occurred while generating {file_name}: %s",
            type(ex), ex,
        )
        return False


# TODO: this method should disappear when we finish converting all of the output
# to use the official CSV formats.
def _create_file_from_list(action: Callable, file_name: str) -> bool:
    logger.info(f"Exporting {file_name}")
    try:
        data = action()
        if data is not None:
            export_data.to_csv(data, os.path.join(schoology_output_path, file_name))
        return True
    except Exception as ex:
        logger.error(
            f"An exception occurred while generating {file_name} : %s",
            ex,
        )
        return False


def _get_users() -> pd.DataFrame:
    return service.get_users()


# This variable facilitates temporary storage of output results from one GET
# request that need to be used for creating another GET request.
result_bucket: Dict[str, pd.DataFrame] = {}


def _get_sections() -> pd.DataFrame:
    sections = service.get_sections()
    result_bucket["sections"] = sections
    return sections


def _get_assignments(section_id: int) -> Callable:
    # This nested function provides "closure" over `section_id`
    def __get_assignments() -> Optional[pd.DataFrame]:
        assignments = service.get_assignments(section_id)
        result_bucket["assignments"] = assignments

        return assignments

    return __get_assignments


def _get_submissions() -> list:
    assignments_df: pd.DataFrame = result_bucket["assignments"]
    return service.get_submissions(assignments_df)


def _get_section_associations(section_id: int) -> Callable:
    def __get_section_associations() -> pd.DataFrame:
        return service.get_section_associations(section_id)

    return __get_section_associations


def main():
    _create_file_from_dataframe(
        _get_users, lms.get_user_file_path(schoology_output_path)
    )
    succeeded = _create_file_from_dataframe(
        _get_sections, lms.get_section_file_path(schoology_output_path)
    )

    # Cannot proceed with section-related files if the sections extract did not
    # succeed.
    if not succeeded:
        sys.exit(-1)

    for section_id in result_bucket["sections"]["SourceSystemIdentifier"].values:
        file_path = lms.get_assignment_file_path(schoology_output_path, section_id)
        succeeded = _create_file_from_dataframe(_get_assignments(section_id), file_path)

        if succeeded:
            # TODO: use correct file path, and use DatFrame instead of list, in FIZZ-103
            _create_file_from_list(_get_submissions, "submissions.csv")

        file_path = lms.get_section_association_file_path(
            schoology_output_path, section_id
        )
        succeeded = _create_file_from_dataframe(_get_section_associations(section_id), file_path)

        # TODO: When merging with the work to create attendance events, should skip the attendance
        # if section associations failed.


if __name__ == "__main__":
    logger.info("Starting Ed-Fi LMS Schoology Extractor")
    main()
