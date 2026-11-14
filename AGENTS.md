# Repository guidance

This is public source. Keep controller captures, vendor binaries, customer projects,
credentials, personal paths and acceptance reports outside Git or in ignored `.local/`.
Use synthetic fixtures. Stage named paths and inspect staged diffs before publishing.

Work on main unless isolation is needed. Commit verified increments and push often
when authorized. Keep README commands and capability boundaries current. Run local
tests; any GitHub Actions must be workflow_dispatch only.

Share transport-independent services between CLI and GUI. Do not add an MCP server,
background listener, controller writes or motion in this phase. Separate offline,
simulator and physical-controller evidence. SRS internal assemblies are not a public SDK.
