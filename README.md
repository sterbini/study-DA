# Dynamics Aperture Study Package

This package consists of a collection of tools to study the dynamics aperture of a particle accelerator with [Xsuite](https://github.com/xsuite/xsuite). In a sense, it is a replacement of the [DA study template](https://github.com/xsuite/DA_study_template), but much more advanced. It also allows to configure colliders and do tracking without necessarily running parametric scans.

 The package is divided into four main parts:

- **Study Generation**: Provides functions to generate, from template scripts and a configuration file, the dynamics aperture study as a multi-generational tree representing the various layers of the corresponding parametric scan. Alternatively, one can generate a single job from configuring a collider and running some tracking (or any other type of job), without doing a scan.
- **Study Submission**: Allows seamless submission of the generated study locally and/or to computing clusters (mainly HTCondor), and the automatic retrieval of the results.
- **Study Postprocessing**: Provides functions to postprocess the raw results (usually `.parquet` files from tracking) and aggregate them into a Pandas `DataFrame`.
- **Study Plotting**: Provides functions to visualize the postprocessed results as 2D and 3D heatmaps.

The whole project is described in details in the [full documentation](https://colasdroin.github.io/study-DA/), along with tutorials and description of the implemented functions.

Note that this package is still under development. Consequently, this README might evolve in the near future.

## Installation

### Simple usage

The package is available on PyPI and can be installed using `pip`.

```bash
pip install study-da
```

## Usage

Please refer to the [full documentation](https://colasdroin.github.io/study-DA/).

## Contributing

We welcome contributions to the Dynamics Aperture Study Package. If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

1. Fork the repository
2. Create a new branch (`git checkout -b feature/yourfeature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add your feature'`)
5. Push to the branch (`git push origin feature/yourfeature`)
6. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
