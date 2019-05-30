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

"""This module defines class for working with tests and verdicts."""

import os
import shlex
from enum import Enum

import yaml
from loguru import logger

from pygon.generator import Generator
from pygon.config import TEST_FORMAT, BUILD_DIR

class Verdict(Enum):
    """Verdict for judgement.

    Values:
        OK: test passed / validation ok.
        TIME_LIMIT_EXCEEDED: self-explanatory.
        MEMORY_LIMIT_EXCEEDED: self-explanatory.
        REAL_TIME_LIMIT_EXCEEDED: self-explanatory.
        RUNTIME_ERROR: non-zero exit code for solution.
        VALIDATION_FAILED: non-zero exit code for validator.
        CHECK_FAILED: unexpected exit code for checker.
        WRONG_ANSWER: self-explanatory.
        PRESENTATION_ERROR: self-explanatory.
    """


    OK = "OK"
    TIME_LIMIT_EXCEEDED = "TL"
    MEMORY_LIMIT_EXCEEDED = "ML"
    REAL_TIME_LIMIT_EXCEEDED = "RL"
    RUNTIME_ERROR = "RE"
    VALIDATION_FAILED = "VF"
    CHECK_FAILED = "CF"
    WRONG_ANSWER = "WA"
    PRESENTATION_ERROR = "PE"


class FileName:
    """An object, representing file name of problem's input/output.
    May be either standard IO or a file with a name.
    """
    def __init__(self, stdio=False, filename=None):
        """Constructs a FileName.

        Args:
            stdio: if True, use standard IO
            filename: if stdio is False, use file with this name
        """

        self.stdio = stdio
        self.filename = filename

    def __str__(self):
        """Convert to string representation."""

        if self.stdio:
            return "stdio"

        return self.filename

    def statement_str(self, field, language="english"):
        """Convert to string to be used in a statement.

        Args:
            field: either "input" or "output"
            language: statement's language
        """

        if not self.stdio:
            return self.filename

        if field == "input":
            return "standard input"
        if field == "output":
            return "standard output"
        raise ValueError('`field` must be one of ("input", "output"), '
                         'got {}'.format(field))


class SolutionTest:
    """A test case for solution. May be either manually entered
    or generated using a generator.
    """

    def __init__(self, index, problem=None, sample=False, generate=None):
        """Construct a SolutionTest.

        Args:
            index: an integer index of the test.
            problem: a Problem which this test belongs to.
            sample: whether to use the test in the samples.
            generate: None if test is manually entered or a string,
                      containing generation command (e.g. "gen 1 2 3").
        """

        self.index = index
        self.problem = problem
        self.sample = sample
        self.generate = generate

    def get_descriptor_path(self):
        """Returns a path to the test's descriptor."""

        return os.path.join(self.problem.root, "tests",
                            TEST_FORMAT.format(self.index) + ".yaml")

    def load(self):
        """Load data about itself from the descriptor file."""

        with open(self.get_descriptor_path()) as desc:
            data = yaml.safe_load(desc.read())

        self.sample = data.get('sample', False)
        self.generate = data.get('generate')

    def get_input_path(self):
        """Returns a path to the test's input data."""

        if not self.generate:
            return os.path.join(self.problem.root, "tests",
                                TEST_FORMAT.format(self.index))

        return os.path.join(self.problem.root, BUILD_DIR, "tests",
                            TEST_FORMAT.format(self.index))

    def build(self):
        """If a test is not manual, generates it."""

        if not self.generate:
            return

        logger.info("<bold>{problem} :: </bold> generating test {index}".format(
            problem=self.problem.internal_name,
            index=self.index
        ))

        dirname = os.path.dirname(self.get_input_path())
        os.makedirs(dirname, exist_ok=True)

        args = shlex.split(self.generate)
        gen = Generator.from_identifier(args.pop(0), self.problem)
        gen.ensure_compile()
        gen.generate(self.get_input_path(), args)
