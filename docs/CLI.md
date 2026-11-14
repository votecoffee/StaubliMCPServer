# Headless command guide

Run `RunWorkbench.cmd` from any working directory after installing the checkout in
its `.venv`. An installed `staubli` command has the same arguments.

```powershell
.\RunWorkbench.cmd catalog
.\RunWorkbench.cmd describe project.inspect
.\RunWorkbench.cmd run srs.discover
```

Use UTF-8 request files to avoid Windows command-line JSON quoting:

```powershell
New-Item -ItemType Directory -Force .local | Out-Null
@{path='C:\RobotProjects\ExampleCell'} | ConvertTo-Json | Set-Content -Encoding utf8 .local\request.json
.\RunWorkbench.cmd run project.inspect --args-file .local\request.json --output .local\inspection.json
```

`--output` creates a new receipt and refuses overwrite. Exit status is 0 for
success, 1 for an operation/request/receipt failure, and 2 for command syntax
errors. Successful invocations print one JSON object to stdout. Operation errors
carry `ok=false`, `error.code`, `error.message` and `data=null`. Execution receipts
include operation, schema version, package version, request ID and elapsed time.
Parser errors are written by argparse to stderr. There is no resident server.

## Operations

| Operation | Arguments | Behavior |
|---|---|---|
| `srs.discover` | none | Find SRS installations without loading vendor code |
| `srs.launch` | `executable`, `cell` | Launch an explicit executable with a `.cell` argument; opening is unverified |
| `project.inventory` | `path` directory | List relative file paths, sizes and extensions |
| `project.inspect` | `path` directory | Inspect XML, hashes and local references; report missing/escaping targets |
| `project.compare` | `left`, `right` directories | Byte-hash additions, removals and changes |
| `project.search` | `path`, `text`, optional `limit` (100) | Literal case-insensitive text search with line numbers |
| `xml.inspect` | `path` file | XML namespace, attributes and bounded element listing |
| `val3.analyze` | `path` .pjx/.pgx/.dtx | Program/data inventory and lexical call/motion candidates |
| `simulator.read` | `resource`, `port`, optional `insecure_tls` (false), `timeout` (5) | One bounded local HTTPS GET |

`describe` returns the authoritative argument types and ranges. No operation
deploys applications, changes controller data or commands motion. Desktop launch
opens vendor software and may activate whatever behavior that software associates
with the selected cell; only request it when opening that cell is intended.

## Local CS9 simulator

Establish independently that the chosen port belongs to the intended local SRS
emulator. The adapter fixes the host to `127.0.0.1`, disables proxies and follows
no redirects. Locality does not prove controller identity. It never scans ports,
retries, enumerates links or adds arbitrary API paths.

```powershell
@{resource='position';port=850;insecure_tls=$true;timeout=5} | ConvertTo-Json | Set-Content -Encoding utf8 .local\simulator.json
.\RunWorkbench.cmd run simulator.read --args-file .local\simulator.json
```

Port 850 is an example, not a universal default. TLS verification is enabled unless
explicitly disabled for that invocation. The self-signed emulator certificate may
require `insecure_tls=true`. Responses are limited to 2 MiB and reads to 30 seconds.
Allowed resources: `model`, `payload`, `limits`, `axis`, `position`, and
`static_joint_torque`. Raw vendor fields and units remain unconverted; verify
the selected controller documentation before interpreting them. Payload settings
are external load data, not robot link inertia tensors. These endpoints are
experimental and may differ by controller revision or require authentication.

## Saved-source limits

Directory scans stop at 20,000 files; reads are limited to 8 MiB per file, and
comparison/search/XML inspection have a 256 MiB aggregate budget. Subdirectory
symlinks and Windows junctions are not traversed. The selected root itself may be
an explicitly resolved link. XML entity expansion and external entities are rejected.
Search supports UTF-8/BOM, BOM-marked UTF-16 and a CP1252 fallback. XML parsing honors
the file declaration. Parsers never save or normalize the source.

Hash receipts identify the bytes read; they are not transactional snapshots of a
running emulator's changing directory. For comparisons that require stable evidence,
use saved copies. VAL3 calls are lexical candidates, not a full grammar, call graph,
compiler, unit conversion or safety check. Launch requests are not native acceptance.
