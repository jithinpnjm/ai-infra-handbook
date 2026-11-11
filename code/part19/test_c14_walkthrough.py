import pathlib
import sys
from collections import Counter

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import c14_bank  # noqa: E402
import c14_walkthrough as w  # noqa: E402


@pytest.fixture(scope="module")
def bank():
    return c14_bank.load_bank()


def test_set_size_and_uniqueness(bank):
    qs = w.pick_set(bank, 20, seed=1)
    assert len(qs) == 20 and len({q["id"] for q in qs}) == 20


def test_mixed_topics_in_short_set(bank):
    qs = w.pick_set(bank, 10, seed=2)
    assert len({q["topic"] for q in qs}) == 10


def test_level_mix_follows_weights(bank):
    c = Counter(q["difficulty"] for q in w.pick_set(bank, 20, seed=3))
    assert c["core"] >= 7 and c["senior"] >= 8 and c["stretch"] >= 2


def test_filters_applied(bank):
    qs = w.pick_set(bank, 5, topics=["linux", "storage"], levels=["senior"], seed=4)
    assert all(q["topic"] in ("linux", "storage") and q["difficulty"] == "senior" for q in qs)


def test_seed_reproducible(bank):
    a = [q["id"] for q in w.pick_set(bank, 12, seed=7)]
    b = [q["id"] for q in w.pick_set(bank, 12, seed=7)]
    c = [q["id"] for q in w.pick_set(bank, 12, seed=8)]
    assert a == b and a != c


def test_whole_bank_when_n_equals_pool(bank):
    assert len(w.pick_set(bank, len(bank["questions"]), seed=1)) == len(bank["questions"])


def test_too_many_and_bad_n_fail(bank):
    with pytest.raises(ValueError):
        w.pick_set(bank, 500)
    with pytest.raises(ValueError):
        w.pick_set(bank, 0)
    with pytest.raises(ValueError):
        w.pick_set(bank, 50, topics=["behavioural"], levels=["stretch"])


def test_render_hides_answers_by_default(bank):
    q = bank["questions"][0]
    assert "Model answer" not in w.render(q, 1)
    full = w.render(q, 1, answers=True)
    assert "Model answer" in full and "Follow-up" in full and q["link"] in full


def test_cli(capsys):
    assert w.main(["--n", "4", "--seed", "1", "--topic", "linux", "--answers"]) == 0
    out = capsys.readouterr().out
    assert out.count("Model answer") == 4
    assert w.main(["--n", "999"]) == 2
