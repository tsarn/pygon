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

from pygon.language import Language, Source
from pygon.problem import Problem

class MockLanguage(Language):
    def get_compile_command(self, src, exe):
        return [normpath("/x/compile"), src, exe]

    def get_execute_command(self, src, exe):
        return [normpath("/y/execute"), src, exe]


class MockSource(Source):
    directory_name = "mock"
    standard_instances = ["foo", "bar"]

custom_src = MockSource(name="test.cpp", problem=Problem(normpath("/x/prob")),
                        lang=MockLanguage())

class TestSource:
    def test_get_descriptor_path(self):
        assert custom_src.get_descriptor_path() == normpath("/x/prob/mock/test.yaml")

    def test_identifier(self):
        assert custom_src.identifier == "test"

    def test_get_execute_command(self):
        assert custom_src.get_execute_command() == [
            normpath("/y/execute"),
            normpath("/x/prob/mock/test.cpp"),
            normpath("/x/prob/pygon-build/mock/test")
        ]
