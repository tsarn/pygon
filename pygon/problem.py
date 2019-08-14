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

"""This module defines class for working with problems."""

import os
import subprocess
import glob
from shutil import rmtree

import yaml
from loguru import logger

from pygon.testcase import FileName, SolutionTest, CheckerTest, Verdict
from pygon.testcase import expand_generator_command, ValidatorTest
from pygon.config import TEST_FORMAT, BUILD_DIR
from pygon.ejudge import export_problem as ejudge_export


class ProblemConfigurationError(Exception):
    pass


class Problem:
    """A problem.

    Attributes:
        root: path to problem root
        internal_name (str): problem internal name (e.g. "aplusb")
        input_file (FileName): input file
        output_file (FileName): output file
        interactive (bool): is this problem interactive?
        time_limit (float): time limit in seconds
        memory_limit (float): memory limit in MiB
        active_checker (Checker): active checker for the problem (or None)
        active_interactor (Interactor): active interactor for the problem (or None)
        active_validators (list): list of active Validators for the problem
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
        self.interactive = False
        self.time_limit = 1.0
        self.memory_limit = 256.0
        self.active_checker = None
        self.active_interactor = None
        self.active_validators = []

    def load(self):
        """Load itself from descriptor."""

        from pygon.checker import Checker
        from pygon.validator import Validator
        from pygon.interactor import Interactor

        with open(self.get_descriptor_path()) as desc:
            data = yaml.safe_load(desc.read())

        self.internal_name = data["internal_name"]
        self.input_file = FileName(data.get("input_file", "standard_io"))
        self.output_file = FileName(data.get("output_file", "standard_io"))
        self.interactive = data.get("interactive", False)
        self.time_limit = data.get("time_limit", 1.0)
        self.memory_limit = data.get("memory_limit", 256.0)

        chk = data.get("active_checker")

        if chk:
            self.active_checker = Checker.from_identifier(chk, self)
        else:
            self.active_checker = None

        itr = data.get("active_interactor")

        if itr:
            self.active_interactor = Interactor.from_identifier(itr, self)
        else:
            self.active_interactor = None

        self.active_validators = []

        for i in data.get("active_validators", []):
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

        try:
            lst = set(os.listdir(os.path.join(self.root, directory)))
        except FileNotFoundError:
            return []

        res = []

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

        try:
            lst = set(os.listdir(dirname))
        except FileNotFoundError:
            return

        for src in lst:
            if src.endswith(".yaml"):
                continue

            base = os.path.splitext(src)[0]
            if '{}.yaml'.format(base) in lst:
                continue

            logger.success("{} {} discovered", cls.__name__, src)

            obj = cls(problem=self, name=src)
            obj.save()

    def get_statements(self):
        """Returns list of all Statements."""

        from pygon.statement import Statement

        res = []

        for lang in os.listdir(os.path.join(self.root, "statements")):
            if lang == "tests":
                continue

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

    def get_tests(self, cls):
        """Collects all of the tests of type cls:
        solution/checker/validator tests.
        """

        res = []
        try:
            lst = set(os.listdir(os.path.join(self.root, cls.directory)))
        except OSError:
            return res

        for i in lst:
            if not i.endswith(".yaml"):
                base = i
            else:
                base = i[:-5]
            try:
                index = int(base)
            except ValueError:
                continue

            if TEST_FORMAT.format(index) != base or index < 1:
                continue

            test = cls(index, problem=self)

            if not i.endswith(".yaml"):
                if "{}.yaml".format(i) in lst:
                    continue

                # There's no descriptor, so this test is has default settings,
                # so we don't run load.
            else:
                test.load()
            res.append(test)

        res.sort(key=lambda test: test.index)

        return res

    def get_solution_tests(self):
        """Collects all of the `SolutionTest`s from the file system and
        returns it as a list, sorted by index.
        """

        return self.get_tests(SolutionTest)

    def get_checker_tests(self):
        """Collects all of the `CheckerTest`s from the file system and
        returns it as a list, sorted by index.
        """

        return self.get_tests(CheckerTest)

    def get_validator_tests(self):
        """Collects all of the `ValidatorTest`s from the file system and
        returns it as a list, sorted by index.
        """

        return self.get_tests(ValidatorTest)

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
# Globs are supported (you can use /something/*), tests are ordered
# lexicographically.
#
# Generated tests are lines beginning with 'G', then flags,
# then generator command. By default, ranges are expanded into
# several tests. For example, generator command "gen [1..3]" expands
# into three tests, with generator commands "gen 1", "gen 2" and "gen 3"
# respectively. You can also use several ranges in one command and
# specify step, for example "gen 10 [1,3..9] 20 [5,4..1]".
#
# List of flags:
#   S - this test is a sample
#   R - do not expand ranges or globs in this test
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
                exp = expand_generator_command(test.generate)
                if len(exp) != 1 or exp[0] != test.generate:
                    line += "R"
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
                if "R" not in flags:
                    for i in sorted(glob.glob(os.path.join(self.root, arg))):
                        test = test.copy()
                        with open(i, 'rb') as f:
                            test['data'] = f.read()
                        tests.append(test)
                else:
                    with open(os.path.join(self.root, arg), 'rb') as f:
                        test['data'] = f.read()
                    tests.append(test)
            elif flags[0] == "G":
                if "R" not in flags:
                    for i in expand_generator_command(arg):
                        test = test.copy()
                        test["generate"] = i
                        tests.append(test)
                else:
                    test["generate"] = arg
                    tests.append(test)
            else:
                raise ValueError("Malformed line: '{}'".format(l))

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

    def build(self, statements=True):
        """Build the problem verifying that:

        - There is an active checker and it compiles
        - (If interactive) There is an active interactor and it compiles
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

        if self.interactive:
            if not self.input_file.stdio or not self.output_file.stdio:
                raise ProblemConfigurationError("Interactive problems must use stdio")

            if not self.active_interactor:
                raise ProblemConfigurationError("Active interactor is not set")

            try:
                self.active_interactor.ensure_compile()
            except subprocess.CalledProcessError:
                raise ProblemConfigurationError("Active interactor compilation failed")

        main_solution = self.get_main_solution()

        try:
            main_solution.ensure_compile()
        except subprocess.CalledProcessError:
            raise ProblemConfigurationError("Main solution compilation failed")

        for validator in self.active_validators:
            try:
                validator.ensure_compile()
            except subprocess.CalledProcessError:
                raise ProblemConfigurationError(
                    "Validator {} compilation failed".format(validator)
                )

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

        if statements:
            for stmt in self.get_statements():
                try:
                    stmt.build()
                except subprocess.CalledProcessError:
                    raise ProblemConfigurationError(
                        "Failed to build {} statement. See '{}' for details".format(
                            stmt.language, stmt.get_log_path()
                        ))

        logger.success("Problem built successfully")

    def verify(self):
        """Build and lint problem for configuration errors.
        Raises errors when:

        - Problem fails to build correctly (see `Problem.build`).
        - Solutions have incorrect tags.
        - Active checker doesn't pass all checker tests.
        - Active validators don't pass all validator tests.

        Reports warnings when:

        - Checker tests are missing and custom checker is used.
        - Validator tests are missing and custom validator is used.
        - Custom validator is not used.
        - No tests.
        - Sample tests are not first.

        """

        from pygon.solution import Solution

        self.build(statements=False)

        solutions = Solution.all(self)
        tests = self.get_solution_tests()

        for solution in solutions:
            verdicts = []
            for test in tests:
                verdicts.append(solution.judge(test).verdict)
            if solution.tag.check_all(verdicts):
                logger.success("Solution {} has correct tag"
                               .format(solution.identifier))
            else:
                raise ProblemConfigurationError("Solution {} has incorrect tag"
                                                .format(solution.identifier))

        checker_tests = self.get_checker_tests()

        for test in checker_tests:
            test.validate(self.active_checker)

        if checker_tests:
            logger.success("Checker passed all tests")
        elif not self.active_checker.standard:
            logger.warning("No checker tests found, please consider adding them")

        validator_tests = self.get_validator_tests()

        for test in self.get_validator_tests():
            test.validate(self.active_validators)

        if any(not i.standard for i in self.active_validators):
            if validator_tests:
                logger.success("Validators passed all tests")
            else:
                logger.warning("No validator tests found, please consider adding them")
        else:
            logger.warning("No custom validators found, please consider adding them")

        if tests:
            prefix = True
            for test in tests:
                if test.sample:
                    if not prefix:
                        logger.warning(
                            "Test case {} is a sample, but is not among "
                            "the first tests for the problem".format(test.index))
                else:
                    prefix = False
        else:
            logger.warning("No test cases found")

    def ejudge_export(self, language=None):
        """Export problem in ejudge format to BUILD_ROOT/ejudge"""

        path = os.path.join(self.root, BUILD_DIR, "ejudge")
        rmtree(path, ignore_errors=True)
        ejudge_export(self, path, language=language)
