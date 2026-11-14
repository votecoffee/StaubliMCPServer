"""One-shot JSON front end; no GUI imports or resident worker."""
import argparse
import json
from pathlib import Path
import sys
from .registry import catalog, execute
from .jsonio import loads, MAX_REQUEST


def main(argv=None):
    parser = argparse.ArgumentParser(description="Standalone Stäubli workbench")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("catalog", help="List operations and input schemas")
    describe = sub.add_parser("describe", help="Describe one operation")
    describe.add_argument("operation")
    run = sub.add_parser("run", help="Execute one operation")
    run.add_argument("operation")
    args = run.add_mutually_exclusive_group()
    args.add_argument("--args", default=None, help="JSON object")
    args.add_argument("--args-file", type=Path, help="UTF-8 JSON object (avoids shell quoting)")
    run.add_argument("--output", type=Path, help="Create a new JSON receipt; refuses overwrite")
    options = parser.parse_args(argv)
    if options.command == "catalog":
        print(json.dumps({"schema_version": 1, "operations": catalog()}, ensure_ascii=True))
        return 0
    if options.command == "describe":
        operation = next((op for op in catalog() if op["name"] == options.operation), None)
        print(json.dumps({"schema_version": 1, "ok": operation is not None, "data": operation,
                          "error": None if operation else {"code": "unknown_operation", "message": "Use catalog"}}))
        return 0 if operation else 1
    try:
        if options.args_file:
            with options.args_file.open("rb") as stream:
                source = stream.read(MAX_REQUEST + 1).decode("utf-8-sig")
        else:
            source = options.args or "{}"
        result = execute(options.operation, loads(source))
    except (OSError, ValueError) as exc:
        result = {"schema_version": 1, "operation": options.operation, "ok": False,
                  "data": None, "error": {"code": type(exc).__name__, "message": str(exc)}}
    rendered = json.dumps(result, ensure_ascii=True)
    if options.output:
        try:
            with options.output.open("x", encoding="utf-8") as stream:
                stream.write(rendered + "\n")
        except OSError as exc:
            result = {"schema_version": 1, "operation": options.operation, "ok": False,
                      "data": None, "error": {"code": "ReceiptWriteError", "message": str(exc)}}
            rendered = json.dumps(result)
    print(rendered)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
