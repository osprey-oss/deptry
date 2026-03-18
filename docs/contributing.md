# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

You can contribute in many ways.

## Types of contributions

### Reporting bugs

Report bugs at https://github.com/osprey-oss/deptry/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fixing bugs

Look through the GitHub issues for bugs. Anything tagged with `bug` and `help wanted` is open to whoever wants to implement a fix for it.

### Implementing features

Look through the GitHub issues for features. Anything tagged with `enhancement` and `help wanted` is open to whoever wants to implement it.

### Writing documentation

_deptry_ could always use more documentation, whether as part of the official documentation, in docstrings, or even on the web in blog posts, articles, and such.

### Submitting feedback

The best way to send feedback is to file an issue at https://github.com/osprey-oss/deptry/issues.

If you are proposing a new feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions are welcome :)

## Get started!

Ready to contribute? Here's how to set up _deptry_ for local development. Please note this documentation assumes you
already have [uv](https://docs.astral.sh/uv/), [Git](https://git-scm.com/) and [pre-commit](https://pre-commit.com/)
installed and ready to go.

1. [Fork](https://github.com/osprey-oss/deptry/fork) the _deptry_ repository on GitHub.

2. Clone your fork locally:
    ```bash
    cd <directory_in_which_repo_should_be_created>
    git clone git@github.com:YOUR_NAME/deptry.git
    ```

3. Now you need to set up your local environment. Navigate into the directory:
    ```bash
    cd deptry
    ```

    Then, install the virtual environment with:
    ```bash
    uv sync
    ```

4. Install `pre-commit` hooks to run linters/formatters at commit time:
    ```bash
    pre-commit install
    ```

5. Create a branch for local development:
    ```bash
    git checkout -b name-of-your-bugfix-or-feature
    ```

    Now you can make your changes locally.

6. If you are adding a feature or fixing a bug, make sure to add tests in the `tests` directory.

7. Once you're done, validate that all unit and functional tests are passing:
    ```bash
    make test
    ```

8. Before submitting a pull request, you should also run [tox](https://tox.wiki/en/latest/). This will run the tests across all the Python versions that _deptry_ supports:
    ```bash
    tox
    ```

    This requires you to have multiple versions of Python installed.
    This step is also triggered in the CI pipeline, so you could also choose to skip this step locally.

9. Commit your changes and push your branch to GitHub:
    ```bash
    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature
    ```

10. Submit a pull request through GitHub.

## Pull request guidelines

Before you submit a pull request, ensure that it meets the following guidelines:

1. If the pull request adds a functionality or fixes a bug, the pull request should include tests.
2. If the pull request adds a functionality, the documentation in `docs` directory should probably be updated.
