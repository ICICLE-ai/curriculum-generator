# Contributing to Smart Curriculum Designer

Thank you for helping improve Smart Curriculum Designer. Contributions may include bug reports, documentation improvements, new curriculum templates, dataset scanners, model evaluation stages, workflow or configuration artifacts, and code changes.

## Before Contributing

1. Read the [README.md](README.md), [HOW_TO_USE.md](documentation/HOW_TO_USE.md), and [YAML_CONFIG_GUIDE.md](documentation/YAML_CONFIG_GUIDE.md).
2. Review open issues and pull requests to avoid duplicate work.
3. **Do not submit credentials, private keys, proprietary data, restricted data, sensitive locations, personally identifiable information, or material that you are not authorized to share.**
4. Use the issue templates to report a problem or propose a change before beginning a substantial contribution.

## Contribution Pathways

The project welcomes contributions in increasing order of technical and maintenance responsibility:

1. **Execute an example**: Run a sample pipeline configuration (e.g. `configs/skin_cancer_config.yaml` or `configs/food_config.yaml`) and report any problems.
2. **Improve documentation or tutorials**: Refine user guides, YAML parameter descriptions, or educational explanations.
3. **Add or improve automated tests**: Expand test coverage for dataset scanners, Jinja2 template renderers, or metric extractors.
4. **Propose curriculum templates & datasets**: Author new Jinja2 template modules (`digitalagedu/templates/`) or domain dataset adapters.
5. **Prepare a bounded code contribution**: Submit modular enhancements to the orchestrator, vision stages, or practice generators.

## Pull Requests

A pull request should:

- Reference the related issue or explain the user/maintainer problem being addressed.
- Be limited to one coherent, self-contained change.
- Include or update unit tests when practical (`pytest`).
- Update documentation when user-visible behavior, interfaces, configuration parameters, installation steps, or limitations change.
- Identify dependencies, data assumptions, security implications, and maintenance implications.
- Not include secrets, unreviewed large binary weights, private datasets, or unlicensed materials.

Maintainers may request changes, defer a contribution, or decline it when the change lacks a clear maintenance owner, conflicts with project scope, introduces unacceptable security or data risks, or cannot be reviewed with available resources.

## License and Contributor Rights

By submitting a contribution, you represent that you have the right to submit it and that it may be distributed under this repository's MIT license. If your employer, institution, funder, or data provider imposes restrictions, obtain authorization before contributing.

## Security Issues

Do not report suspected vulnerabilities in a public issue. Follow [SECURITY.md](SECURITY.md).
