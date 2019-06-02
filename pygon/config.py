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

"""This module defines some configuration."""

import os

import yaml
from click import get_app_dir

BUILD_DIR = "pygon-build"
TEST_FORMAT = "{:02d}"

DEFAULT_CONFIG_FILE = """\
# Path to pdflatex. Default works if pdflatex is in your PATH.
pdflatex: "pdflatex"

# Language configurations, pretty self-explanatory.
# Again, default works if necessary tools are in your PATH.
languages:
    c++03:
        compile: "g++ -Wall -O2 -lm -std=c++03 {src} -o {exe} {inc}"
    c++11:
        compile: "g++ -Wall -O2 -lm -std=c++11 {src} -o {exe} {inc}"
        autodetect: [".cc", ".cpp"]
    c++14:
        compile: "g++ -Wall -O2 -lm -std=c++14 {src} -o {exe} {inc}"
    c++17:
        compile: "g++ -Wall -O2 -lm -std=c++17 {src} -o {exe} {inc}"

    c99:
        compile: "gcc -Wall -O2 -lm -std=c99 {src} -o {exe} {inc}"
    c11:
        compile: "gcc -Wall -O2 -lm -std=c11 {src} -o {exe} {inc}"
        autodetect: [".c"]

    python2:
        execute: "python2 {src}"
    python3:
        execute: "python3 {src}"
        autodetect: [".py"]
"""


def load_config():
    """Reads config as a Python object. Creates config file if missing."""

    path = os.path.join(get_app_dir("pygon"), "pygon.yaml")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if not os.path.exists(path):
        with open(path, 'w') as cfg:
            cfg.write(DEFAULT_CONFIG_FILE)

    with open(path) as cfg:
        return yaml.safe_load(cfg.read())


CONFIG = load_config()
