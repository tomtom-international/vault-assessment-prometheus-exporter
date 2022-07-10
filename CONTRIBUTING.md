# Contributing

Contributions are welcome.
Contributors are required to agree to the [Developer Certificate of Origin](https://developercertificate.org/).

## Development

### Basic Setup

The Python package is managed with Poetry, for a detailed introductions please see their [introduction document](https://python-poetry.org/docs/).

Some common commands are as follows:

* `poetry install` - to install the project and its dependencies
* `poetry shell` - to get a shell with the poetry-managed virtual environment pre-loaded
* `poetry run <command>` - to run the command within the poetry-managed virtual environment.
* `poetry update` - to update the dependencies, be sure to commit `poetry.lock` if you are trying to update dependencies

### Versioning

Every PR submitted must increase the version via `bump2version`.

* For small changes (e.g. fixes), this should be done with `bump2version patch`
* For minor changes (e.g. extending an existing feature), this should be done with `bump2version minor`
* For major changes (e.g. changing how the configuration file works, adding a new exporter module), this should be done with `bump2version major`. Please open a ticket or contact the maintainers before starting work on a change you think may be major.

### Automated Linting and Scanning Tools

All tools used here will enforce their checks in pull requests, blocking the pull request from being merged until completed.

#### Python Checks

To help protect the health of this project, all contributions are required to pass certain healthchecks, comprised of the following:

* [pylint](https://www.pylint.org/) - using `pyproject.toml` for its configuration
* [black](https://black.readthedocs.io/en/stable/) - also using `pyproject.toml` for configuration, automatically applies formatting when run
* [mypy](http://mypy-lang.org/) - also using `pyproject.toml` for its configuration, mypy enforces static typing
* [bandit](https://bandit.readthedocs.io/en/latest/) - to scan for common Python vulnerabilities
* [pytest](https://docs.pytest.org/en/7.1.x/) - to execute automated tests, also configured in `pyproject.toml`

#### Docker Checks

* the docker image is test-built in amd64, arm64 and arm/v7 architectures for every PR
* [hadolint](https://github.com/hadolint/hadolint) - scans the Dockerfile for common mistakes
* [trivy](https://github.com/aquasecurity/trivy) - trivy is executed on every PR against a freshly-built image to check for vulnerabilities


#### Other Checks

* [gitleaks](https://github.com/zricethezav/gitleaks) - scans the repository for possible secrets (e.g. passwords, keys), this is only the last line of defense, you should double-check before you commit!
* [bump2version](https://github.com/c4urself/bump2version) - we ensure that the version has been bumped by bump2version on every pull request

#### Automatic PR Builds

The [Docker Checks](#docker-checks) job can be configured to push a PR build image (tagged pr-#) to your repository.
It does not work when running from a forked repository.
This image will be cleaned up after the PR is closed.
Using this functionality requires the following secrets to be added:

* `BULD_PR` must be set to `true`
* `PR_CONTAINERS_USER` must be set to the user associated with the `PR_CONTAINERS` token
* `PR_CONTAINERS` must be set to a Github PAT with `read`, `write` and `delete` packages permissions

A PAT must be used rather than the built-in token, as Github Actions does not currently support setting the `delete` permission for packages on the default token.

If you wish to enable the functionality in an organization, you must also provide the organization name in a secret called `ORG`.
