# Copyright (c) 2019 Tsarev Nikita
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

"""This module defines class for working with problems."""

import os
import subprocess

import yaml
from loguru import logger

from pygon.testcase import FileName, SolutionTest, Verdict
from pygon.config import TEST_FORMAT


class ProblemConfigurationError(Exception):
    pass


class Problem:
    """A problem.

    Attributes:
        root: path to problem root
        internal_name: problem internal name (e.g. "aplusb")
        input_file: FileName of input file
        output_file: FileName of output file
        time_limit: time limit in seconds
        memory_limit: memory limit in MiB
        active_checker: active Checker for the problem (or None)
        active_validators: list of active Validators for the problem
    """

    def __init__(self, root):
        """Constructs a Problem

        Args:
            root: path to problem root
        """
        self.root = root
        self.internal_name = os.path.basename(root)
        self.input_file = FileName(stdio=True)
        self.output_file = FileName(stdio=True)
        self.time_limit = 1.0
        self.memory_limit = 256.0
        self.active_checker = None
        self.active_validators = []

    def load(self):
        """Load itself from descriptor."""

        from pygon.checker import Checker
        from pygon.validator import Validator

        with open(self.get_descriptor_path()) as desc:
            data = yaml.safe_load(desc.read())

        self.internal_name = data["internal_name"]
        self.input_file = FileName(data.get("input_file", "standard_io"))
        self.output_file = FileName(data.get("output_file", "standard_io"))
        self.time_limit = data.get("time_limit", 1.0)
        self.memory_limit = data.get("memory_limit", 256.0)

        chk = data.get("active_checker")

        if chk:
            self.active_checker = Checker.from_identifier(chk, self)
        else:
            self.active_checker = None

        self.active_validators = []

        for i in data.get("active_validators"):
            self.active_validators.append(Validator.from_identifier(i, self))

    def get_source_filename(self, directory, name):
        """Get a source filename from identifier, or determine that
        the source doesn't exist.

        Args:
            directory: directory where to look for the source (e.g. "checkers")
            name: identifier of the source (e.g. "check")

        Returns:
            None if source was not found, filename of the source otherwise
            (e.g. "check.cpp")
        """

        lst = os.listdir(os.path.join(self.root, directory))
        for i in lst:
            if os.path.splitext(i)[0] == name and not i.endswith(".yaml"):
                return i

        return None

    def get_descriptor_path(self):
        """Returns a path to problem's descriptor file"""

        return os.path.join(self.root, "problem.yaml")

    def get_sources(self, directory):
        """Returns a list of all sources' filenames.

        Args:
            directory: directory where to look for the source (e.g. "solutions")

        Returns:
            list: source filenames (e.g. ["solve_ok.cpp", "solve_wa.cpp"])
        """

        res = []

        lst = set(os.listdir(os.path.join(self.root, directory)))
        for i in lst:
            if i.endswith(".yaml"):
                continue

            base = os.path.splitext(i)[0]
            if '{}.yaml'.format(base) not in lst:
                continue

            res.append(i)

        res.sort()

        return res

    def discover_sources(self, cls):
        """Discover sources that lack descriptors and create them.

        Args:
            cls: a Source subclass
        """

        dirname = os.path.join(self.root, cls.directory_name)
        lst = set(os.listdir(dirname))
        for src in lst:
            if src.endswith(".yaml"):
                continue

            base = os.path.splitext(src)[0]
            if '{}.yaml'.format(base) in lst:
                continue

            logger.info("{} {} discovered", cls.__name__, src)

            obj = cls(problem=self, name=src)
            obj.save()

    def get_statements(self):
        """Returns list of all Statements."""

        from pygon.statement import Statement

        res = []

        for lang in os.listdir(os.path.join(self.root, "statements")):
            with open(os.path.join(self.root, "statements", lang, "name.txt")) as f:
                name = f.read().strip()
            res.append(Statement(problem=self, name=name, language=lang))

        return res

    def get_main_solution(self):
        """Returns the problem's main Solution.

        Raises:
            ProblemConfigurationError - no/more than one main solution is found
        """

        from pygon.solution import Solution

        if hasattr(self, "_main_solution"):
            return self._main_solution

        res = []

        for i in self.get_sources(Solution.directory_name):
            sol = Solution(name=i, problem=self)
            sol.load()
            if sol.tag.tag == "main":
                res.append(sol)

        if not res:
            raise ProblemConfigurationError("No main solution found")

        if len(res) > 1:
            raise ProblemConfigurationError("More than one main solution found")

        self._main_solution = res[0]
        return self._main_solution

    def get_solution_tests(self):
        """Collects all of the SolutionTests from file system and
        returns it as a list, sorted by indices
        """

        res = []

        for i in os.listdir(os.path.join(self.root, "tests")):
            if not i.endswith(".yaml"):
                continue
            base = i[:-5]
            try:
                index = int(base)
            except ValueError:
                continue

            if TEST_FORMAT.format(index) != base or index < 1:
                continue

            test = SolutionTest(index, problem=self)
            test.load()
            res.append(test)

        res.sort(key=lambda test: test.index)

        return res

    def edit_solution_tests(self):
        """Returns a editable multiline value for managing tests."""

        res = """\
# Managing tests of problem {problem}
#
# Each non-empty line of this file, except comments, which begin with '#'
# signifies a test. Test may be either manually entered or generated.
#
# Manually entered tests are lines beginning with 'M', then flags,
# then a path to the input file, relative to the problem root.
#
# Generated tests are lines beginning with 'G', then flags,
# then generator command.
#
# List of flags:
#   S - this test is a sample
#
# For example, following line means a manually entered test that is
# included in the statements and is located at PROBLEMROOT/tests/01:
#
# MS tests/01
#
# Edit your tests, then save this file and exit the editor

""".format(problem=self.internal_name)

        lines = []

        for test in self.get_solution_tests():
            if test.generate:
                line = "G"
            else:
                line = "M"

            if test.sample:
                line += "S"

            line += " "

            if test.generate:
                line += test.generate
            else:
                line += os.path.join("tests", TEST_FORMAT.format(test.index))

            lines.append(line)

        return res + "\n".join(lines)

    def update_solution_tests(self, text):
        """Updates SolutionTests from editable text
        (see edit_solution_tests).
        """

        tests = []
        dirname = os.path.join(self.root, "tests")

        for line in text.split("\n"):
            l = line.strip()
            if l.startswith("#") or not l:
                continue
            if " " not in l:
                raise ValueError("Malformed line: '{}'".format(l))
            flags = l[:l.find(" ")]
            arg = l[l.find(" ")+1:]

            test = dict(sample="S" in flags)

            if flags[0] == "M":
                with open(os.path.join(self.root, arg), 'rb') as f:
                    test['data'] = f.read()
            elif flags[0] == "G":
                test['generate'] = arg
            else:
                raise ValueError("Malformed line: '{}'".format(l))

            tests.append(test)

        to_remove = set(os.listdir(dirname))

        for i, test in enumerate(tests):
            index = TEST_FORMAT.format(i + 1)
            if 'data' in test:
                to_remove.discard(index)
            to_remove.discard(index + ".yaml")

            obj = SolutionTest(index=i + 1, problem=self,
                               sample=test['sample'],
                               generate=test.get('generate'))

            obj.save()
            if 'data' in test:
                with open(os.path.join(dirname, index), 'wb') as f:
                    f.write(test['data'])

        for i in to_remove:
            os.remove(os.path.join(dirname, i))

    def add_statement(self, lang, name):
        """Add new statement.

        Args:
            lang: statement language.
            name: name of the problem in that language.
        """

        root = os.path.join(self.root, "statements", lang)
        if os.path.exists(root):
            logger.error("{} already exists", root)
            return False

        os.makedirs(root, exist_ok=True)

        with open(os.path.join(root, "name.txt"), "w") as f:
            print(name, file=f)

        with open(os.path.join(root, "problem.tex"), "w") as f:
            print("""\
% Write problem legend here

\\InputFile

% Write input format here

\\OutputFile

% Write output format here

% Sample tests replace the following line, if you remove it,
% they will not be displayed.

\\SAMPLES

\\Explanations

% Write your explanations here. You can also remove this (or any other)
% section entirely. It's up to you.
""", file=f)

        return True

    def build(self):
        """Build the problem verifying that:

        - There is an active checker and it compiles
        - There is a main solution and it compiles
        - All active validators compile
        - All tests are generated and valid
        - Main solution gets OK

        Should be ran prior to verification.
        """

        if not self.active_checker:
            raise ProblemConfigurationError("Active checker is not set")

        try:
            self.active_checker.ensure_compile()
        except subprocess.CalledProcessError:
            raise ProblemConfigurationError("Active checker compilation failed")

        main_solution = self.get_main_solution()

        try:
            main_solution.ensure_compile()
        except subprocess.CalledProcessError:
            raise ProblemConfigurationError("Main solution compilation failed")

        tests = self.get_solution_tests()

        for test in tests:
            try:
                test.build()
            except subprocess.CalledProcessError:
                raise ProblemConfigurationError("Generator compilation failed")

            for validator in self.active_validators:
                verdict = validator.validate(test.get_input_path())
                if verdict.verdict != Verdict.OK:
                    raise ProblemConfigurationError(
                        "Validator {} rejects test {}: {}".format(
                            validator.identifier,
                            test.index,
                            verdict.comment
                        ))

        for test in tests:
            verdict = main_solution.judge(test)

            if not main_solution.tag.check_one(verdict.verdict):
                raise ProblemConfigurationError(
                    "Main solution {} gets {} on test {}: {}".format(
                        main_solution.identifier,
                        verdict.verdict,
                        test.index,
                        verdict.comment
                    ))

        for stmt in self.get_statements():
            try:
                stmt.build()
            except subprocess.CalledProcessError:
                raise ProblemConfigurationError(
                    "Failed to build {} statement. See '{}' for details".format(
                        stmt.language, stmt.get_log_path()
                    ))

        logger.info("Problem {} built successfully".format(self.internal_name))
