Example externally-defined sampler for Cobaya
=============================================

This package contains the bare minimum necessary to implement a [Cobaya sampler](https://cobaya.readthedocs.io/en/latest/sampler.html), or a Cobaya wrapper for an independent sampler. Such a package can contain any code at all, as long is it implements a class inheriting from `cobaya.sampler.Sampler` (or a derivative of it) and makes it importable from the root of the package.

As an example, check out the definition of the single class defined in ``my_sampler.py``. There you can find code snippets for different ways to interact with Cobaya models and output drivers.

If this code is installed as a Python package with ``pip``, it can be used in a Cobaya input file or dictionary as:

    sampler:
      example_sampler.MySampler:
        # ...

To test it, run ``cobaya-run`` with the input files in the ``examples/`` folder.
