# Pygon

Pygon is a console application designed to make it easier to prepare
programming contests. It addresses some gripes I (and many others apparently) have with
[Polygon](https://polygon.codeforces.com). Note, that Pygon isn't related to Polygon in any way.

## Requirements

Python 3.5+ is required, as well as C compiler for building
solution runner utility (if you're on Windows, binary is already bundled with
pygon and you don't need to worry about it) and a C++ compiler for building standard checkers
and validators.

## Comparison with Polygon

What I personally like about Pygon more:

 - It's offline and always available.
   It's very annoying when Polygon's TLS certificate expires, or it is down,
   or I'm in a remote area with a summer computer school and suddenly there's
   no internet connection because cellphone tower is not working for some reason.
   Stuff like this happens far more often than you'd think and it's never pleasant.
 - It doesn't impose a version control system on you.
   Sometimes I just want to use git, you know? It's easier to share,
   easier to reason about and supports so much more features than Polygon's VCS.
 - It has a single source of truth for everything. Remember Polygon generator scripts?
 - You don't have to wait for ages for the package to be built (yes, even with verification!)
 - All the files are stored locally and human-readable.
   So convenient! Especially for people who mainly use terminal apps.
   No need to copy and paste code into your browser.
 - Supports `examplethree` and `examplewide` out of the box.
 - It's pretty. Colors in the terminal are just so freaking cool.
 - It's open source.

What I personally like about Polygon more

 - It has a nice integration with a lot of online judges.
   Ideally, I'd like Pygon to eventually have a Polygon-compatible web server for exporting problems
   to, say, ejudge.
 - It has so many cool warnings. From duplicate tests to typography errors and undefined
   behavior in C++ generators.
 - Currently it has more features, for example test groups.
   Hopefully not for long :)
