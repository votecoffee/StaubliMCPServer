"""Bounded, read-only access to saved engineering sources."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PureWindowsPath
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

MAX_FILES = 20000
MAX_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
XML_SUFFIXES = {".cell", ".controller", ".pjx", ".pgx", ".dtx", ".xml"}
TEXT_SUFFIXES = XML_SUFFIXES | {".txt", ".log", ".ini", ".conf", ".cfg", ".json"}


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def root_path(path):
    root = Path(path).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Expected an existing project directory")
    return root


def entries(path):
    root = root_path(path)
    result = []
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(folder) / d).is_symlink()
                         and not getattr(Path(folder) / d, "is_junction", lambda: False)())
        for name in sorted(files):
            file = Path(folder) / name
            if file.is_symlink() or not file.resolve().is_relative_to(root):
                continue
            if len(result) >= MAX_FILES:
                raise ValueError(f"Project exceeds {MAX_FILES} files; choose a smaller root")
            result.append(file)
    return root, sorted(result, key=lambda p: p.relative_to(root).as_posix())


def read_bytes(file, limit=MAX_BYTES):
    with file.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"File exceeds {limit} byte limit: {file.name}")
    return data


def digest(file):
    return hashlib.sha256(read_bytes(file)).hexdigest()


def xml(file):
    return ET.fromstring(read_bytes(file))


def decode(data):
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16"
    try:
        return data.decode("utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        return data.decode("cp1252"), "cp1252"


def reference(base, text, root):
    # SRS stores Windows separators even when inspected on another OS.
    windows = PureWindowsPath(text)
    if windows.is_absolute() or windows.drive or windows.root:
        raise ValueError("Absolute project reference")
    candidate = (base / Path(*windows.parts)).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Project reference escapes selected root")
    return candidate


def inventory(path):
    root, files = entries(path)
    return {"root": str(root), "files": [
        {"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
         "kind": p.suffix.lower().lstrip(".") or "other"} for p in files],
        "count": len(files), "evidence": "saved-files"}


def inspect_xml(path):
    file = Path(path).expanduser().resolve(strict=True)
    if file.suffix.lower() not in XML_SUFFIXES:
        raise ValueError("Select .cell, .controller, .pjx, .pgx, .dtx or .xml")
    tree = xml(file)
    elements = list(tree.iter())
    return {"path": str(file), "sha256": digest(file), "root": tree.tag,
            "attributes": tree.attrib, "element_count": len(elements),
            "elements": [{"tag": local_name(e.tag), "attributes": e.attrib}
                         for e in elements[:1000]],
            "truncated": len(elements) > 1000, "evidence": "saved-xml"}


def inspect_project(path):
    root, files = entries(path)
    selected = [p for p in files if p.suffix.lower() in XML_SUFFIXES]
    if sum(p.stat().st_size for p in selected) > MAX_TOTAL_BYTES:
        raise ValueError("XML budget exceeded; choose a smaller project root")
    documents, findings = [], []
    for file in selected:
        relative = file.relative_to(root).as_posix()
        try:
            tree = xml(file)
            refs = []
            for element in tree.iter():
                for key in ("file", "path"):
                    if key not in element.attrib:
                        continue
                    value = element.attrib[key]
                    row = {"reference": value}
                    try:
                        target = reference(file.parent, value, root)
                        row["exists"] = target.is_file()
                        if not row["exists"]:
                            findings.append({"file": relative, "code": "missing_reference", "reference": value})
                    except ValueError as exc:
                        row["error"] = str(exc)
                        findings.append({"file": relative, "code": "unsafe_reference", "reference": value})
                    refs.append(row)
            documents.append({"file": relative, "root": local_name(tree.tag),
                              "attributes": tree.attrib, "sha256": digest(file), "references": refs})
        except (ET.ParseError, DefusedXmlException, ValueError) as exc:
            findings.append({"file": relative, "code": "invalid_xml", "detail": str(exc)})
    return {"root": str(root), "documents": documents, "findings": findings,
            "evidence": "saved-files", "native_compile_verified": False}


def compare(left, right):
    def manifest(path):
        root, files = entries(path)
        if sum(p.stat().st_size for p in files) > MAX_TOTAL_BYTES:
            raise ValueError("Comparison byte budget exceeded")
        return {p.relative_to(root).as_posix(): digest(p) for p in files}
    a, b = manifest(left), manifest(right)
    return {"added": sorted(b.keys() - a.keys()), "removed": sorted(a.keys() - b.keys()),
            "changed": [{"path": p, "before_sha256": a[p], "after_sha256": b[p]}
                        for p in sorted(a.keys() & b.keys()) if a[p] != b[p]],
            "unchanged": sum(a[p] == b[p] for p in a.keys() & b.keys()), "evidence": "saved-files"}


def search(path, text, limit=100):
    if not text or not 1 <= limit <= 1000:
        raise ValueError("Use nonempty text and limit 1..1000")
    root, files = entries(path)
    matches, skipped, consumed = [], [], 0
    for file in files:
        if file.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = file.relative_to(root).as_posix()
        if consumed + file.stat().st_size > MAX_TOTAL_BYTES:
            raise ValueError("Search byte budget exceeded")
        try:
            data = read_bytes(file)
            consumed += len(data)
            content, encoding = decode(data)
        except (ValueError, UnicodeError) as exc:
            skipped.append({"file": relative, "detail": str(exc)})
            continue
        for number, line in enumerate(content.splitlines(), 1):
            if text.casefold() in line.casefold():
                if len(matches) == limit:
                    return {"matches": matches, "truncated": True, "skipped": skipped}
                matches.append({"file": relative, "line": number, "text": line[:1000], "encoding": encoding})
    return {"matches": matches, "truncated": False, "skipped": skipped}
