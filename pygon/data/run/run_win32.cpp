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

#define UNICODE
#define _UNICODE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <shellapi.h>
#include <psapi.h>
#include <wchar.h>
#include <strsafe.h>

#define CMD_MAX 65536

#define OK 0
#define TL 1
#define ML 2
#define RL 3

struct result_t {
    int verdict;
    int exitcode;
    int time;
    int memory;
};

static char *verdicts[] = {
    "ERR",
    "OK",
    "TL",
    "ML",
    "RL"
};

long long FileTimeToLongLong(const FILETIME *ft)
{
    return ft->dwLowDateTime + ((long long)ft->dwHighDateTime << 32);
}

void run(int argc, wchar_t **argv, int tl, int ml, int rl, result_t *res)
{
    res->verdict = -1;
    res->exitcode = 0;
    res->time = 0;
    res->memory = 0;

    wchar_t cmd[CMD_MAX];
    cmd[0] = 0;

    for (int i = 0; i < argc; ++i) {
        wcscat(cmd, L"\"");
        wcscat(cmd, argv[i]);
        wcscat(cmd, L"\" ");
    }

    PROCESS_INFORMATION pi;
    STARTUPINFOW si;

    ZeroMemory(&pi, sizeof(pi));
    ZeroMemory(&si, sizeof(si));

    if (!CreateProcessW(argv[0], cmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        fprintf(stderr, "CreateProcessW FAILED\n");
        return;
    }

    if (WaitForSingleObject(pi.hProcess, rl) == WAIT_TIMEOUT) {
        res->verdict = RL;
        TerminateProcess(pi.hProcess, 0);
    }

    PROCESS_MEMORY_COUNTERS mc;

    if (GetProcessMemoryInfo(pi.hProcess, &mc, sizeof(mc))) {
        res->memory = mc.PeakWorkingSetSize / 1024 / 1024;
    } else {
        fprintf(stderr, "GetProcessMemoryInfo FAILED\n");
    }

    FILETIME utime, stime, dummy1, dummy2;

    if (GetProcessTimes(pi.hProcess, &dummy1, &dummy2, &stime, &utime)) {
        res->time = FileTimeToLongLong(&stime) / 10000 + FileTimeToLongLong(&utime) / 10000;
    } else {
        fprintf(stderr, "GetProcessTimes FAILED\n");
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

    DWORD exitcode;
    GetExitCodeProcess(pi.hProcess, &exitcode);

    res->exitcode = (int)exitcode;

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
}

int main()
{
    // Usage: run <tl> <ml> <rl> <log> <args>

    int argc;
    wchar_t **argv = CommandLineToArgvW(GetCommandLineW(), &argc);

    if (argc <= 5) {
        fprintf(stderr, "not enough arguments\n");
        return 1;
    }
    result_t res;

    int tl = _wtoi(argv[1]);
    int ml = _wtoi(argv[2]);
    int rl = _wtoi(argv[3]);

    run(argc - 5, argv + 5, tl, ml, rl, &res);

    FILE *f = _wfopen(argv[4], L"w");
    fprintf(f, "verdict: %s\n", verdicts[res.verdict + 1]);
    fprintf(f, "exitcode: %d\n", res.exitcode);
    fprintf(f, "time: %d\n", res.time);
    fprintf(f, "memory: %d\n", res.memory);
    fclose(f);

    return 0;
}
