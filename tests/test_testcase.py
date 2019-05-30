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

from os.path import normpath

from pygon.testcase import FileName, SolutionTest
from pygon.problem import Problem

class TestFileName:
    def test_str_stdio(self):
        f = FileName(stdio=True)
        assert str(f) == "stdio"

    def test_str_filename(self):
        f = FileName(filename="input.txt")
        assert str(f) == "input.txt"

    def test_statement_str_stdio(self):
        f = FileName(stdio=True)
        assert f.statement_str("input") == "standard input"
        assert f.statement_str("output") == "standard output"

    def test_statement_str_filename(self):
        f = FileName(filename="input.txt")
        assert f.statement_str("input") == "input.txt"
        assert f.statement_str("output") == "input.txt"


class TestSolutionTest:
    def test_get_descriptor_path(self):
        t = SolutionTest(index=5, problem=Problem('/x/prob'))
        assert t.get_descriptor_path() == normpath("/x/prob/tests/05.yaml")

    def test_get_input_path_manual(self):
        t = SolutionTest(index=5, problem=Problem('/x/prob'))
        assert t.get_input_path() == normpath("/x/prob/tests/05")

    def test_get_input_path_generated(self):
        t = SolutionTest(index=5, problem=Problem('/x/prob'), generate="gen")
        assert t.get_input_path() == normpath("/x/prob/pygon-build/tests/05")
