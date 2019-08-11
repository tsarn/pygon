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

"""This module contains pygon CLI."""

import os
import sys
import re
import tempfile

import click
from tabulate import tabulate
from loguru import logger

from pygon.config import CONFIG, BUILD_DIR
from pygon.problem import Problem, ProblemConfigurationError
from pygon.contest import Contest, switch_logger
from pygon.checker import Checker
from pygon.validator import Validator
from pygon.generator import Generator
from pygon.solution import Solution
from pygon.interactor import Interactor
from pygon.testcase import SolutionTest, expand_generator_command
from pygon.ejudge import write_script as write_ejudge_script


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


def get_problem_or_contest():
    dirname = os.getcwd()

    while True:
        if os.path.exists(os.path.join(dirname, "problem.yaml")):
            prob = Problem(dirname)
            prob.load()
            return prob

        if os.path.exists(os.path.join(dirname, "contest.yaml")):
            cont = Contest(dirname)
            cont.load()
            return cont

        dirname = os.path.dirname(dirname)

        if os.path.dirname(dirname) == dirname:
            break

    logger.error("Not in a problem or contest directory")
    sys.exit(1)


@click.group()
@click.option("-v", "--verbose", count=True, help="Show more output")
def cli(verbose):
    if verbose == 1:
        CONFIG["level"] = "INFO"
    elif verbose > 1:
        CONFIG["level"] = "DEBUG"

    switch_logger()

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
              "tests", "validators", "interactors"]:
        os.makedirs(os.path.join(dirname, i), exist_ok=True)

    with open(os.path.join(dirname, "problem.yaml"), "w") as desc:
        print("""\
# Internal problem name, should be concise,
# recognisable and match the directory name.
internal_name: "{}"

# Is this problem interactive?
interactive: false

# Input file name, or "standard_io" if reading from standard input.
# Must be "standard_io" for interactive problems.
input_file: standard_io

# Output file name, or "standard_io" if writing to standard output.
# Must be "standard_io" for interactive problems.
output_file: standard_io

# Time limit per test in seconds.
time_limit: 1.0

# Memory limit per test in MiB.
memory_limit: 256

# Active checker, default is probably good enough if you have single possible answer.
active_checker: standard.lcmp

# Active validators, default checks that tests are reasonably formatted.
active_validators: [standard.wfval]

# Active interactor. Uncomment following line if `interactive` is true.
# active_interactor: (YOUR INTERACTOR HERE)
""".format(name), file=desc, end="")


@click.command(help="Create a new contest")
@click.argument("name")
def initcontest(name):
    if not re.match(r'^[a-z0-9-]+$', name):
        print("Please use lowercase English letters, numbers, "
              "and dashes for the contest name")
        sys.exit(1)
    dirname = os.path.abspath(name)

    if os.path.exists(dirname):
        print("Directory '{}' already exists".format(dirname))
        sys.exit(1)

    os.makedirs(os.path.join(dirname, "problems"), exist_ok=True)
    os.makedirs(os.path.join(dirname, "resources"), exist_ok=True)

    with open(os.path.join(dirname, "contest.yaml"), "w") as desc:
        print("""\
name:
    english: "Example contest"

location:
    english: "London, UK"

date:
    english: "Jan 1, 2019"

# Uncomment following lines when adding problems:

# problems:
#     - id: problem-one       # Problem's internal name
#       prefix: A             # Problem's prefix in contest
#     - id: problem-two
#       prefix: B
""".format(name), file=desc, end="")


@click.command(help="Export problem or contest to ejudge")
@click.option("-l", "--language", help="Language for full problem names (e.g. \"english\")")
def ejudgeexport(language=None):
    prob = get_problem_or_contest()

    try:
        prob.build(statements=False)
        prob.ejudge_export(language=language)
    except ProblemConfigurationError as e:
        logger.error("Problem configuration error: {}", str(e))
        sys.exit(1)


@click.command(help="Print ejudge deployment script")
@click.option("-l", "--language", help="Language for full problem names (e.g. \"english\")")
@click.option("-d", "--directory", help="Directory for contest (e.g. \"/home/judges/000001\")")
def ejudgedeploy(language=None, directory=None):
    cont = get_problem_or_contest()

    try:
        cont.build(statements=False)
        cont.ejudge_export(language=language)
        write_ejudge_script(os.path.join(cont.root, BUILD_DIR, "ejudge"), contest_dir=directory)
    except ProblemConfigurationError as e:
        logger.error("Problem configuration error: {}", str(e))
        sys.exit(1)


@click.command(help="Build problem or contest")
@click.option("--statements/--no-statements", help="Build statements?",
              default=True, show_default=True)
def build(statements):
    prob = get_problem_or_contest()

    try:
        prob.build(statements=statements)
    except ProblemConfigurationError as e:
        logger.error("Problem configuration error: {}", str(e))
        sys.exit(1)


@click.command(help="Lint problem or contest for configuration errors")
def verify():
    prob = get_problem_or_contest()

    try:
        prob.verify()
    except ProblemConfigurationError as e:
        logger.error("Problem configuration error: {}", str(e))
        sys.exit(1)


@click.command(help="Generate descriptors for sources that don't have them")
def discover():
    prob = get_problem()
    prob.discover_sources(Checker)
    prob.discover_sources(Generator)
    prob.discover_sources(Validator)
    prob.discover_sources(Solution)

    if prob.interactive:
        prob.discover_sources(Interactor)


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

    need_judging = 0

    for test in tests:
        for solution in solutions:
            if solution.need_judge(test):
                need_judging += 1

    with click.progressbar(length=need_judging) as bar:
        for test in tests:
            data.append([str(test.index)])
            for i, solution in enumerate(solutions):
                if solution.need_judge(test):
                    bar.update(1)
                res = solution.judge(test)
                verdicts[i].append(res.verdict)
                s = click.style(res.verdict.value, fg="green" if
                                solution.tag.check_one(res.verdict) else "red",
                                bold=True)
                s += " {:>4} ms {:>3} MiB".format(round(res.time * 1000), round(res.memory))
                data[-1].append(s)

    data.append(["Tag correct?"])
    exitcode = 0
    for i, solution in enumerate(solutions):
        valid = solution.tag.check_all(verdicts[i])
        if valid:
            s = click.style("YES", fg="green", bold=True)
        else:
            s = click.style("NO", fg="red", bold=True)
            exitcode = 1
        data[-1].append(s)

    click.echo(tabulate(data, header, tablefmt="presto"))
    sys.exit(exitcode)


@click.command(help="Stress-test solutions for tag violations")
@click.option("-s", "--solutions", help="Comma-separated subset of solutions to run (default: all except main)")
@click.argument("command")
def stress(command, solutions):
    prob = get_problem()

    try:
        prob.build(statements=False)
    except ProblemConfigurationError as e:
        logger.error("Problem configuration error: {}", str(e))
        sys.exit(1)

    if not solutions:
        solutions = [i for i in Solution.all(prob) if i.tag.tag != "main"]
    else:
        solutions = [Solution.from_identifier(i, prob) for i in solutions.split(",")]

    if not solutions:
        logger.warning("No solutions to stress")
        return

    commands = expand_generator_command(command)

    offenders = {}
    verdicts = {}

    for solution in solutions:
        offenders[solution.name] = None
        verdicts[solution.name] = set()

    main_solution = prob.get_main_solution()

    with tempfile.TemporaryDirectory() as dirname:
        with click.progressbar(commands) as bar:
            for cmd in bar:
                test = SolutionTest(problem=prob, generate=cmd,
                                    dirname=dirname)
                test.build()
                main_solution.judge(test)
                failed = set()
                for i, solution in enumerate(solutions):
                    res = solution.judge(test)
                    verdicts[solution.name].add(res.verdict)
                    if not solution.tag.check_one(res.verdict):
                        offenders[solution.name] = cmd
                        failed.add(i)
                solutions = [x for i, x in enumerate(solutions) if i not in failed]
                if not solutions:
                    break

    for solution, cmd in offenders.items():
        click.echo("{} displayed verdicts: ".format(click.style(solution, bold=True)), nl=False)
        click.echo(", ".join([i.styled for i in verdicts[solution]]), nl=False)
        if cmd is None:
            click.echo(" (no counterexample found)")
        else:
            click.echo(" (found counterexample: {})".format(cmd))


cli.add_command(init)
cli.add_command(initcontest)
cli.add_command(build)
cli.add_command(verify)
cli.add_command(discover)
cli.add_command(edittests)
cli.add_command(addstatement)
cli.add_command(invoke)
cli.add_command(stress)
cli.add_command(ejudgeexport)
cli.add_command(ejudgedeploy)


def main():
    cli()
