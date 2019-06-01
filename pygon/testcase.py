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
import itertools
from enum import Enum

import yaml
from loguru import logger

from pygon.generator import Generator
from pygon.config import TEST_FORMAT, BUILD_DIR

class Verdict(Enum):
    """Verdict for a judgement."""

    OK = "OK"
    TIME_LIMIT_EXCEEDED = "TL"
    MEMORY_LIMIT_EXCEEDED = "ML"
    RUNTIME_ERROR = "RE"
    VALIDATION_FAILED = "VF"
    CHECK_FAILED = "CF"
    WRONG_ANSWER = "WA"
    PRESENTATION_ERROR = "PE"


class FileName:
    """An object, representing file name of problem's input/output.
    May be either standard IO or a file with a name.
    """
    def __init__(self, mixed=None, stdio=False, filename=None):
        """Constructs a FileName.

        Args:
            mixed: if set, then if equal to "standard_io", then stdio == True,
                   else filename == mixed
            stdio: if True, use standard IO
            filename: if stdio is False, use file with this name
        """

        if mixed:
            if mixed == "standard_io":
                stdio = True
                filename = None
            else:
                stdio = False
                filename = mixed

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

        self.sample = data.get("sample", False)
        self.generate = data.get("generate")

    def save(self):
        """Save data about itself into the descriptor file."""

        with open(self.get_descriptor_path(), "w") as desc:
            data = dict(sample=self.sample)
            if self.generate:
                data["generate"] = self.generate
            yaml.dump(data, desc, default_flow_style=False)

    def get_input_path(self):
        """Returns a path to the test's input data."""

        if not self.generate:
            return os.path.join(self.problem.root, "tests",
                                TEST_FORMAT.format(self.index))

        return os.path.join(self.problem.root, BUILD_DIR, "tests",
                            TEST_FORMAT.format(self.index))

    def get_output_path(self, identifier):
        """Returns a path to the output data.

        Args:
            identifier (str): identifier of `Solution` whose
                              output data to point to.
        """

        return os.path.join(self.problem.root, BUILD_DIR, "outputs",
                            identifier, TEST_FORMAT.format(self.index))

    def get_verdict_path(self, identifier):
        """Returns a path to the verdict.

        Args:
            identifier (str): identifier of `Solution` whose
                              verdict to point to.
        """

        return os.path.join(self.problem.root, BUILD_DIR, "outputs",
                            identifier, TEST_FORMAT.format(self.index) + ".yaml")

    def build(self):
        """If a test is not manual and needs generating, generate it."""

        if not self.generate:
            return

        args = shlex.split(self.generate)
        gen = Generator.from_identifier(args.pop(0), self.problem)
        gen.ensure_compile()

        gen_time = os.path.getmtime(gen.get_executable_path())
        desc_time = os.path.getmtime(self.get_descriptor_path())
        try:
            res_time = os.path.getmtime(self.get_input_path())
        except OSError:
            res_time = float("-inf")

        if res_time < max(gen_time, desc_time):
            logger.info("Generating test {index}", index=self.index)
            dirname = os.path.dirname(self.get_input_path())
            os.makedirs(dirname, exist_ok=True)
            gen.generate(self.get_input_path(), args)


def expand_range(val):
    """Expands the Haskell-like range given as a parameter
    into Python's `range` object. The range must be finite.

    Args:
        val (str): a range to expand.

    Returns:
        range: resulting range.

    Raises:
        ValueError: if given an invalid Haskell-like range.

    >>> expand_range("[1..10]")
    range(1, 11)

    >>> expand_range("[1,3..10]")
    range(1, 11, 2)

    >>> expand_range("[5,4..1]")
    range(5, 0, -1)
    """

    if not val.startswith("[") or not val.endswith("]"):
        raise ValueError("Invalid bracket placement")

    val = val[1:-1]
    spl = val.split("..")
    if len(spl) != 2 or not all(spl):
        raise ValueError("Invalid range")

    end = int(spl[1])
    if "," in spl[0]:
        begin, bstep = map(int, spl[0].split(","))
        step = bstep - begin
    else:
        begin = int(spl[0])
        step = 1

    if step == 0:
        raise ValueError("Zero step is not allowed")

    if step > 0:
        end += 1
    else:
        end -= 1

    return range(begin, end, step)


def expand_generator_command(cmd):
    """Expands a generator command into a list of generator commands
    by expanding the ranges inside it.

    Args:
        cmd (str): the source command

    Returns:
        list: a list of strs, the expanded generator commands

    >>> expand_generator_command("gen 123")
    ["gen 123"]

    >>> expand_generator_command("gen [1..3] [1..2]")
    ["gen 1 1", "gen 2 1", "gen 3 1", "gen 1 2", "gen 2 2", "gen 3 2"]
    """

    spl = shlex.split(cmd)
    res = []

    for token in spl:
        try:
            expanded = expand_range(token)
        except ValueError:
            expanded = [token]
        res.append(list(map(shlex.quote, map(str, expanded))))

    return list(map(" ".join, itertools.product(*res)))
