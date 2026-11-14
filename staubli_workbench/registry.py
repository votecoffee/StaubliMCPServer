"""Small typed operation contract usable by any future transport."""
from __future__ import annotations
from dataclasses import dataclass
import inspect
import time
import uuid
from . import __version__, files, srs, val3


@dataclass(frozen=True)
class Operation:
    name: str
    description: str
    function: object
    inputs: dict
    effect: str = "read-local"

    def descriptor(self):
        signature = inspect.signature(self.function)
        return {"name": self.name, "description": self.description, "effect": self.effect,
                "input_schema": {"type": "object", "properties": self.inputs,
                    "required": [k for k, v in signature.parameters.items() if v.default is inspect.Parameter.empty],
                    "additionalProperties": False}}


STRING = {"type": "string"}
OPERATIONS = [
    Operation("srs.discover", "Find installed SRS executable versions without loading them", srs.discover, {}),
    Operation("srs.launch", "Request SRS to open a cell in the desktop", srs.launch,
              {"executable": STRING, "cell": STRING}, "launch-desktop"),
    Operation("project.inventory", "List bounded saved-project files", files.inventory, {"path": STRING}),
    Operation("project.inspect", "Inspect saved XML and check local references", files.inspect_project, {"path": STRING}),
    Operation("project.compare", "Compare two project directories by byte hashes", files.compare, {"left": STRING, "right": STRING}),
    Operation("project.search", "Search saved text literally, case-insensitively", files.search,
              {"path": STRING, "text": STRING, "limit": {"type": "integer", "minimum": 1, "maximum": 1000}}),
    Operation("xml.inspect", "Inspect namespaced SRS/VAL3 XML metadata", files.inspect_xml, {"path": STRING}),
    Operation("val3.analyze", "Inspect VAL3 programs, data and call candidates", val3.analyze, {"path": STRING}),
]


def catalog():
    return [operation.descriptor() for operation in OPERATIONS]


def execute(name, arguments):
    start = time.monotonic()
    result = {"schema_version": 1, "version": __version__, "request_id": str(uuid.uuid4()), "operation": name}
    try:
        operation = next((op for op in OPERATIONS if op.name == name), None)
        if operation is None:
            raise ValueError(f"Unknown operation: {name}; use catalog")
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a JSON object")
        inspect.signature(operation.function).bind(**arguments)
        for key, value in arguments.items():
            spec = operation.inputs[key]
            expected = {"string": str, "integer": int, "boolean": bool, "number": (int, float)}[spec["type"]]
            if not isinstance(value, expected) or (isinstance(value, bool) and spec["type"] != "boolean"):
                raise ValueError(f"Invalid type for {key}: expected {spec['type']}")
            if "minimum" in spec and not spec["minimum"] <= value <= spec["maximum"]:
                raise ValueError(f"{key} out of range")
        result.update(ok=True, data=operation.function(**arguments), error=None)
    except Exception as exc:
        result.update(ok=False, data=None, error={"code": type(exc).__name__, "message": str(exc)})
    result["elapsed_ms"] = round((time.monotonic() - start) * 1000, 2)
    return result
