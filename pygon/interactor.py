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

import os
import subprocess
from collections import namedtuple

from pygon.source import Source
from pygon.testcase import Verdict


class Interactor(Source):
    """An interactor for an interactive problem."""

    directory_name = "interactors"

    def __init__(self, **kwargs):
        """Constructs a Interactor.

        Args:
            name: name of the interactor with extension (e.g. "interactor.cpp").
            problem: Problem which this interactor belongs to.
            lang: Language of the interactor.
        """

        super(Interactor, self).__init__(**kwargs)

    def interact(self, inp, out, invoke):
        """Interacts with a solution on a test.
        Expects interactor to be already compiled.

        Args:
            inp: path to the test's input file.
            out: path to the interactor's output on this test.
            invoke (Invoke): invoker of the solution.

        Returns:
            InvokeResult: instance containing the judgement.
        """

        cmd = self.get_execute_command()
        cmd += [inp, out]
        rd, wr = os.pipe()
        proc = subprocess.Popen(cmd, stdin=rd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        invoke.stdin = proc.stdout
        invoke.stdout = wr
        res = invoke.run()
        os.close(rd)
        os.close(wr)
        proc.wait()

        res.icomment = proc.stderr.read().decode().strip()

        if res.verdict != Verdict.OK:
            return res

        res.verdict = Verdict.CHECK_FAILED
        if proc.returncode == 0:
            res.verdict = Verdict.OK
        elif proc.returncode == 1:
            res.verdict = Verdict.WRONG_ANSWER
        elif proc.returncode == 2:
            res.verdict = Verdict.PRESENTATION_ERROR

        return res
