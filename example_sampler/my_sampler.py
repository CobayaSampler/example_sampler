"""
Example sampler class or wrapper.
"""

import os

from cobaya.sampler import Sampler
from cobaya.collection import SampleCollection
from cobaya.tools import NumberWithUnits


class MySampler(Sampler):
    """
    Example class for implementing a sampler or interfacing an external one.

    It needs to implement three methods:

    - ``initialise(self)``: initialization and configuration (``__init__.py`` is
      handled by ``cobaya.sampler.Sampler`` and should not be overriden).

    - ``run(self)``: runs the sampling process and writes the output.

    - ``products(self, optional_args)``: returns the results of the sampler; it can
      implement custom arguments.

    See the source code of this class for example snippets.
    """

    # Here you can specify the sampler options and their default values
    # (you can also use an external .yaml file)
    option = 1
    option_scale = "10d"


    def initialize(self):
        """Initializes and configures the sampler."""

        # # If this is a wrapper for an external sampler, import it here:
        # try:
        #     import external_sampler
        # except ModuleNotFoundError:
        #     raise # ...

        # Define some useful variables for the sampler about the parameterization
        # (see the docs for the Parameterization class)
        self.sampled_parameter_names = list(self.model.parameterization.sampled_params())
        self.n_sampled_params = self.model.prior.d()

        # Get priors/bounds
        self.bounds = self.model.prior.bounds(
            confidence_for_unbounded=0.9999995  # 5-sigma
        )

        self.log.info("Sampling the following parameters:")
        for i, p in enumerate(self.sampled_parameter_names):
            self.log.info(f" - {p} within bounds {self.bounds[i]}")

        # Automatically scale options with dimensionality, e.g. "5d" = 5 * dimensionality
        self.option_scale = NumberWithUnits(
            self.option_scale, "d", scale=self.n_sampled_params, dtype=int
        ).value

        self.log.info(f"Called with options {self.option=}, {self.option_scale=}")

        # Prepare table to store samples
        # ("name" can be different for different sets or MPI processes)
        self.samples = SampleCollection(self.model, self.output, name="1")

        # Prepare additional output, if any.
        # NB: standard output folders and files will always be created if saving samples
        #     as cobaya.collection.SampleCollection, as shown in the `run` method.
        if self.output:
            # Prepare an additional file in the default output folder,
            # called "root_addtional.xyz"
            self.additional_filename = self.output.add_suffix("additional", separator="_")
            self.additional_filename += ".xyz"
            # Prepare an extra folder on top of the default output one.
            # NB: self.output.create_folder(name) is MPI-aware, meaning the folder will
            #     only be created once when running with MPI.
            self.additional_folder = os.path.join(
                self.output.folder, self.output.prefix + "_" + "additional_folder"
            )
            self.output.create_folder(self.additional_folder)

            self.log.info(
                f"Additional data will be written into file {self.additional_filename} "
                f"or folder {self.additional_folder}"
            )

        # Exploiting the speed hierarchy [Optional but ecouraged!]
        self.model.measure_and_set_speeds()
        self.blocks, self.oversampling_factors = \
            self.model.get_param_blocking_for_sampler(oversample_power=0.4)
        self.blocks_indices = []
        self.log.info("Parameter blocks and their oversampling factors:")
        for f, b in zip(self.oversampling_factors, self.blocks):
            self.mpi_info(f" - {f} : {b}")
            self.blocks_indices.append([self.sampled_parameter_names.index(p) for p in b])

        self.log.info("Initialization complete!")

    def run(self):
        """Runs the sampling process. It must ensure the output is written at the end."""

        self.log.info("Starting sampler run...")

        # Draw a random sample from the prior
        prior_sample = self.model.prior.sample(ignore_external=True)[0]
        self.log.info(
            "Random sample drawn from prior: "
            f"{dict(zip(self.sampled_parameter_names, prior_sample))}"
        )

        # Evaluate the posterior for that sample
        post = self.model.logposterior(prior_sample)
        self.log.info(f"Full log-posterior result: {post}")
        # To get just the logposterior: post.logpost

        # [Optional: exploiting parameter hierarchy]
        # Change the fastest parameters and re-evaluate.
        # If there is a parameter hierarchy, this second logpost evaluation is faster:
        # only the last segment of the pipeline is recalculated.
        new_prior_sample = self.model.prior.sample(ignore_external=True)[0]
        prior_sample[self.blocks_indices[-1]] = new_prior_sample[self.blocks_indices[-1]]
        self.log.info(
            "Updated random sample drawn from prior: "
            f"{dict(zip(self.sampled_parameter_names, prior_sample))}"
        )
        post = self.model.logposterior(prior_sample)
        self.log.info(f"New log-posterior result: {post}")

        # Save a sample in the collection
        self.samples.add(
            prior_sample,
            derived=post.derived,
            weight=1,
            logpriors=post.logpriors,
            loglikes=post.loglikes,
        )
        # Ensure that the collection is fully written, if an output file is defined
        self.samples.out_update()

        self.log.info(f"Finished sampling. Sample stored in {self.samples.file_name}")

    def products(self):
        """Returns the results of the sampling process."""
        return {"sample": self.samples}
