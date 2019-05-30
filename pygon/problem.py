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

"""This module defines class for working with problems"""

import os

from pygon.testcase import FileName, SolutionTest
from pygon.config import TEST_FORMAT

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

    def get_descriptor_path(self):
        """Returns a path to problem's descriptor file"""

        return os.path.join(self.root, "problem.yaml")

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
