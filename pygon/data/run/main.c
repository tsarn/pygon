// Copyright (c) 2019 Tsarev Nikita
//
// Permission is hereby granted, free of charge, to any person obtaining
// a copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so, subject to
// the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
// IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
// CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
// TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#include "run.h"
#include <stdio.h>
#include <stdlib.h>

static char *verdicts[] = {
    "ERR",
    "OK",
    "TL",
    "ML",
    "RL"
};

int main(int argc, char **argv)
{
    // Usage: run <tl> <ml> <rl> <log> <args>
    if (argc <= 5) {
        fprintf(stderr, "not enough arguments\n");
        return 1;
    }
    result_t res;

    int tl = atoi(argv[1]);
    int ml = atoi(argv[2]);
    int rl = atoi(argv[3]);

    run(argc - 5, argv + 5, tl, ml, rl, &res);

    FILE *f = fopen(argv[4], "w");
    fprintf(f, "verdict: %s\n", verdicts[res.verdict + 1]);
    fprintf(f, "exitcode: %d\n", res.exitcode);
    fprintf(f, "time: %d\n", res.time);
    fprintf(f, "memory: %d\n", res.memory);
    fclose(f);

    return 0;
}
