import io
import pytest
from staubli_workbench import simulator
from staubli_workbench.registry import execute


class Response:
    status = 200
    fp = None
    def __init__(self, data=b'{"joints":{"j1":0}}'):
        self.stream = io.BytesIO(data)
    def read1(self, size):
        return self.stream.read(size)


class Connection:
    instances = []
    response = Response
    sock = None
    def __init__(self, host, port, **kwargs):
        self.host, self.port, self.kwargs = host, port, kwargs
        self.closed = False
        self.instances.append(self)
    def request(self, method, path, headers):
        self.requested = (method, path)
    def getresponse(self):
        return self.response()
    def close(self):
        self.closed = True


def test_read_fixed_host_and_resource(monkeypatch):
    monkeypatch.setattr(simulator.http.client, "HTTPSConnection", Connection)
    result = execute("simulator.read", {"resource": "position", "port": 850})
    assert result["ok"] and result["data"]["tls_verified"]
    connection = Connection.instances[-1]
    assert connection.host == "127.0.0.1" and connection.closed
    assert connection.requested == ("GET", "/api/arm/position")


def test_redirect_is_not_followed_and_connection_closes(monkeypatch):
    class Redirect(Response):
        status = 302
    monkeypatch.setattr(Connection, "response", Redirect)
    monkeypatch.setattr(simulator.http.client, "HTTPSConnection", Connection)
    assert not execute("simulator.read", {"resource": "position", "port": 850})["ok"]
    assert Connection.instances[-1].closed


@pytest.mark.parametrize("resource,port", [("../../write", 850), ("position", 0), ("position", 70000)])
def test_invalid_target_fails_before_connect(resource, port, monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Invalid request attempted a connection")
    monkeypatch.setattr(simulator.http.client, "HTTPSConnection", fail)
    assert not execute("simulator.read", {"resource": resource, "port": port})["ok"]


def test_response_byte_budget_closes_connection(monkeypatch):
    monkeypatch.setattr(simulator, "MAX_RESPONSE", 2)
    monkeypatch.setattr(simulator.http.client, "HTTPSConnection", Connection)
    assert not execute("simulator.read", {"resource": "position", "port": 850})["ok"]
    assert Connection.instances[-1].closed
