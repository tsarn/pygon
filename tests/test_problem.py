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

import os
from os.path import normpath

from pygon.problem import Problem


class TestProblem:
    def test_get_source_filename(self, monkeypatch):
        p = Problem("/x/prob")
        monkeypatch.setattr(os, 'listdir', lambda _: [
            "test1.yaml",
            "test1.cpp",
            "test2.yaml",
            "test3.py",
        ])
        assert p.get_source_filename("sources", "test1") == "test1.cpp"
        assert p.get_source_filename("sources", "test2") == None

    def test_get_sources(self, monkeypatch):
        p = Problem("/x/prob")
        monkeypatch.setattr(os, 'listdir', lambda _: [
            "test1.yaml",
            "test1.cpp",
            "test2.yaml",
            "test3.py",
        ])
        assert p.get_sources("sources") == ["test1.cpp"]
