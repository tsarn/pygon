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

"""This module defines class for working with solutions."""

import os

import yaml
from loguru import logger

from pygon.language import Language
from pygon.source import Source
from pygon.invoke import Invoke
from pygon.testcase import Verdict


class SolutionTag:
    """A tag, determining what verdicts is the solution allowed to get.
    Three kinds of tags are available: main correct solution,
    correct solution and incorrect solution.

    Main correct solution is exactly one in a correctly formed problem.
    It determines answers to the tests, which are then fed to the checker.

    Correct solutions are expected to get OK on all tests.

    Incorrect solutions are paremetrized by list of verdicts they are allowed
    to get on each test (not counting OK). If OK is included in the list,
    the solution is allowed to be correct, otherwise it must get at least one
    non-OK verdict on any test to be valid.
    """

    def __init__(self, tag="correct", verdicts=None):
        """Constructs a SolutionTag.

        Args:
            tag: "main", "correct" or "incorrect". See class docstring for info.
            verdicts: if tag == "incorrect", then a list of Verdicts.
        """

        if tag == "main":
            self.tag = "main"
        elif tag == "correct":
            self.tag = "correct"
        elif tag == "incorrect":
            self.tag = "incorrect"
            if verdicts is None:
                raise ValueError("Tag 'incorrect' requires a list of verdicts")
            self.verdicts = verdicts
        else:
            raise ValueError("Invalid value for 'tag': {!r}".format(tag))

    def check_one(self, verdict):
        """Checks if a result on one test is valid.
        Note, that results on all individual tests can be valid,
        but solution may be invalid anyway. See check_all.

        Args:
            verdict: a Verdict, which the solution got on a test

        Returns:
            True if solution is valid on the test, and False otherwise.
        """

        if verdict == Verdict.OK:
            return True

        if self.tag != "incorrect":
            return False

        return verdict in self.verdicts

    def check_all(self, verdicts):
        """Checks if a result on all tests is valid.

        Args:
            verdicts: a list of Verdicts, which the solution got on the tests.

        Returns:
            True if solution is valid on the test set as a whole,
            and False otherwise.
        """

        if not all([self.check_one(i) for i in verdicts]):
            return False

        if self.tag != "incorrect":
            return True

        return any([i != Verdict.OK for i in verdicts])


class Solution(Source):
    """A solution for a problem"""

    directory_name = "solutions"

    def __init__(self, tag=None, **kwargs):
        """Constructs a Solution.

        Args:
            name: name of the solution with extension (e.g. "solve_ok.cpp").
            problem: Problem which this solution belongs to.
            lang: Language of the solution.
            tag: a SolutionTag for the solution
        """

        self.tag = tag or SolutionTag()
        super(Solution, self).__init__(**kwargs)

    def load(self):
        """See base class."""

        with open(self.get_descriptor_path()) as desc:
            data = yaml.safe_load(desc)

        self.lang = Language.from_name(data.get('language'))
        self.tag = SolutionTag(data.get("tag", "main"),
                               [Verdict(i) for i in data.get("verdicts", [])])

    def invoke(self, test):
        """Invoke solution on a test (without running a checker).

        Args:
            test: a SolutionTest.

        Returns:
            InvokeResult
        """

        self.ensure_compile()

        invoke = Invoke(self.get_execute_command(),
                        time_limit=self.problem.time_limit,
                        memory_limit=self.problem.memory_limit)

        inp = test.get_input_path()
        out = test.get_output_path(self.identifier)

        os.makedirs(os.path.dirname(out), exist_ok=True)

        with invoke.with_temp_cwd():
            with invoke.with_stdin(self.problem.input_file, inp):
                with invoke.with_stdout(self.problem.output_file, out):
                    return invoke.run()

    def judge(self, test):
        """Runs and judges solution on a test.

        Args:
            test: a SolutionTest.

        Returns:
            InvokeResult
        """

        main_solution = self.problem.get_main_solution()

        logger.info("Judging {solution} on test {test}",
                    solution=self.identifier,
                    test=test.index)

        res = self.invoke(test)

        if res.verdict != Verdict.OK:
            return res

        inp = test.get_input_path()
        out = test.get_output_path(self.identifier)
        ans = test.get_output_path(main_solution.identifier)

        chk = self.problem.active_checker.judge(inp, out, ans)
        res.verdict = chk.verdict
        res.comment = chk.comment

        return res
