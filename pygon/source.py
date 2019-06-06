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

"""This module defines classes for working sources."""

import os
from abc import ABC

import yaml
from pkg_resources import resource_filename
from loguru import logger

from pygon.language import Language
from pygon.config import BUILD_DIR


class UnknownSourceError(Exception):
    """Raised when source with specified name could not be found."""


class Source(ABC):
    """A source file.

    Attributes:
        directory_name: directory name in problem hierarchy.
        standard_instances: list of identifiers of standard sources.
        standard: None if custom source, otherwise an identifier of standard
                  source (e.g. "lcmp").
        problem: the source's Problem.
        lang: the source's Language.
    """

    directory_name = "sources"
    standard_instances = []

    def __init__(self, standard=None, name=None, problem=None, lang=None):
        """Constructs a Source.

        Args:
            standard: None if custom source,
                      one of Source.standard_instances otherwise

        Args (if not standard):
            name: the source's name with extension (e.g. "source.cpp").
            problem: the source's Problem.
            lang: the source's Language.
        """

        if standard and standard not in self.standard_instances:
            raise ValueError("standard: expected one of {}, got {}".format(
                self.standard_instances, standard))

        self.standard = standard

        if standard:
            name = "{}.cpp".format(standard)
            lang = Language.from_name("c++11")

        self.name = name
        self.problem = problem
        self.lang = lang or Language.from_name(Language.autodetect(name))

    def get_source_path(self):
        """Returns path to source code file."""

        if self.standard:
            return resource_filename(
                "pygon", os.path.join("data", self.directory_name, self.name))

        return os.path.join(self.problem.root, self.directory_name, self.name)

    def get_executable_path(self):
        """Returns path to executable file."""

        from pygon.invoke import get_exe_suffix

        if self.standard:
            return resource_filename(
                "pygon",
                os.path.join("data", BUILD_DIR,
                             self.directory_name, self.standard) + get_exe_suffix())

        return os.path.join(self.problem.root, BUILD_DIR,
                            self.directory_name, self.identifier + get_exe_suffix())

    def get_resource_dirs(self):
        """Returns a list of resource directories in search order."""

        res = [resource_filename("pygon", os.path.join("data", "resources"))]

        if self.problem:
            res.insert(0, os.path.join(self.problem.root, "resources"))

        return res

    @property
    def identifier(self):
        """Returns source's identifier, usually filename without extension."""

        if self.standard:
            return "standard.{}".format(self.standard)

        return os.path.splitext(self.name)[0]

    @classmethod
    def from_identifier(cls, identifier, problem):
        """Construct an existing Source from an identifier and a problem."""

        if identifier.startswith("standard."):
            return cls(standard=identifier[len("standard."):])

        name = problem.get_source_filename(cls.directory_name, identifier)
        if name is None:
            raise UnknownSourceError("{} is not among {} of problem {}".format(
                identifier,
                cls.directory_name,
                problem.internal_name))

        res = cls(name=name, problem=problem)
        res.load()
        return res

    @classmethod
    def all(cls, problem):
        """Loads all problem's sources of this type.

        Args:
            problem: the relevant Problem instance.

        Returns:
            a list of Sources.
        """

        res = []

        for name in problem.get_sources(cls.directory_name):
            src = cls(name=name, problem=problem)
            src.load()
            res.append(src)

        return res

    def load(self):
        """Loads data about itself from the descriptor file."""

        with open(self.get_descriptor_path()) as desc:
            data = yaml.safe_load(desc)

        self.lang = Language.from_name(data.get('language'))

    def save(self):
        """Save data about itself into the descriptor file."""

        with open(self.get_descriptor_path(), "w") as desc:
            yaml.dump(dict(language=self.lang.name),
                      desc, default_flow_style=False)

    def get_descriptor_path(self):
        """Returns path to descriptor, where information
        about the source is stored.
        """

        return os.path.splitext(self.get_source_path())[0] + ".yaml"

    def compile(self):
        """Compiles the source.

        Raises:
            CalledProcessError: if compiler returns non-zero exit code.
        """

        logger.info("Compiling {} '{}'", self.directory_name[:-1], self.identifier)

        dirname = os.path.dirname(self.get_executable_path())
        os.makedirs(dirname, exist_ok=True)
        self.lang.compile(self.get_source_path(), self.get_executable_path(),
                          self.get_resource_dirs())

    def ensure_compile(self):
        """Compiles the source if executable is missing or
        is older than the source file.

        Raises:
            OSError: if source file doesn't exist or is inaccessible.
            CalledProcessError: if compiler returns non-zero exit code.
        """

        src_time = os.path.getmtime(self.get_source_path())

        if self.standard:
            desc_time = float("-inf")
        else:
            desc_time = os.path.getmtime(self.get_descriptor_path())

        try:
            exe_time = os.path.getmtime(self.get_executable_path())
        except OSError:
            exe_time = float("-inf")

        if exe_time < max(desc_time, src_time):
            self.compile()

    def get_execute_command(self):
        """Returns a command to execute the source.

        Returns:
            a list of strings: the command.
        """

        return self.lang.get_execute_command(self.get_source_path(),
                                             self.get_executable_path())
