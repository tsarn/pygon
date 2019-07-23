# Copyright (c) 2019 Nikita Tsarev
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""This module defines class for working with contests."""

import os

import yaml
from pkg_resources import resource_filename

from pygon.config import BUILD_DIR
from pygon.problem import Problem
from pygon.statement import Statement


class Contest:
    """A contest.

    Attributes:
        root: path to contest root.
        problems (list): list of pairs (prefix, Problem).
        name (dict): mapping from language to contest name.
        location (dict): mapping from language to contest location.
        date (dict): mapping from language to contest date.
    """

    def __init__(self, root):
        self.root = root
        self.problems = []
        self.name = {}
        self.location = {}
        self.date = {}

    def load(self):
        """Load itself from descriptor."""

        with open(self.get_descriptor_path()) as desc:
            data = yaml.safe_load(desc)

        self.problems = []
        self.name = data.get("name", {})
        self.location = data.get("location", {})
        self.date = data.get("date", {})

        for p in data["problems"]:
            root = os.path.join(self.root, "problems", p["id"])
            prob = Problem(root)
            prob.load()
            self.problems.append((p["prefix"], prob))

    def get_languages(self):
        """Returns contest's languages."""

        return list(set(list(self.name) + list(self.location) + list(self.date)))

    def build(self, statements=True):
        """Build the contest."""

        for prefix, problem in self.problems:
            problem.build(statements=False)

        if statements:
            for lang in self.get_languages():
                stmt = ContestStatement(contest=self, language=lang,
                                        name=self.name.get(lang, ""),
                                        location=self.location.get(lang, ""),
                                        date=self.date.get(lang, ""))
                stmt.build()

    def verify(self):
        """Run verification on all problems."""

        for prefix, problem in self.problems:
            problem.verify()

    def get_descriptor_path(self):
        """Return a path to contest's descriptor file."""

        return os.path.join(self.root, "contest.yaml")


class ContestStatement(Statement):
    """Statements for a contest.

    Attributes:
        contest: the Contest.
        language: statement's language in lowercase English (e.g. "russian").
        name: contest's name (e.g. "Olympiad in Informatics").
        location: contest's location (e.g. "Moscow").
        date: contest's date (e.g. "June 1st, 2019").
    """

    def __init__(self, contest, language, name, location, date):
        self.contest = contest
        self.language = language
        self.name = name
        self.location = location
        self.date = date

    def get_resource_dirs(self):
        """Returns list of resource directories."""

        return [
            os.path.join(self.contest.root, "resources"),
            resource_filename("pygon", os.path.join("data", "resources"))
        ]

    def get_build_root(self):
        """Returns path to build root."""

        return os.path.join(self.contest.root, BUILD_DIR,
                            "statements", self.language)

    def get_log_path(self):
        """Returns path to TeX log."""

        return os.path.join(self.get_build_root(), "statements.log")

    def build(self):
        """Builds the statement."""

        root = self.get_build_root()
        os.makedirs(root, exist_ok=True)

        with open(os.path.join(root, "olymp.sty"), "w") as f:
            f.write(self.read_resource("olymp.sty"))

        statements = []

        for prefix, problem in self.contest.problems:
            with open(os.path.join(problem.root, "statements", self.language,
                                   "name.txt")) as f:
                name = f.read().strip()

            stmt = Statement(problem=problem, name=name, language=self.language)
            stmt.build()

            path = os.path.join(root, "{}.tex".format(problem.internal_name))

            with open(path, "w") as f:
                f.write(stmt.get_tex_statement())

            statements.append(path)

        self.build_statements(statements,
                              name=self.name,
                              location=self.location,
                              date=self.date)
