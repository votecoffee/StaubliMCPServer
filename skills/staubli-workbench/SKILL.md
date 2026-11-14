---
name: staubli-workbench
description: Use the standalone Stäubli workbench to inspect SRS cells and VAL3 sources, compare saved projects, discover SRS installations, or read explicitly selected local CS9 simulator resources.
---

# Stäubli workbench

Use this repository's Python CLI for repeatable engineering operations. It shares
services with the desktop GUI and contains no MCP server. The maintained checkout
is the directory two levels above this skill folder. Use its absolute
`RunWorkbench.cmd` path on Windows or the installed `staubli` command. If the skill
was copied elsewhere, locate the user's checkout rather than guessing a personal path.
Read [the CLI guide](../../docs/CLI.md) for contracts and limits and
[architecture](../../docs/ARCHITECTURE.md) when extending adapters.

## Routing

- Start with `catalog` or `describe <operation>` to obtain supported schemas.
- Use `srs.discover` to find installations; it does not establish license or SDK readiness.
- For a saved cell, pass its containing directory to `project.inventory` and
  `project.inspect`. A `.cell` references controller files; VAL3 `.pjx` files
  reference `.pgx` programs and `.dtx` databases. XML namespaces vary by format.
- Use `val3.analyze` for program/data inventories and lexical call candidates;
  use `project.search` for literal references. These do not compile or establish
  reachability, execution order, motion behavior or runtime values.
- Use `project.compare` on stable saved directories for byte-level differences.
- Use `xml.inspect` to inspect one supported source without modifying its encoding,
  namespaces or CDATA. Native compilation remains a separate acceptance step.
- Use `srs.launch` only when opening the selected cell in vendor software is part
  of the user's task. A returned PID proves only a launch request, not cell loading.
- Use `simulator.read` only after establishing that the explicit loopback port
  belongs to the intended local emulator. Choose one catalog resource; do not
  probe other routes or assume the port is universal. Unverified TLS is an explicit
  per-request option for a self-signed local certificate. Read errors stop the call.

## Invocation and evidence

Create UTF-8 JSON argument files outside public source or in ignored `.local/` and
invoke `run <operation> --args-file <absolute-file>`. This avoids Windows shell
quoting problems. `--output <new-file>` optionally saves a receipt and refuses overwrite.
Check both process status and `ok`. Preserve operation, package/schema versions,
source hashes, endpoint, completeness flags and any reported findings in handoffs.
An `ok` inspection may contain missing-reference or XML findings: inspect them.

Keep saved-source, local-endpoint, native SRS and physical-controller evidence
distinct. Locality alone does not authenticate an emulator. Raw simulator fields
retain vendor units/conventions; consult the selected controller documentation.
Payload properties are not robot link mass/inertia tensors.

This phase provides no native compiler adapter, deployment, controller setting
writes or motion commands. Do not improvise writes through internal SRS DLLs or
arbitrary web endpoints. When extending the workbench, use the shared registry
and services; keep Qt optional and future transport code separate. Track native
qualification and reviewed source changes using the linked architecture roadmap.
