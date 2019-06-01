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
from tabulate import tabulate
from loguru import logger

from pygon.problem import Problem, ProblemConfigurationError
from pygon.checker import Checker
from pygon.validator import Validator
from pygon.generator import Generator
from pygon.solution import Solution


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


@click.command(help="Generate descriptors for sources that don't have them")
def discover():
    prob = get_problem()
    prob.discover_sources(Checker)
    prob.discover_sources(Generator)
    prob.discover_sources(Validator)
    prob.discover_sources(Solution)


@click.command(help="Manage tests: reorder, remove, add")
def edittests():
    prob = get_problem()
    result = click.edit(prob.edit_solution_tests(), extension=".conf")
    if not click.confirm("This is a possibly destructive action. Continue?"):
        return
    prob.update_solution_tests(result)


@click.command(help="Create a new statement")
@click.option("-l", "--language", prompt="New statement's language (e.g. \"english\")")
@click.option("-n", "--name", prompt="Full name of the problem in this language")
def addstatement(language, name):
    prob = get_problem()
    prob.add_statement(language, name)


@click.command(help="Run solutions on tests")
@click.option("-t", "--tests", help="Comma-separated subset of tests to run (default: all)")
@click.option("-s", "--solutions", help="Comma-separated subset of solutions to run (default: all)")
def invoke(tests=None, solutions=None):
    prob = get_problem()

    try:
        prob.build(statements=False)
    except ProblemConfigurationError as e:
        logger.error("Problem configuration error: {}", str(e))
        sys.exit(1)

    if not tests:
        tests = prob.get_solution_tests()
    else:
        res = []
        for i in tests.split(","):
            if "-" in i:
                begin, end = map(int, i.split("-"))
                res += list(range(begin, end+1))
            else:
                res.append(int(i))
        tests = []
        res = set(res)
        for test in prob.get_solution_tests():
            if test.index in res:
                tests.append(test)

    if not solutions:
        solutions = Solution.all(prob)
    else:
        solutions = [Solution.from_identifier(i, prob) for i in solutions.split(",")]

    header = ["Test"] + [i.name for i in solutions]
    data = []
    verdicts = [[] for _ in solutions]

    for test in tests:
        data.append([str(test.index)])
        for i, solution in enumerate(solutions):
            res = solution.judge(test)
            verdicts[i].append(res.verdict)
            s = click.style(res.verdict.value, fg="green" if
                            solution.tag.check_one(res.verdict) else "red",
                            bold=True)
            s += " {} ms / {} MiB".format(round(res.time * 1000), round(res.memory))
            data[-1].append(s)

    data.append(["Tag correct?"])
    for i, solution in enumerate(solutions):
        valid = solution.tag.check_all(verdicts[i])
        if valid:
            s = click.style("YES", fg="green", bold=True)
        else:
            s = click.style("NO", fg="red", bold=True)
        data[-1].append(s)

    click.echo(tabulate(data, header, tablefmt="presto"))

cli.add_command(init)
cli.add_command(build)
cli.add_command(discover)
cli.add_command(edittests)
cli.add_command(addstatement)
cli.add_command(invoke)


def main():
    cli()
