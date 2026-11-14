# Contributing

Install `.[gui,dev]` in a virtual environment and run `python -m pytest`.
Add meaningful failure-path checks for filesystem boundaries, parsing and network
adapters. Use generated fixtures, never proprietary projects or binaries.

Keep operations in services with explicit input/output contracts in the registry.
Return structured errors; stdout is reserved for CLI JSON. Keep heavy imports lazy.
Update README and docs when capabilities change. Native SRS verification must be
reported separately from offline tests and simulator observations.
