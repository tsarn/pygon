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

"""This module defines class for working with checkers."""

import subprocess
from collections import namedtuple

from pygon.source import Source
from pygon.testcase import Verdict


class CheckerVerdict(namedtuple('CheckerVerdict', 'verdict comment')):
    """Checker's verdict on a solution with a comment."""


class Checker(Source):
    """A checker for a problem"""

    directory_name = "checkers"
    standard_instances = [
        "fcmp",
        "hcmp",
        "lcmp",
        "ncmp",
        "wcmp",
        "yesno",
    ]

    def __init__(self, **kwargs):
        """Constructs a Checker.

        Args:
            standard: None if custom checker, one of Checker.STANDARD otherwise.

        Args (if not standard):
            name: name of the checker with extension (e.g. "checker.cpp").
            problem: Problem which this checker belongs to.
            lang: Language of the checker.
        """

        super(Checker, self).__init__(**kwargs)

    def judge(self, inp, out, ans):
        """Judges a solution on a test.
        Expects checker to be already compiled.

        Args:
            inp: path to the test's input file.
            out: path to the solution's output on this test.
            ans: path to the correct solution's output on this test.

        Returns:
            CheckerVerdict: instance containing the judgement.
        """

        cmd = self.get_execute_command()
        cmd += [inp, out, ans]
        res = subprocess.run(cmd, stderr=subprocess.PIPE,
                             universal_newlines=True)
        verdict = Verdict.CHECK_FAILED
        if res.returncode == 0:
            verdict = Verdict.OK
        elif res.returncode == 1:
            verdict = Verdict.WRONG_ANSWER
        elif res.returncode == 2:
            verdict = Verdict.PRESENTATION_ERROR

        return CheckerVerdict(verdict, res.stderr.strip())
