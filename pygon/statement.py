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

"""This module defines class for working with statements."""

import os
import subprocess

from loguru import logger
import yaml
from pkg_resources import resource_filename

from pygon.config import BUILD_DIR, CONFIG, TEST_FORMAT


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
        else:
            if time == round(time):
                if format(round(time), "02d").endswith("01"):
                    suff = "second"

        return "{:.03f}".format(time).rstrip("0.") + " " + suff

    def get_memory_limit(self):
        """Returns humanized memory limit in statement's language."""

        suff = "mebibytes"
        mem = self.problem.memory_limit

        if self.language == "russian":
            suff = "мегабайт"

            if mem == round(mem):
                written = str(round(mem))
                if len(written) == 1 or written[-2] != "1":
                    if written[-1] in "234":
                        suff = "мегабайта"
        else:
            if mem == round(mem):
                if format(round(mem), "02d").endswith("01"):
                    suff = "mebibyte"

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
        stmt = stmt.replace("#Preamble#", r"""
\makeatletter
\renewcommand{\@oddhead}{}
\makeatother
""")
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

    def get_test_presentation(self, index):
        """Returns information about test's presentation in statements
        as dict with following keys:

        wide(bool): use examplewide environment?
        note(str): if not None, use examplethree environment with this note.
        input(str): custom input data.
        answer(str): custom answer data.
        """

        data = {
            "wide": False,
            "note": None,
            "input": None,
            "answer": None
        }

        paths = [
            os.path.join(self.problem.root, "statements", "tests",
                         TEST_FORMAT.format(index) + ".yaml"),
            os.path.join(self.get_statement_root(), "tests",
                         TEST_FORMAT.format(index) + ".yaml"),
        ]

        for path in paths:
            try:
                with open(path) as f:
                    data.update(yaml.safe_load(f))
            except OSError:
                pass

        return data

    def get_tex_samples(self):
        """Returns sample tests in TeX source code form."""

        tests = []
        main_solution = self.problem.get_main_solution()

        for test in self.problem.get_solution_tests():
            if not test.sample:
                continue

            inp_path = test.get_input_path()
            ans_path = test.get_output_path(main_solution.identifier)

            data = self.get_test_presentation(test.index)

            if data["input"]:
                inp_path = os.path.join(self.get_build_root(),
                                        "test.{}".format(test.index))
                with open(inp_path, "w") as f:
                    f.write(data["input"])

            data["inp_path"] = inp_path

            if data["answer"]:
                ans_path = os.path.join(self.get_build_root(),
                                        "test.{}.a".format(test.index))
                with open(ans_path, "w") as f:
                    f.write(data["answer"])

            data["ans_path"] = ans_path

            tests.append(data)

        if not tests:
            return ""

        if len(tests) > 1:
            res = ["\\Examples"]
        else:
            res = ["\\Example"]

        prev_env = None
        for data in tests:
            if data["note"] is not None:
                env = "examplethree"
            elif data["wide"]:
                env = "examplewide"
            else:
                env = "example"

            if env != prev_env:
                if prev_env:
                    res.append("\\end{%s}" % prev_env)
                res.append("\\begin{%s}" % env)
                prev_env = env

            res.append("\\exmpfile{%s}{%s}" % (data["inp_path"], data["ans_path"]))

            if env == "examplethree":
                res[-1] += "{%s}" % data["note"]

        res.append("\\end{%s}" % prev_env)

        return "\n".join(res)

    def get_tex_statement(self):
        """Returns a TeX code to include the statement."""

        return r"""
\def\ShortProblemTitle{}
\graphicspath{%s}
\begin{problem}{%s}{%s}{%s}{%s}{%s}
\renewcommand{\SAMPLES}{%s}
\input{%s}
\end{problem}
""" % ("".join("{" + i + "}" for i in self.get_resource_dirs()),
       self.name,
       self.problem.input_file.statement_str("input", self.language),
       self.problem.output_file.statement_str("output", self.language),
       self.get_time_limit(), self.get_memory_limit(),
       self.get_tex_samples(),
       self.get_statement_path())
