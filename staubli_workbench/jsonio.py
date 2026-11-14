"""Strict bounded request JSON for automation."""
import json
import math

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
    def floating(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("Nonfinite JSON number: " + value)
        return parsed
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=floating)
