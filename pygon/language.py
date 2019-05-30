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

"""This module defines classes for working with languages / compilers."""

import subprocess
from abc import ABC, abstractmethod


class Language(ABC):
    """Programming language / compiler."""

    @abstractmethod
    def get_compile_command(self, src, exe):
        """Returns compilation command as list of strings
        or None if compilation is not required.

        Args:
            src: absolute path to source code file
            exe: absolute path to resulting executable

        Returns:
            None or compilation command as a list of strings, for example:
            ["gcc", "-std=c99", "-O2", "/tmp/test.c", "-o", "/tmp/test"]
        """

    @abstractmethod
    def get_execute_command(self, src, exe):
        """Returns execution command as list of strings.

        Args:
            src: absolute path to source code file.
            exe: absolute path to executable.

        Returns:
            None or execution command as a list of strings, for example:
            ["python3", "/tmp/test.py"].
        """

    @staticmethod
    def from_name(name):
        """Returns a configured Language with specified name."""
        # TODO

    def compile(self, src, exe):
        """Unconditionally compiles a file.

        Args:
            src: absolute path to source code file.
            exe: absolute path to resulting executable.

        Raises:
            CalledProcessError: if compiler returns non-zero exit code.
        """
        cmd = self.get_compile_command(src, exe)
        if not cmd:
            return
        subprocess.run(cmd, check=True)
