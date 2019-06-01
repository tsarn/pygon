Creating a simple problem
=========================

This tutorial explains how to create a simple problem.
I will use the classic ``A+B`` as an example. Let's begin.

Our problem will be named ``aplusb``. This is internal name (identifier),
name used in statements will be different. The name should be in lowercase
English letters, numbers or dashes. Let's create the problem:

::

    $ pygon init aplusb
    $ cd aplusb

Our problem will be very simple: given two numbers, find their sum.
For example, for input ``2 3`` output ``5``.
Let's write the correct solution. Save the following in ``solutions/solve.cpp``:

.. code:: c++

   #include <iostream>
   int main() {
       int a, b;
       std::cin >> a >> b;
       std::cout << a + b << std::endl;
       return 0;
   }

Now we will need to let Pygon know about this solution by creating a descriptor file.
Descriptor file has a ``.yaml`` extension, since it's just YAML file.
For example, descriptor for our solution will be located at ``solutions/solve.yaml``.
Run the following command to automatically generate descriptors:

::

    $ pygon discover

Great! Now we need to mark this solution as the main one. This means, it will be used
to generate answers to the tests. Please note, that there can only be one main solution.
Edit ``solutions/solve.yaml`` and set ``tag`` to ``main``, instead of just ``correct``.

Now, add a statement by running the following command:

::

    $ pygon addstatement

Edit your statement at ``statements/LANGUAGE/problem.tex``.
Write something interesting and then continue on with this tutorial.

Now add a generator. This is left as an exercise (basically copy-paste some example
from https://github.com/MikeMirzayanov/testlib and tweak it a little). Then, ``discover`` it as usual.

You can add a custom checker if you want, but in this problem this is not necessary.
To change the problem's checker edit ``active_checker`` property in ``problem.yaml``.
There's also a number of standard checkers available, which compare participant's output to
main solution's output. See :doc:`/standard` for a full list of standard checkers and validators.

Now we need to add the tests. Tests are located in ``tests/`` directory
and are numbered starting from 1. They must have names ``01``, ``02``, ...
``10``, ``11``, ..., ``99``, ``100``, ``101`` and so on. Basically, a result of
calling ``printf("%02d", index)``. Create your first test in ``tests/01``, and put
something like ``2 3`` there. Note that if you haven't removed ``standard.wfval`` from
``active_validators`` field in ``problem.yaml`` (and for most problems you shouldn't),
your test must be correctly formatted. Refer to :doc:`/standard` for more info.

Let's add 10 generated tests. Note, that generators generate the same test for the same
command line arguments, so we need to create 10 tests, with generator commands ``gen 1``,
``gen 2`` and so on. The easiest way to do that is to use the ``pygon edittests`` command.
It allows you to easily add, remove and reorder tests. Run it and an you will be presented
with an editor. Suppose your generator is called ``gen`` (comes from a source file named
``gen.cpp`` for example), then add the following line at the end of the file: ``G gen [1..10]``,
then save the file and exit the editor. This does exactly what we need.
