# Pygon

Pygon is a console application designed to make it easier to prepare
programming contests. It addresses some gripes I (and many others apparently) have with
[Polygon](https://polygon.codeforces.com). Note, that Pygon isn't related to Polygon in any way.

## Requirements

Python 3.5+ is required. Currently running solutions depends on GNU time-compatible command.
So, probably only Linux is supported right now. But don't worry! I'm working on it.
Anyway, you wouldn't even have to think about dependencies if I get around to packaging this whole
thing properly. There's hope.

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
 - It's pretty. Colors in the terminal are just so freaking sexy.
 - It's open source.
 - More features coming (I've been working on only for three days when I wrote this README, give me a break)

What I personally like about Polygon more

 - It has a nice integration with a lot of online judges.
   Ideally, I'd like Pygon to eventually have a Polygon-compatible web server for exporting problems
   to, say, ejudge.
 - It has so many cool warnings. From duplicate tests to typography errors and undefined
   behavior in C++ generators.
 - Currently it has a lot more features, like test groups, interactive problems and contests.
   Hopefully not for long :)
