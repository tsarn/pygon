Standard checkers and validators
================================

Following standard checkers are available:

- ``standard.fcmp`` compare files as sequences of lines (ignoring line endings).
- ``standard.lcmp`` compare files as sequences of tokens in lines (ignoring wrong spaces placing).
  This is the default checker.
- ``standard.wcmp`` compare files as sequences of tokens (ignoring wrong spaces/newlines placing).
- ``standard.hcmp`` compare two signed huge integers.
- ``standard.ncmp`` compare sequences of ints
- ``standard.yesno`` yes or no, case insensitive

Following standard validators are available:

- ``standard.wfval`` is equivalent to tests well-formed option in Polygon.
  It checks that:

  - File is not empty 
  - Each line ends with ``\n``
  - No leading or trailing spaces 
  - No two consecutive spaces 
  - Only allow ``\n`` and characters with codes ``32..127``
  - No leading or trailing empty lines

