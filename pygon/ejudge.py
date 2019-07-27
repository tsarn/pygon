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

"""This module contains code for exporting to ejudge."""

import os
import sys
import io
import tarfile
import base64
import shlex
from shutil import copy2


TEST_PAT = "%02d"
CORR_PAT = "%02d.a"
CHECK_CMD = "check"
PATCHER = """#!/bin/sh

ME=$(readlink -f "$0")
DIR=$(dirname "$ME")
SRC="$DIR/contest.cfg"
TGT="$DIR/conf/serve.cfg"
sed '/PYGON_CONTEST_START/,/PYGON_CONTEST_END/d' "$TGT" > "$TGT.new"
echo >> "$TGT.new"
cat "$SRC" >> "$TGT.new"
mv "$TGT.new" "$TGT"
"""

def generate_config(problem, language=None, prefix=None):
    f = io.StringIO()

    print("[problem]", file=f)

    if problem.input_file.stdio:
        print("use_stdin = 1", file=f)
    else:
        print("use_stdin = 0", file=f)
        print("input_file = \"{}\"".format(problem.input_file), file=f)

    if problem.output_file.stdio:
        print("use_stdout = 1", file=f)
    else:
        print("use_stdout = 0", file=f)
        print("output_file = \"{}\"".format(problem.output_file), file=f)

    print("use_corr = 1", file=f)
    print("enable_testlib_mode = 1", file=f)
    print("time_limit_millis = {}".format(round(1000 * problem.time_limit)), file=f)

    mem_limit = "{}M".format(round(problem.memory_limit))
    print("max_vm_size = {}".format(mem_limit), file=f)
    print("max_stack_size = {}".format(mem_limit), file=f)

    if prefix:
        print("short_name = \"{}\"".format(prefix), file=f)

    for i in problem.get_statements():
        if i.language == language or language is None:
            print("long_name = \"{}\"".format(i.name), file=f)
            break

    print("internal_name = \"{}\"".format(problem.internal_name), file=f)
    print("test_pat = \"{}\"".format(TEST_PAT), file=f)
    print("corr_pat = \"{}\"".format(CORR_PAT), file=f)
    print("check_cmd = \"{}\"".format(CHECK_CMD), file=f)

    f.seek(0)
    return f.read()


def export_problem(problem, target, language=None, prefix=None):
    """Exports problem to target directory."""

    os.makedirs(target, exist_ok=True)
    os.makedirs(os.path.join(target, "tests"), exist_ok=True)

    with open(os.path.join(target, "problem.cfg"), "w") as f:
        f.write(generate_config(problem, language=language, prefix=prefix))

    copy2(problem.active_checker.get_executable_path(),
             os.path.join(target, CHECK_CMD))

    main = problem.get_main_solution()

    for test in problem.get_solution_tests():
        copy2(test.get_input_path(),
                 os.path.join(target, "tests", TEST_PAT % test.index))

        copy2(test.get_output_path(main.identifier),
                 os.path.join(target, "tests", CORR_PAT % test.index))


def export_contest(contest, target, language=None):
    """Exports contest to target directory."""

    os.makedirs(target, exist_ok=True)
    os.makedirs(os.path.join(target, "problems"), exist_ok=True)

    for prefix, problem in contest.problems:
        export_problem(problem,
                       os.path.join(target, "problems", problem.internal_name),
                       language=language, prefix=prefix)

    last_id = 0
    with open(os.path.join(target, "contest.cfg"), "w") as f:
        print("# PYGON_CONTEST_START", file=f)
        for prefix, problem in contest.problems:
            cfg = generate_config(problem, language=language, prefix=prefix)
            f.write(cfg)
            last_id += 1
            print("id = {}".format(last_id), file=f)
            print(file=f)
        print("# PYGON_CONTEST_END", file=f)

    with open(os.path.join(target, "patch.sh"), "w") as f:
        f.write(PATCHER)


def write_script(target, contest_dir=None, fd=sys.stdout):
    archive = io.BytesIO()

    with tarfile.open(fileobj=archive, mode="w:gz") as f:
        f.add(target, arcname=".")

    if contest_dir:
        print("""#!/bin/sh
OLDPATH="$(pwd)"
cd %s
""" % shlex.quote(contest_dir), file=fd)
    else:
        print("""#!/bin/sh

if [ "x$1" = "x" ]; then
    echo "Usage: $0 <contest directory>"
    exit 1
fi

OLDPATH="$(pwd)"
cd "$1"
""", file=fd)

    print("""
rm -rf problems contest.cfg patch.sh

cat << _EOF | base64 -d | tar xz""", file=fd)

    archive.seek(0)
    print(base64.b64encode(archive.read()).decode(), file=fd)

    print("""_EOF
sh ./patch.sh
cd "$OLDPATH"
""", file=fd)
