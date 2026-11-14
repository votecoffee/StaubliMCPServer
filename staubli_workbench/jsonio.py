"""Strict bounded request JSON for automation."""
import json

MAX_REQUEST = 1024 * 1024


def loads(text):
    if len(text.encode("utf-8")) > MAX_REQUEST:
        raise ValueError("Request exceeds 1 MiB")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Nonfinite JSON number: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
