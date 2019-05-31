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

"""This module contains pygon CLI."""

import os
import sys
import re

import click
from loguru import logger

from pygon.problem import Problem, ProblemConfigurationError
from pygon.checker import Checker
from pygon.validator import Validator
from pygon.generator import Generator


def get_problem():
    dirname = os.getcwd()

    while True:
        if os.path.exists(os.path.join(dirname, "problem.yaml")):
            prob = Problem(dirname)
            prob.load()
            return prob

        dirname = os.path.dirname(dirname)

        if os.path.dirname(dirname) == dirname:
            break

    logger.error("Not in a problem directory")
    sys.exit(1)


@click.group()
def cli():
    pass


@click.command(help="Create a new problem")
@click.argument("name")
def init(name):
    if not re.match(r'^[a-z0-9-]+$', name):
        print("Please use lowercase English letters, numbers, "
              "and dashes for the problem name")
        sys.exit(1)
    dirname = os.path.abspath(name)

    if os.path.exists(dirname):
        print("Directory '{}' already exists".format(dirname))
        sys.exit(1)

    for i in ["checkers", "generators", "resources", "solutions", "statements",
              "tests", "validators"]:
        os.makedirs(os.path.join(dirname, i), exist_ok=True)

    with open(os.path.join(dirname, "problem.yaml"), "w") as desc:
        print("""\
# Internal problem name, should be concise, recognisable and match the directory name
internal_name: "{}"

# Input file name, or "standard_io" if reading from standard input
input_file: standard_io

# Output file name, or "standard_io" if writing to standard output
output_file: standard_io

# Time limit per test in seconds
time_limit: 1.0

# Memory limit per test in MiB
memory_limit: 256

# Active checker, default is probably good enough if you have single possible answer
active_checker: standard.lcmp

# Active validators, default checks that tests are reasonably formatted
active_validators: [standard.wfval]
""".format(name), file=desc, end="")


@click.command(help="Build problem")
def build():
    prob = get_problem()

    try:
        prob.build()
    except ProblemConfigurationError as e:
        logger.error("Problem configuration error: {}", str(e))


cli.add_command(init)
cli.add_command(build)
