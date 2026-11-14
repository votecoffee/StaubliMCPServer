import json
import subprocess
import sys
import pytest
from staubli_workbench import files
from staubli_workbench.registry import execute, catalog


@pytest.fixture
def project(tmp_path):
    (tmp_path / "demo.cell").write_text('<Cell xmlns="urn:synthetic" version="test"><File path="Controller1\\demo.pjx"/></Cell>')
    controller = tmp_path / "Controller1"
    controller.mkdir()
    (controller / "demo.pjx").write_text('<Project><Programs><Program file="start.pgx"/></Programs><Data file="missing.dtx"/></Project>')
    (controller / "start.pgx").write_text('<Programs xmlns="urn:synthetic"><Program name="start"><Code><![CDATA[begin\n// movej(fake)\n s="movel(fake)"\n movej(jHome,tTool,mSpeed)\n call worker()\nend]]></Code></Program></Programs>')
    return tmp_path


def test_project_references_and_val3(project):
    result = execute("project.inspect", {"path": str(project)})
    assert result["ok"]
    assert [f["reference"] for f in result["data"]["findings"]] == ["missing.dtx"]
    program = execute("val3.analyze", {"path": str(project / "Controller1/start.pgx")})["data"]["programs"][0]
    assert program["motion_candidates"] == ["movej"]
    assert program["call_candidates"] == ["movej", "worker"]


def test_entities_and_escape_are_reported(project):
    (project / "bad.xml").write_text('<!DOCTYPE x [<!ENTITY x "bad">]><x>&x;</x>')
    (project / "escape.pjx").write_text('<Project><Program file="..\\..\\outside.pgx"/></Project>')
    findings = files.inspect_project(project)["findings"]
    assert any(f["code"] == "invalid_xml" for f in findings)
    assert any(f["code"] == "unsafe_reference" for f in findings)


def test_compare_uses_bytes_and_names(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(); b.mkdir()
    (a / "same").write_bytes(b"same"); (b / "same").write_bytes(b"same")
    (a / "changed").write_bytes(b"a"); (b / "changed").write_bytes(b"b")
    (a / "removed").write_bytes(b"a"); (b / "added").write_bytes(b"b")
    result = files.compare(a, b)
    assert result["added"] == ["added"] and result["removed"] == ["removed"]
    assert result["changed"][0]["path"] == "changed" and result["unchanged"] == 1


def test_bounded_read_and_search(project, monkeypatch):
    assert files.search(project, "movej", 1)["truncated"]
    monkeypatch.setattr(files, "MAX_FILES", 1)
    with pytest.raises(ValueError):
        files.inventory(project)
    with pytest.raises(ValueError):
        files.read_bytes(project / "demo.cell", 2)


@pytest.mark.parametrize("name,args", [("absent", {}), ("project.inventory", {}),
    ("project.inventory", {"path": 1}), ("srs.discover", {"oops": 2}),
    ("project.search", {"path": "x", "text": "y", "limit": True}),
    ("srs.discover", [])])
def test_invalid_contract_returns_error(name, args):
    assert not execute(name, args)["ok"]


def test_cli_is_json_and_has_no_qt_or_mcp_import():
    process = subprocess.run([sys.executable, "-m", "staubli_workbench.cli", "catalog"], capture_output=True, text=True)
    assert process.returncode == 0
    assert len(json.loads(process.stdout)["operations"]) == len(catalog())
    probe = subprocess.run([sys.executable, "-c", "import sys; import staubli_workbench.cli; assert not any(n.startswith(('PySide6','mcp')) for n in sys.modules)"], capture_output=True)
    assert probe.returncode == 0


def test_cli_receipt_refuses_overwrite(tmp_path):
    output = tmp_path / "receipt.json"
    output.write_text("keep")
    process = subprocess.run([sys.executable, "-m", "staubli_workbench.cli", "run", "srs.discover", "--output", str(output)], capture_output=True, text=True)
    assert process.returncode == 1
    assert json.loads(process.stdout)["error"]["code"] == "ReceiptWriteError"
    assert output.read_text() == "keep"


@pytest.mark.parametrize("text", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'])
def test_strict_request_json(text):
    from staubli_workbench.jsonio import loads
    with pytest.raises(ValueError):
        loads(text)


def test_directory_junction_is_not_traversed(tmp_path):
    import os
    if os.name != "nt":
        pytest.skip("Windows junction check")
    outside, root = tmp_path / "outside", tmp_path / "project"
    outside.mkdir(); root.mkdir()
    (outside / "private.xml").write_text("<private/>")
    junction = root / "linked"
    created = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True)
    if created.returncode:
        pytest.skip("Junction creation unavailable")
    assert files.inventory(root)["count"] == 0


def test_launch_rejects_cell_directory_without_starting_process(tmp_path, monkeypatch):
    from staubli_workbench import srs
    exe, cell = tmp_path / "StaubliRoboticsSuite.exe", tmp_path / "example.cell"
    exe.write_bytes(b"synthetic")
    cell.mkdir()
    def unexpected(*args, **kwargs):
        pytest.fail("Invalid target started a process")
    monkeypatch.setattr(srs.subprocess, "Popen", unexpected)
    assert not execute("srs.launch", {"executable": str(exe), "cell": str(cell)})["ok"]
