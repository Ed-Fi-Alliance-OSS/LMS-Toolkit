# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

from .request_client_base import RequestClientBase
from .paginated_result import PaginatedResult


DEFAULT_URL = "https://api.schoology.com/v1/"


class RequestClient(RequestClientBase):
    """
    The RequestClient class wraps all the configuration complexity related to authentication
    and http requests for Schoology API

    Args:
        schoology_key (str): The consumer key given by Schoology
        schoology_secret (str): The consumer secret given by Schoology
        base_url (str, optional): The API base url. Default value: https://api.schoology.com/v1/

    Attributes:
        oauth (OAuth1Session): The two-legged authenticated OAuth1 session
    """

    def __init__(
        self,
        schoology_key: str,
        schoology_secret: str,
        base_url: str = DEFAULT_URL
    ):
        assert schoology_key is not None
        assert schoology_secret is not None
        assert base_url is not None

        super().__init__(schoology_key, schoology_secret, base_url)

    def get_assignments_by_section_ids(self, section_ids: list) -> dict:
        """
        Args:
            section_ids (list): A list of section ids

        Returns:
            dict: A parsed response from the server
        """
        assert section_ids is not None

        assignments = []
        for section_id in section_ids:
            url = f"sections/{section_id}/assignments"
            assignments_per_section = PaginatedResult(
                self,
                20,
                self.get(url),
                "assignment",
                self.base_url + url
            )
            while True:
                assignments = assignments + assignments_per_section.current_page_items
                if assignments_per_section.get_next_page() is None:
                    break

        return assignments

    def get_section_by_id(self, section_id: str) -> dict:
        """
        Args:
            section_id (list): The id of the section

        Returns:
            dict: A parsed response from the server
        """
        assert section_id is not None

        response = self.get(f"sections/{section_id}")
        return response

    def get_submissions_by_section_id(self, section_id: str, page_size: int = 20) -> PaginatedResult:
        """
        Args:
            section_id (list): The id of the section

        Returns:
            PaginatedResult: A parsed response from the server
        """
        assert section_id is not None

        url = f"sections/{section_id}/submissions"
        return PaginatedResult(
            self,
            page_size,
            self.get(url),
            "user",
            self.base_url + url
        )

    def get_users(self, page_size: int = 20) -> PaginatedResult:
        """
        Gets all the users from the Schoology API

        Returns:
            PaginatedResult: An object that wraps the request's response
        """
        url = f'users?start=0&limit={page_size}'

        return PaginatedResult(
            self,
            page_size,
            self.get(url),
            "user",
            self.base_url + url
        )
