# Architecture and capability boundaries

`registry.py` owns versioned operation descriptors, input checks and result envelopes.
`files.py`, `val3.py`, `srs.py` and `simulator.py` implement independent services.
The one-shot CLI and optional Qt GUI call that same dispatcher. Qt is imported only
by the GUI. Neither entrypoint opens an MCP transport, broker or background listener.

The GUI builds ordinary labeled controls from operation descriptors, runs work in
a Qt thread, presents a bounded result tree and full JSON receipt, and saves window,
splitter and input path state with QSettings. It refuses close while its worker is
active rather than abandoning the thread. Network reads are bounded; filesystem
operation completion depends on the selected storage device.

The service/catalog, worker and layout patterns were informed by FanucMCPServer
(`local_cli.py`, `core/workers.py`, `ui/layout_state.py`). This implementation does
not copy its MCP bootstrap or depend on its universal framework package, whose
dependency closure includes MCP. Future adapters can consume the catalog without
changing engineering services. There is currently no native worker to manage.

## Current and planned work

| Layer | Current | Next acceptance boundary |
|---|---|---|
| Saved cell/controller XML | Read-only metadata and references | Native SRS opening/compilation |
| VAL3 | Program/data inventory, lexical calls | Full symbols, library resolution, vendor validation |
| Project comparison | Relative paths and exact byte hashes | Semantic diffs and durable reviewed edits |
| SRS installation | Executable discovery and explicit launch request | Supported, version-qualified automation interface |
| Local CS9 web | Fixed-resource experimental reads | Verified identity, schemas, auth and bounded recordings |
| Physical controller | No transport or writes | Separate explicit controller scope and qualification |
| MCP | No server | Only if requested in a later phase |

Future work is tracked in [reviewed local change packages](https://github.com/votecoffee/StaubliMCPServer/issues/1),
[native SRS automation](https://github.com/votecoffee/StaubliMCPServer/issues/2), and
[qualified CS9 diagnostics](https://github.com/votecoffee/StaubliMCPServer/issues/3).
Resource ownership, exact source preimages, durable job state and ambiguous-outcome
receipts become necessary when those adapters add native jobs or writes.

## Sources

- [Stäubli Robotics Suite](https://www.staubli.com/global/en/robotics/products/robot-software/staeubli-robotics-suite.html): vendor product and licensing context. It is not an API specification.
- [Stäubli SRS brochure](https://www.staubli.com/content/dam/robotics/products/robots/software/srs/Staubli-Robotics-Suite-brochure-EN.pdf): vendor IDE capabilities. Native IDE capabilities are not automatically CLI capabilities.
- [FANUC workbench](https://github.com/votecoffee/FanucMCPServer): related service/desktop architecture.

The XML schemas and local CS9 routes in this release were observed in installed
SRS 2025.5.2 / SRC s8.21.1cs9_BS4740. This is observed compatibility, not a stable
vendor SDK contract. Vendor internal .NET assemblies are not loaded or redistributed.
