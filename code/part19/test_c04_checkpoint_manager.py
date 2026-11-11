import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from c04_checkpoint_manager import CheckpointManager, MANIFEST  # noqa: E402


def payload(step):
    return {"model.bin": f"model-{step}".encode() * 100, "optim.bin": b"o" * 500}


def test_save_and_resume_latest(tmp_path):
    m = CheckpointManager(str(tmp_path), keep=3)
    for s in (100, 200, 300):
        m.save_files(s, payload(s), meta={"loss": 1.0 / s})
    step, path, skipped = m.latest_valid()
    assert step == 300 and skipped == []
    assert os.path.isfile(os.path.join(path, "model.bin"))
    assert m.manifest_meta(300)["loss"] == pytest.approx(1 / 300)


def test_keep_n_prunes_oldest(tmp_path):
    m = CheckpointManager(str(tmp_path), keep=2)
    for s in (1, 2, 3, 4):
        m.save_files(s, payload(s))
    assert m.committed_steps() == [3, 4]


def test_crash_before_commit_leaves_no_visible_checkpoint(tmp_path):
    m = CheckpointManager(str(tmp_path), keep=3)
    m.save_files(100, payload(100))
    tmp = m.begin(200)  # writer starts, then the process dies
    with open(os.path.join(tmp, "model.bin"), "wb") as f:
        f.write(b"half")
    assert m.committed_steps() == [100]
    assert m.latest_valid()[0] == 100


def test_begin_discards_leftover_staging_of_same_step(tmp_path):
    m = CheckpointManager(str(tmp_path))
    tmp = m.begin(5)
    with open(os.path.join(tmp, "stale.bin"), "wb") as f:
        f.write(b"x")
    tmp2 = m.begin(5)
    assert os.listdir(tmp2) == []


def test_commit_refuses_to_overwrite(tmp_path):
    m = CheckpointManager(str(tmp_path))
    m.save_files(7, payload(7))
    m.begin(7)
    with pytest.raises(FileExistsError):
        m.commit(7)


def test_flipped_byte_is_detected_by_checksum(tmp_path):
    m = CheckpointManager(str(tmp_path), keep=3)
    m.save_files(100, payload(100))
    target = os.path.join(m.path_for(100), "model.bin")
    data = bytearray(open(target, "rb").read())
    data[10] ^= 0xFF  # same size, one corrupted byte
    open(target, "wb").write(bytes(data))
    assert m.verify(100, full=False).ok  # size check alone misses it
    v = m.verify(100, full=True)
    assert not v.ok and "checksum mismatch model.bin" in v.problems


def test_truncated_file_is_detected_by_size(tmp_path):
    m = CheckpointManager(str(tmp_path))
    m.save_files(100, payload(100))
    target = os.path.join(m.path_for(100), "optim.bin")
    open(target, "wb").write(b"short")
    v = m.verify(100, full=False)
    assert not v.ok and "size mismatch optim.bin" in v.problems


def test_missing_manifest_means_incomplete(tmp_path):
    m = CheckpointManager(str(tmp_path))
    m.save_files(100, payload(100))
    os.remove(os.path.join(m.path_for(100), MANIFEST))
    assert m.verify(100).problems == ["manifest missing"]


def test_resume_skips_corrupt_newest_and_uses_previous(tmp_path):
    m = CheckpointManager(str(tmp_path), keep=3)
    for s in (100, 200, 300):
        m.save_files(s, payload(s))
    target = os.path.join(m.path_for(300), "model.bin")
    data = bytearray(open(target, "rb").read())
    data[0] ^= 0x01
    open(target, "wb").write(bytes(data))
    step, path, skipped = m.latest_valid()
    assert step == 200
    assert skipped[0][0] == 300 and "checksum mismatch model.bin" in skipped[0][1]


def test_all_corrupt_returns_none(tmp_path):
    m = CheckpointManager(str(tmp_path))
    m.save_files(1, payload(1))
    os.remove(os.path.join(m.path_for(1), "model.bin"))
    step, path, skipped = m.latest_valid()
    assert step is None and path is None and len(skipped) == 1


def test_quarantine_renames_bad_checkpoint(tmp_path):
    m = CheckpointManager(str(tmp_path))
    m.save_files(1, payload(1))
    m.save_files(2, payload(2))
    os.remove(os.path.join(m.path_for(2), "model.bin"))
    step, _, _ = m.latest_valid(quarantine=True)
    assert step == 1
    assert os.path.isdir(m.path_for(2) + ".corrupt")
    assert m.committed_steps() == [1]


def test_prune_keeps_last_good_when_newest_is_corrupt(tmp_path):
    m = CheckpointManager(str(tmp_path), keep=1)
    m.save_files(1, payload(1))
    m.save_files(2, payload(2))  # prune: step 1 is evicted, keep=1
    m = CheckpointManager(str(tmp_path), keep=2)
    m.save_files(3, payload(3))
    os.remove(os.path.join(m.path_for(3), "optim.bin"))
    m.prune()  # step 3 is bad, so both good steps survive
    assert m.committed_steps() == [2, 3]
    assert m.latest_valid()[0] == 2


def test_keep_one_with_bad_newest_keeps_older_good(tmp_path):
    m = CheckpointManager(str(tmp_path), keep=1)
    m.save_files(1, payload(1))
    tmp = m.begin(2)
    with open(os.path.join(tmp, "model.bin"), "wb") as f:
        f.write(b"abc")
    m.commit(2)
    os.truncate(os.path.join(m.path_for(2), "model.bin"), 1)
    m.save_files(3, payload(3))  # prune runs: 2 is bad, 1 and 3 are good
    assert m.committed_steps() == [2, 3]
    assert m.latest_valid()[0] == 3
