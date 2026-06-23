# Releasing Project Rosetta

Project Rosetta is published to PyPI from a published GitHub Release. The
workflow uses PyPI Trusted Publishing, so no long-lived API token is stored in
GitHub.

## Workflows

| Workflow | Trigger | Role |
| --- | --- | --- |
| `package.yml` | Pull requests and pushes to `main` | Builds the wheel/sdist from source, smoke-tests the local install, and uploads build artifacts. This is the pre-release validation workflow. |
| `publish.yml` | Published GitHub Release | Builds from the release tag and publishes to PyPI. Uses a concurrency group keyed on the release tag so duplicate triggers for the same tag do not publish in parallel. |
| `quality.yml` | Pull requests and pushes to `main` | Runs linting and tests on the checked-out source tree. |

No CI workflow installs the package from PyPI. The `package.yml` workflow
validates the distributable by building and installing the wheel produced from
the repository checkout. After a release, verify the published package manually
with `python -m pip install projectrosetta==X.Y.Z`.

## One-Time PyPI Setup

Before the first release, create a pending trusted publisher on PyPI with:

- PyPI project name: `project-rosetta`
- GitHub owner: `volvo-cars`
- GitHub repository: `projectrosetta`
- Workflow filename: `publish.yml`
- Environment name: `pypi`

Create a protected GitHub environment named `pypi`. Add required reviewers if
publication should require explicit approval.

## Release Steps

1. Update `[project].version` in `pyproject.toml`.
2. Merge the version change and confirm the Quality and Package workflows pass.
3. Create and publish a GitHub Release with tag `vX.Y.Z`.
4. Confirm the Publish to PyPI workflow completes.
5. Verify the release with `python -m pip install projectrosetta==X.Y.Z`.

The publication workflow rejects a release when its tag does not exactly match
the package version.
