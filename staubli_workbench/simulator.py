"""Experimental, explicitly selected local CS9 web reads."""
import http.client
import json
import ssl
import time

RESOURCES = {name: "/api/arm/" + name for name in ("model", "payload", "limits", "axis", "position")}
RESOURCES["static_joint_torque"] = "/api/arm/model/staticjnttorque"
MAX_RESPONSE = 2 * 1024 * 1024


def read(resource, port, insecure_tls=False, timeout=5):
    if resource not in RESOURCES:
        raise ValueError("Unknown resource; select " + ", ".join(RESOURCES))
    if not 1 <= port <= 65535 or not 0.1 <= timeout <= 30:
        raise ValueError("Use port 1..65535 and timeout 0.1..30 seconds")
    context = ssl._create_unverified_context() if insecure_tls else ssl.create_default_context()
    connection = http.client.HTTPSConnection("127.0.0.1", port, timeout=timeout, context=context)
    deadline = time.monotonic() + timeout
    try:
        connection.request("GET", RESOURCES[resource], headers={"Accept": "application/json", "Connection": "close"})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"Simulator returned HTTP {response.status}; redirects are not followed")
        chunks, size = [], 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Simulator read deadline exceeded")
            # Connection: close can detach the socket; response still owns its file.
            sock = connection.sock or getattr(getattr(response.fp, "raw", None), "_sock", None)
            if sock is not None:
                sock.settimeout(remaining)
            chunk = response.read1(min(65536, MAX_RESPONSE + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_RESPONSE:
                raise ValueError("Simulator response exceeds byte budget")
        payload = json.loads(b"".join(chunks))
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object from selected simulator resource")
        return {"resource": resource, "endpoint": f"https://127.0.0.1:{port}{RESOURCES[resource]}",
                "payload": payload, "tls_verified": not insecure_tls,
                "evidence": "local-endpoint-read", "controller_identity_verified": False,
                "note": "Experimental CS9 endpoint; caller must establish local emulator identity. Payload settings are not robot link inertias."}
    finally:
        connection.close()
