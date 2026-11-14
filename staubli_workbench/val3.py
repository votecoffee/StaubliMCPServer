"""Source inspection, deliberately not a VAL3 compiler."""
import re
from pathlib import Path
from .files import document, local_name


def analyze(path):
    file = Path(path).expanduser().resolve(strict=True)
    if file.suffix.lower() not in {".pgx", ".dtx", ".pjx"}:
        raise ValueError("Select a VAL3 .pgx, .dtx or .pjx file")
    tree, sha256 = document(file)
    programs, data, references = [], [], []
    for element in tree.iter():
        tag = local_name(element.tag)
        if tag == "Program" and "name" in element.attrib:
            code = "\n".join(e.text or "" for e in element.iter() if local_name(e.tag) == "Code")
            # Remove comments and quoted strings before collecting call candidates.
            stripped = re.sub(r'//[^\n]*|"(?:""|[^"\n])*"', "", code)
            calls = sorted(set(re.findall(r"\b([A-Za-z_][\w:]*)\s*\(", stripped)))
            programs.append({"name": element.attrib["name"], "attributes": element.attrib,
                             "lines": len(code.splitlines()), "call_candidates": calls,
                             "motion_candidates": [c for c in calls if c.lower() in
                                 {"movej", "movel", "movec", "moves", "movelf", "movejf"}]})
        if tag == "Data" and "name" in element.attrib:
            data.append({"name": element.attrib["name"], "attributes": element.attrib,
                         "values": [v.attrib for v in element if local_name(v.tag) == "Value"]})
        for key in ("file", "path"):
            if key in element.attrib:
                references.append(element.attrib[key])
    return {"path": str(file), "sha256": sha256, "programs": programs,
            "data": data, "references": references, "evidence": "saved-source",
            "analysis": "Lexical call candidates only; not compilation, reachability or motion validation"}
