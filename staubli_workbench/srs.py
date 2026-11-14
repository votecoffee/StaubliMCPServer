"""Installation discovery and explicit desktop launch; no private DLL loading."""
import os
from pathlib import Path
import subprocess


def discover():
    installations = []
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        base = Path(os.environ.get(variable, "C:/Program Files")) / "Staubli"
        if not base.is_dir():
            continue
        for executable in sorted(base.glob("SRS*/app-*/StaubliRoboticsSuite.exe")):
            installations.append({"executable": str(executable), "version_folder": executable.parent.name,
                                  "sdk_verified": False})
    return {"installations": installations, "evidence": "filesystem-discovery",
            "note": "Presence does not verify license, SDK availability or a running session"}


def launch(executable, cell):
    exe, source = Path(executable).resolve(strict=True), Path(cell).resolve(strict=True)
    if exe.name.lower() != "staubliroboticssuite.exe" or source.suffix.lower() != ".cell":
        raise ValueError("Select StaubliRoboticsSuite.exe and an existing .cell")
    if os.name != "nt":
        raise ValueError("SRS launch requires Windows")
    process = subprocess.Popen([str(exe), str(source)], cwd=exe.parent)
    return {"pid": process.pid, "requested_cell": str(source), "evidence": "launch-request",
            "opened_verified": False}
