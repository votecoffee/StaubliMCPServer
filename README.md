# StaubliMCPServer

Standalone Windows workbench for Stäubli Robotics Suite (SRS): a desktop GUI,
headless JSON CLI and reusable chat skill. The repository name reserves a future
integration; this version contains no MCP server or background listener.

## Contents

- [Install](#install)
- [Usage](#usage)
- [Architecture](#architecture)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)

## Install

Python 3.11+ is required. SRS and its license are separately installed vendor software.
Offline operations do not require SRS. From this checkout:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[gui,dev]"
```

Omit `gui` for a headless installation. No vendor binaries are distributed.

## Usage

```powershell
.venv\Scripts\staubli catalog
.venv\Scripts\staubli run srs.discover
.venv\Scripts\staubli-gui
```

The CLI returns one JSON envelope per invocation. See [the command guide](docs/CLI.md)
for saved-project inspection, VAL3 analysis, comparison and simulator reads.
Use [the skill](skills/staubli-workbench/SKILL.md) for chat workflows.

## Architecture

Python services and an operation registry are shared by a one-shot CLI and optional
PySide6 GUI, following the service/desktop separation used by
[FanucMCPServer](https://github.com/votecoffee/FanucMCPServer).
Core calls do not import Qt or initialize SRS. See [capabilities and planned adapters](docs/ARCHITECTURE.md).

This phase does not deploy programs, move robots or write controller settings.
File analysis establishes saved-source evidence, not SRS compilation or runtime acceptance.

## Maintainers

[@votecoffee](https://github.com/votecoffee)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run tests locally; use synthetic projects
and keep private robot data out of commits.

## License

[MIT](LICENSE), copyright 2026 votecoffee. Stäubli and SRS are vendor trademarks;
this independent project is not affiliated with Stäubli.
