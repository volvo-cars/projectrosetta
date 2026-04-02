# Contributing to Project Rosetta

Thank you for your interest in contributing to Project Rosetta.

This document defines the contribution workflow for this repository and the governance controls that apply to changes targeting the `main` branch.

## Code of Conduct

This project follows the Contributor Covenant [Code of Conduct](.github/CODE_OF_CONDUCT.md). By participating, you agree to follow it.

## Contribution Workflow

All changes must be delivered through pull requests (PRs).

### 1. Open an Issue (Recommended)

Before implementing larger changes, open an issue to describe the problem, expected behavior, and proposed approach.

### 2. Create a Branch

Create a feature or fix branch from the latest `main`.

### 3. Submit a Pull Request

Open a PR to `main` that includes:

- A clear title and concise summary
- Rationale for the change
- Linked issue (when applicable)
- Documentation updates when behavior or usage changes

### 4. Address Review Feedback

Update the PR as needed and resolve all review comments before merge.

## Branch Governance for `main`

The `main` branch is protected and governed by the Change Control Board (CCB).

- Only members of the CCB are authorized to merge PRs into `main`.
- Every PR targeting `main` requires **at least one (1) approval from the CCB** before it can be merged.

These requirements apply to all contributors and are enforced through repository branch protection settings.

## Quality Expectations

Contributors are expected to:

- Keep changes focused and scoped
- Follow existing project structure and conventions
- Ensure documentation remains accurate
- Verify that proposed changes are review-ready

## Pre-commit Hooks

This repository provides a pre-commit configuration to run quality checks
automatically on every commit.

Install pre-commit and set up the hooks once:

- `poetry install --with dev`
- `poetry run pre-commit install`

Note: The `markdownlint` pre-commit hook uses `markdownlint-cli`, which requires
Node.js on your machine (Node.js 12+ for the pinned hook version).

From that point, `ruff` and `markdownlint` will run automatically on every
`git commit`. To run manually across all files:

- `poetry run pre-commit run --all-files`

## Local Quality Checks

The recommended way to run checks locally is via pre-commit:

- `poetry run pre-commit run --all-files` — run all checks
- `poetry run pre-commit run ruff --all-files` — Python lint only
- `poetry run pre-commit run ruff-format --all-files` — Python format only
- `poetry run pre-commit run markdownlint --all-files` — Markdown lint only

These match exactly what CI enforces before merge.

If you prefer to run tools directly without pre-commit:

- `poetry run ruff format --check .`
- `poetry run ruff check .`
- `npx markdownlint-cli "**/*.md" --config .markdownlint.json` (requires Node.js 12+)

## Questions

If you are unsure how to proceed with a contribution, open an issue and request guidance from maintainers.
