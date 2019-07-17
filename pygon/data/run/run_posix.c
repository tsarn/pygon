// Copyright (c) 2019 Nikita Tsarev
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

#define _DEFAULT_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/wait.h>

#define OK 0
#define TL 1
#define ML 2
#define RL 3

typedef struct {
    int verdict;
    int exitcode;
    int time;
    int memory;
} result_t;

static char *verdicts[] = {
    "ERR",
    "OK",
    "TL",
    "ML",
    "RL"
};

static result_t *res;
static int pid;

static void onalarm(int sig)
{
    res->verdict = RL;
    kill(pid, SIGKILL);
}

void run(int argc, char **argv, int tl, int ml, int rl, result_t *r)
{
    res = r;
    res->verdict = -1;
    res->exitcode = 0;
    res->time = 0;
    res->memory = 0;

    pid = fork();

    if (pid < 0) {
        return;
    }

    if (pid == 0) {
        int sec = (tl + 999) / 1000;
        struct rlimit rlim;
        rlim.rlim_cur = sec;
        rlim.rlim_max = RLIM_INFINITY;
        setrlimit(RLIMIT_CPU, &rlim);

        rlim.rlim_cur = (long)ml * 1024 * 1024 * 2;
        rlim.rlim_max = (long)ml * 1024 * 1024 * 2;
        setrlimit(RLIMIT_AS, &rlim);

        execvp(argv[0], argv);
        exit(124);
    }

    signal(SIGALRM, onalarm);
    alarm((rl + 999) / 1000);

    int st;
    struct rusage ru;

    wait4(pid, &st, 0, &ru);

    res->time =  ru.ru_utime.tv_sec * 1000 + ru.ru_utime.tv_usec / 1000;
    res->time += ru.ru_stime.tv_sec * 1000 + ru.ru_stime.tv_usec / 1000;
    res->memory = ru.ru_maxrss / 1024;

    if (res->verdict == -1) {
        if (WIFEXITED(st)) {
            res->exitcode = WEXITSTATUS(st);
        } else if (WIFSIGNALED(st)) {
            int sig = WTERMSIG(st);
            if (sig == SIGXCPU) {
                res->verdict = TL;
            }
            res->exitcode = -sig;
        }
    }

    if (res->verdict == -1) {
        if (res->time >= tl) {
            res->verdict = TL;
        } else if (res->memory >= ml) {
            res->verdict = ML;
        }
    }

    if (res->verdict == -1) {
        res->verdict = OK;
    }
}

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
