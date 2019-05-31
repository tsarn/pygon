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

"""This module defines class for working with validators."""

import subprocess
from collections import namedtuple

from pygon.source import Source
from pygon.testcase import Verdict


class ValidatorVerdict(namedtuple('ValidatorVerdict', 'verdict comment')):
    """Validator's verdict on a test with a comment."""


class Validator(Source):
    """A validator for a problem."""

    directory_name = "validators"
    standard_instances = ["wfval"]

    def __init__(self, **kwargs):
        """Constructs a Validator.

        Args:
            standard: None if custom validator,
                      one of Validator.standard_instances otherwise.

        Args (if not standard):
            name: name of the validator with extension (e.g. "validator.cpp").
            problem: Problem which this validator belongs to.
            lang: Language of the validator.
        """

        super(Validator, self).__init__(**kwargs)

    def validate(self, path):
        """Validate a test.
        Expects validator to be already compiled.

        Args:
            path: path to the test's input file.

        Returns:
            ValidatorVerdict: instance containing the judgement.
        """

        cmd = self.get_execute_command()
        cmd += [path]
        with open(path, 'rb') as testf:
            res = subprocess.run(cmd, stderr=subprocess.PIPE,
                                 stdin=testf, universal_newlines=True)
        verdict = Verdict.VALIDATION_FAILED
        if res.returncode == 0:
            verdict = Verdict.OK

        return ValidatorVerdict(verdict, res.stderr)
