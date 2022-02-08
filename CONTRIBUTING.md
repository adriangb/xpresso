# Contributing to Xpresso

Xpresso is a pure python package that you should be able to get up in running in < 5 minutes.

## Clone the repo

First, clone the repository:

```shell
git clone https://github.com/adriangb/xpresso.git
```

Then change directories into the repository you just cloned:

```shell
cd xpresso
```

## Set up the project

### Automated setup

If you have [Make] installed, you can just run:

```shell
make init && make test && make lint
```

Which will set up a virtual enviromnet (using [Poetry]), install all of the project's dependencies, install git hooks and run all of the tests.

### Manual setup

Alternatively, you can set up the project manually like any other Poetry project:

```shell
pip install -U poetry
poetry install
```

Then to run tests:

```shell
poetry run python -m pytest -v
```

To install git hooks (managed by [pre-commit]):

```shell
pip install -U pre-commit
pre-commit install
```

And to run linters:

```shell
pre-commit run --all-files
```

## Making changes

First you will need to fork the repository on GitHub.
Once you have your own fork, clone it and follow the instructions above to set up the project.
You will make changes in your fork and then open a pull request (PR) against [https://github.com/adriangb/xpresso](https://github.com/adriangb/xpresso).

All changes are expected to come with tests.
If the change impacts user facing behavior, it should also have documentation associated with it.
Once you've made your changes and have passing tests, you can submit a PR.
Every pull request merge will trigger a release, so you need to include a version bump (by editing the version in `pyproject.toml`).
We adhere to [Semantic Versioning].
Use your best judgment as to what sort of version bump your changes warrant and it will be discussed as part of the PR review process.

Pull requests are squash merged, so you do not need to keep a tidy commit history, although it is appreciated if you still do keep your work in progress commit messages clear and consice to aid in the review process.
You are encouraged, but not required, to use [Conventional Commits].

[Make]: https://www.gnu.org/software/make/
[Poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com
[Semantic Versioning]: https://semver.org
[Conventional Commits]: https://www.conventionalcommits.org/en/v1.0.0/
