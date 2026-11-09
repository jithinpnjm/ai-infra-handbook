"""Drive triage_repro with tiny settings: it must finish and clean up."""
import glob
import tempfile

import pytest

import triage_repro as t


def test_cpu_starts_and_joins_its_workers():
    assert t.main(["cpu", "--procs", "2", "--seconds", "0.2"]) == 2


def test_disk_writes_then_removes_its_file():
    before = set(glob.glob(tempfile.gettempdir() + "/triage_disk_*"))
    assert t.main(["disk", "--mb", "3", "--seconds", "5"]) == 3
    assert set(glob.glob(tempfile.gettempdir() + "/triage_disk_*")) == before


def test_mem_holds_the_asked_size():
    assert t.main(["mem", "--mb", "8", "--seconds", "0.1"]) == 8


def test_oversized_request_is_refused():
    with pytest.raises(SystemExit):
        t.main(["mem", "--mb", "999999"])
