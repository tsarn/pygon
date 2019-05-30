/*
Validates that the input matches following criteria:
 
- File is not empty 
- Each line ends with '\n' 
- No leading or trailing spaces 
- No two consecutive spaces 
- Only allow '\n' and characters with codes 32..127 
- No leading or trailing empty lines
*/

#include "testlib.h"

using namespace std;

int main(int argc, char* argv[])
{
    registerValidation(argc, argv);

    if (inf.eof()) {
        quit(_fail, "empty input");
    }

    bool metLine = false;
    bool lineEmpty = true;

    while (!inf.eof()) {
        bool spaceAllowed = false;
        bool endOfLine;
        lineEmpty = true;
        while (!(endOfLine = inf.eoln()) && !inf.eof()) {
            char c = inf.readChar();
            lineEmpty = false;
            if ((c == ' ' && spaceAllowed) || (c >= 33 && c <= 127)) {
                spaceAllowed = (c != ' ');
            } else {
                if (c == ' ') {
                    quit(_fail, "illegal space");
                } else {
                    quitf(_fail, "illegal character with code %d", (int)c);
                }
            }
        }
        if (!spaceAllowed && !lineEmpty) {
            quit(_fail, "illegal trailing space");
        }
        if (lineEmpty && !metLine) {
            quit(_fail, "illegal leading empty line");
        }
        metLine = true;
        if (inf.eof() && !endOfLine) {
            quit(_fail, "last line doesn't end with eoln");
        }
    }

    if (lineEmpty) {
        quit(_fail, "illegal trailing empty line");
    }

    inf.readEof();

    return 0;
}
