# SPDX-License-Identifier: Apache-2.0
# Licensed to the Ed-Fi Alliance under one or more agreements.
# The Ed-Fi Alliance licenses this file to you under the Apache License, Version 2.0.
# See the LICENSE and NOTICES files in the project root for more information.

import json
import logging
import os
import requests

from dotenv import load_dotenv
from typing import Dict, List

from .schema import query_builder
from .utils import validate_date


class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class Extract(Singleton):
    courses: List
    enrollments: List
    sections: List
    students: List

    def __init__(self):
        self.data = None
        self.courses = list()
        self.sections = list()
        self.students = list()
        self.enrollments = list()

    def get_from_canvas(self, query: str) -> Dict:
        """
        Fetch from GraphQL

        Parameters
        ----------
        query: string

        Returns
        -------
        Dict JSON Object
        """

        load_dotenv()
        CANVAS_URL = os.getenv('CANVAS_BASE_URL')
        CANVAS_TOKEN = os.getenv('CANVAS_ACCESS_TOKEN')
        GRAPHQL_URL = f"{CANVAS_URL}/api/graphql"
        GRAPHQL_AUTH = {'Authorization': f'Bearer {CANVAS_TOKEN}'}

        try:
            fetch = requests.post(
                GRAPHQL_URL,
                headers=GRAPHQL_AUTH,
                json={"query": query}
                )

            if fetch.status_code != 200:
                fetch.raise_for_status()

            body = json.loads(fetch.text)

            if "errors" in body:
                raise RuntimeError(str(body))

            return body

        except requests.exceptions.HTTPError as err:
            logging.error(err)

    def extract(self, body) -> None:
        """
        Extract the data

        Parameters
        ----------
        body: Dict JSON Object
        """
        courses = body["data"]["account"]["coursesConnection"]["nodes"][0]

        for course in courses["term"]["coursesConnection"]["nodes"]:
            if course["state"] not in ["available", "completed"]:
                continue

            start_term = courses["term"]["startAt"]
            end_term = courses["term"]["endAt"]

            if start_term is not None and end_term is not None:
                if not validate_date(self.start, self.end, start_term, end_term):
                    continue

            self.courses.append({
                "id": course["_id"],
                "name": course["name"],
                "state": course["state"],
                })

            sections = course["sectionsConnection"]["nodes"]
            for section in sections:
                self.sections.append({
                    "id": section["_id"],
                    "name": section["name"],
                    "sis_section_id": section["sisId"],
                    "created_at": section["createdAt"],
                    "updated_at": section["updatedAt"],
                    })

        if courses.get("pageInfo"):
            courses_page = courses["pageInfo"]
            if courses_page["hasNextPage"]:
                after = courses_page["endCursor"]
                query = query_builder(self.account, after)
                self.get_from_canvas(query)

    def set_account(self, account) -> None:
        self.account = account

    def set_dates(self, start_date, end_date) -> None:
        self.start = start_date
        self.end = end_date

    def run(self) -> None:
        if not self.data:
            query = query_builder(self.account)

            try:
                data = self.get_from_canvas(query)
                self.extract(data)
                self.data = True
            except Exception as e:
                logging.error(e)

    def get_courses(self) -> List:
        return self.courses

    def get_sections(self) -> List:
        return self.sections

    def get_enrollments(self) -> List:
        return self.enrollments

    def get_students(self) -> List:
        return self.students
