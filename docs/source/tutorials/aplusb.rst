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
