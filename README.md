# Project Rosetta

An open-source initiative for bridging simulation and test-track execution in ADAS verification and validation.

Project Rosetta provides tooling and workflows to make scenario generation, reconstruction, and correlation **comparable, measurable, and reproducible** across toolchains and organizations.

## The Problem

In ADAS development, both simulation and test-track execution are critical for V&V, certification, and rating. However, proving that the same scenario behaves consistently across these two environments is challenging—especially when data comes from different formats, tools, and measurement systems.

Project Rosetta solves this by standardizing workflows around open formats and explicit correlation metrics.

## Core Capabilities

1. **Scenario to Test Track**

   - Convert ASAM OpenSCENARIO and OpenDRIVE definitions into robot-executable
     test-track instructions

2. **Test Track Ground Truth to Scenario**

   - Reconstruct comparable OpenSCENARIO and OpenDRIVE files from measured
     test-track ground-truth data

3. **Scenario Correlation**

   - Compute scenario-level metrics to quantify correlation between simulated
     and measured trajectories

## Use Cases

- **Rating & Certification**: Establish traceability between simulation evidence and track evidence for official rating bodies
- **V&V Automation**: Reduce manual effort in scenario correlation analysis through automated metric computation
- **Tool Interoperability**: Use open standards to reduce dependency on proprietary tool ecosystems
- **Research & Collaboration**: Enable joint development across OEMs, partners, and the broader community

## Who This Is For

- ADAS simulation and V&V engineers
- Test-track automation and robotics engineers
- Toolchain and data pipeline architects
- Researchers and integration partners

## Quick Links

- **[Documentation](docs/)** — Start here for guides, architecture, and references
- **[Getting Started](docs/getting-started/)** — Onboarding and setup
- **[FAQ](docs/faq/faq.md)** — Common questions and clarifications
- **[Contributing Guide](CONTRIBUTING.md)** — How to contribute (including CCB governance for `main`)

## Contributor Quick Start

Before opening a pull request, run local quality checks as described in the [Local Quality Checks](CONTRIBUTING.md#local-quality-checks) section.

This ensures your contribution is aligned with repository linting and formatting standards before CI runs.

## Development Setup

Set up the repository with Poetry:

- `poetry install --with dev`

Run the example Poetry entry-point command:

- `poetry run rosetta-hello`

Install pre-commit hooks (one-time):

- `poetry run pre-commit install`

Run all checks locally:

- `poetry run pre-commit run --all-files`

## Guiding Principles

- **Open Standards First**: Prioritize ASAM OpenSCENARIO and OpenDRIVE interoperability
- **Reproducibility**: Ensure deterministic, reviewable transformations
- **Measurability**: Define explicit, scenario-level correlation metrics
- **Collaboration**: Enable contributions from OEMs, tool vendors, research organizations, and the community

## Project Status

Early active development. Architecture and core interfaces are under active design and refinement.

## Support

For questions, bug reports, feature requests, or general support, please **open an issue** on the [GitHub issue tracker](https://github.com/volvo-cars/projectrosetta/issues).

When opening an issue, provide:

- A clear title and description
- Steps to reproduce (for bugs)
- Expected vs. actual behavior
- Environment details (OS, tool versions, etc.) when relevant

Issues enable transparent discussion and help the team prioritize work based on community needs.

## License

This project is licensed under **Mozilla Public License 2.0**.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](./.github/CODE_OF_CONDUCT.md). By participating, you are expected to uphold it. Please report unacceptable behavior to [opensource@volvocars.com](mailto:opensource@volvocars.com).
