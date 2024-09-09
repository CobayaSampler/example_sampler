Example externally-defined sampler for Cobaya
=============================================

Check the definition of the sampler class in the ``my_sampler.py`` file. There you can find code snippets for different ways to interact with Cobaya models and output drivers.

If this code is installed as a Python package with ``pip``, it can be used in a Cobaya input file or dictionary as:

    sampler:
      example_sampler.MySampler:
        # ...

To test it, run ``cobaya-run`` with the input files in the ``examples/`` folder.
