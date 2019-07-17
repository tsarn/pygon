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

"""This module defines class for working with generators."""

import subprocess

from pygon.source import Source


class Generator(Source):
    """A generator for a problem"""

    directory_name = "generators"

    def __init__(self, **kwargs):
        """Constructs a Generator.

        Args:
            name: name of the generator with extension (e.g. "gen.cpp").
            problem: Problem which this generator belongs to.
            lang: Language of the generator.
        """

        super(Generator, self).__init__(**kwargs)

    def generate(self, path, args):
        """Generates a test.
        Expects generator to be already compiled.

        Args:
            path: path to the test.
            args: a list of arguments to the generator.
        """

        cmd = self.get_execute_command()
        cmd += args
        with open(path, 'wb') as test:
            subprocess.run(cmd, stdout=test, check=True)
