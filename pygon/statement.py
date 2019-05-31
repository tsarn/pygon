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

"""This module defines class for working with statements."""

import os
import subprocess

from loguru import logger
from pkg_resources import resource_filename

from pygon.config import BUILD_DIR, CONFIG


class Statement:
    """A statement for a problem.

    Attributes:
        problem: a Problem for this statement.
        name: full problem name (e.g. "A + B")
        language: statement's language in lowercase english (e.g. "russian")
    """

    def __init__(self, problem, name, language="english"):
        self.problem = problem
        self.name = name
        self.language = language

    def get_statement_root(self):
        """Returns path to statement root."""

        return os.path.join(self.problem.root, "statements", self.language)

    def get_statement_path(self):
        """Returns path to statement's TeX source file."""

        return os.path.join(self.get_statement_root(), "problem.tex")

    def get_build_root(self):
        """Returns path to build root."""

        return os.path.join(self.problem.root, BUILD_DIR,
                            "statements", self.language)

    def get_log_path(self):
        """Returns path to TeX Live log."""

        return os.path.join(self.get_build_root(), "statements.log")

    def get_time_limit(self):
        """Returns humanized time limit in statement's language."""

        suff = "seconds"
        time = self.problem.time_limit

        if self.language == "russian":
            suff = "секунд"
            if time == round(time):
                written = str(round(time))
                if len(written) == 1 or written[-2] != "1":
                    if written[-1] == "1":
                        suff = "секунда"
                    elif written[-1] in "234":
                        suff = "секунды"
        elif self.language == "english":
            if time == 1:
                suff = "second"

        return "{:.03f}".format(time).rstrip("0.") + " " + suff

    def get_memory_limit(self):
        """Returns humanized memory limit in statement's language."""

        suff = "MiB"
        mem = self.problem.memory_limit

        if self.language == "russian":
            suff = "мегабайт"

            if mem == round(mem):
                written = str(round(mem))
                if len(written) == 1 or written[-2] != "1":
                    if written[-1] in "234":
                        suff = "мегабайта"

        return "{:.03f}".format(mem).rstrip("0.") + " " + suff

    def get_resource_dirs(self):
        """Returns list of resource directories."""

        return [
            self.get_statement_root(),
            os.path.join(self.problem.root, "resources"),
            resource_filename("pygon", os.path.join("data", "resources"))
        ]

    def read_resource(self, name):
        """Searches for a resource with name in resource search path
        and reads it into string."""

        from pygon.problem import ProblemConfigurationError

        for i in self.get_resource_dirs():
            if os.path.exists(os.path.join(i, name)):
                with open(os.path.join(i, name)) as res:
                    return res.read()

        raise ProblemConfigurationError("Resource {} not found".format(name))

    def build(self):
        """Builds the statement."""

        root = self.get_build_root()
        os.makedirs(root, exist_ok=True)

        with open(os.path.join(root, "olymp.sty"), "w") as f:
            f.write(self.read_resource("olymp.sty"))

        stmt = self.read_resource("statements.tex")

        stmt = stmt.replace("#Language#", "[" + self.language + "]" if
                            self.language in ["russian"] else "")
        stmt = stmt.replace("#ContestName#", "")
        stmt = stmt.replace("#ContestLocation#", "")
        stmt = stmt.replace("#ContestDate#", "")
        stmt = stmt.replace("#Statements#", self.get_tex_statement())

        with open(os.path.join(root, "statements.tex"), "w") as f:
            f.write(stmt)

        cmd = [
            CONFIG.get("pdflatex", "pdflatex"),
            "-interaction=batchmode",
            "statements.tex",
        ]

        logger.info("Building {} statement", self.language)
        subprocess.run(cmd, cwd=root, check=True, stdout=subprocess.DEVNULL)

    def get_tex_samples(self):
        """Returns sample tests in TeX source code form."""

        tests = []
        main_solution = self.problem.get_main_solution()

        for test in self.problem.get_solution_tests():
            if not test.sample:
                continue

            with open(test.get_input_path()) as f:
                inp = f.read()

            with open(test.get_output_path(main_solution.identifier)) as f:
                ans = f.read()

            tests.append((inp, ans))

        if not tests:
            return ""

        res = "\n\\Examples\n"

        for inp, ans in tests:
            res += r"""
\begin{example}
\exmp{%
INP}{%
ANS}%
\end{example}
""".replace("INP", inp).replace("ANS", ans)

        return res

    def get_tex_statement(self):
        """Returns a TeX code to include the statement."""

        return r"""
\def\ShortProblemTitle{}
\graphicspath{%s}
\begin{problem}{%s}{%s}{%s}{%s}{%s}
\input{%s}
%s
\end{problem}
""" % ("".join("{" + i + "}" for i in self.get_resource_dirs()),
       self.name,
       self.problem.input_file.statement_str("input", self.language),
       self.problem.output_file.statement_str("output", self.language),
       self.get_time_limit(), self.get_memory_limit(),
       self.get_statement_path(),
       self.get_tex_samples())
