# Contributing

Thanks for helping to make graphql-server awesome!

We welcome all kinds of contributions:

- Bug fixes
- Documentation improvements
- New features
- Refactoring & tidying


## Getting started

If you have a specific contribution in mind, be sure to check the [issues](https://github.com/graphql-python/graphql-server/issues) and [pull requests](https://github.com/graphql-python/graphql-server/pulls) in progress - someone could already be working on something similar and you can help out.


## Project setup

### Development with virtualenv (recommended)

After cloning this repo, create a virtualenv:

```console
virtualenv graphql-server-dev
```

Activate the virtualenv and install dependencies by running:

```console
python pip install -e ".[test]"
```

If you are using Linux or MacOS, you can make use of Makefile command `make dev-setup`, which is a shortcut for the above python command.

### Development on Conda

You must create a new env (e.g. `graphql-sc-dev`) with the following command:

```sh
conda create -n graphql-sc-dev python=3.8
```

Then activate the environment with `conda activate graphql-sc-dev`.

Proceed to install all dependencies by running:

```console
pip install -e ".[dev]"
```

And you ready to start development!

## Running tests

After developing, the full test suite can be evaluated by running:

```sh
pytest tests --cov=graphql-server -vv
```

If you are using Linux or MacOS, you can make use of Makefile command `make tests`, which is a shortcut for the above python command.

You can also test on several python environments by using tox.

### Running tox on virtualenv

Install tox:

```console
pip install tox
```

Run `tox` on your virtualenv (do not forget to activate it!) and that's it!

### Running tox on Conda

In order to run `tox` command on conda, install
[tox-conda](https://github.com/tox-dev/tox-conda):

```sh
conda install -c conda-forge tox-conda
```

This install tox underneath so no need to install it before.

Then uncomment the `requires = tox-conda` line on `tox.ini` file.

Run `tox` and you will see all the environments being created and all passing tests. :rocket:
