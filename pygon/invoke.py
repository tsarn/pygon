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

"""This module defines helper class for running solutions and
measuring their execution time."""

import os
import subprocess
import tempfile
from shutil import copyfile
from contextlib import contextmanager

import yaml

from pygon.testcase import Verdict
from pygon.config import CONFIG


class InvokeResult:
    """Result of the invocation.

    Attributes:
        verdict: a Verdict
        time: time used in seconds
        memory: memory used in MiB
        comment: checker's comment
    """

    def __init__(self, verdict, time, memory, comment=""):
        self.verdict = verdict
        self.time = time
        self.memory = memory
        self.comment = comment

    def to_dict(self):
        return dict(
            verdict=self.verdict.value,
            time=self.time,
            memory=self.memory,
            comment=self.comment
        )

    @classmethod
    def from_dict(cls, data):
        return cls(verdict=Verdict(data["verdict"]),
                   time=data["time"],
                   memory=data["memory"],
                   comment=data["comment"])


class Invoke:
    """Helper class for running solutions, redirecting their stdin/stdout,
    measuring their time and memory usage.
    Currenly using GNU time.

    Attributes:
        cmd: command to run as a list of strings.
        cwd: working directory of the command.
        stdin: file-like instance to redirect stdin from.
        stdout: file-like instance to redirect stdout to.
        time_limit: time limit in seconds.
        memory_limit: memory limit in MiB.
    """

    def __init__(self, cmd, time_limit=1.0, memory_limit=256.0):
        """Construct an Invoke instance."""

        self.cmd = cmd
        self.cwd = None
        self.stdin = None
        self.stdout = None
        self.time_limit = time_limit
        self.memory_limit = memory_limit

    def run(self):
        """Run the command."""

        with tempfile.TemporaryDirectory() as dirpath:
            logpath = os.path.join(dirpath, "time.out")

            cmd = [
                CONFIG.get("time", "/usr/bin/time"),
                "-q",
                "-f", "user: %U\nsystem: %S\nreal: %e\nmemory: %M",
                "-o", logpath
            ] + self.cmd

            verdict = Verdict.OK

            try:
                subprocess.run(cmd, stdin=self.stdin, stdout=self.stdout,
                               stderr=subprocess.DEVNULL, cwd=self.cwd,
                               timeout=5 * self.time_limit, check=True)
            except subprocess.TimeoutExpired:
                verdict = Verdict.REAL_TIME_LIMIT_EXCEEDED
            except subprocess.CalledProcessError:
                verdict = Verdict.RUNTIME_ERROR

            with open(logpath) as logf:
                log = yaml.safe_load(logf.read())

            time_used = log['user'] + log['system']
            memory_used = log['memory'] / 1024

            if verdict == Verdict.OK:
                if time_used > self.time_limit:
                    verdict = Verdict.TIME_LIMIT_EXCEEDED
                elif memory_used > self.memory_limit:
                    verdict = Verdict.MEMORY_LIMIT_EXCEEDED

            return InvokeResult(verdict, time_used, memory_used)

    @contextmanager
    def with_temp_cwd(self):
        """Use temporary working directory."""

        with tempfile.TemporaryDirectory() as dirpath:
            self.cwd = dirpath
            yield

        self.cwd = None

    @contextmanager
    def with_stdin(self, filename, path):
        """Redirect stdin transparently.

        Args:
            filename: a FileName instance, where will solution read input from?
            path: path to actual input file.
        """

        if filename.stdio:
            with open(path, 'rb') as input_file:
                self.stdin = input_file
                yield
        else:
            copyfile(path, os.path.join(self.cwd, filename.filename))
            self.stdin = subprocess.DEVNULL
            yield

        self.stdin = None

    @contextmanager
    def with_stdout(self, filename, path):
        """Redirect stdout transparently.

        Args:
            filename: a FileName instance, where will solution write to?
            path: path to output file.
        """

        if filename.stdio:
            with open(path, 'wb') as output_file:
                self.stdout = output_file
                yield
        else:
            self.stdout = subprocess.DEVNULL
            yield
            copyfile(os.path.join(self.cwd, filename.filename), path)

        self.stdout = None
