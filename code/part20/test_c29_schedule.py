# code/part20/test_c29_schedule.py
import datetime as dt

import pytest

from c29_schedule import build_schedule, choose_template, main, render

D = dt.date
INTERVIEW = D(2026, 12, 21)


def test_exactly_eight_weeks_uses_eight_week_plan():
    name, spare, blocks = build_schedule(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=56))
    assert name == "8-week" and spare == 0 and len(blocks) == 8
    assert blocks[0].start == INTERVIEW - dt.timedelta(days=56)
    assert blocks[-1].end == INTERVIEW - dt.timedelta(days=1)


def test_more_than_eight_weeks_reports_spare_days():
    name, spare, blocks = build_schedule(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=70))
    assert name == "8-week" and spare == 14 and len(blocks) == 8


def test_blocks_are_contiguous():
    _, _, blocks = build_schedule(INTERVIEW, 8, INTERVIEW - dt.timedelta(days=60))
    for a, b in zip(blocks, blocks[1:]):
        assert b.start == a.end + dt.timedelta(days=1)


def test_less_than_eight_weeks_uses_three_week_plan():
    name, spare, blocks = build_schedule(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=55))
    assert name == "3-week" and len(blocks) == 3 and spare == 34


def test_three_week_boundary():
    assert choose_template(21).name == "3-week"
    assert choose_template(20).name == "10-day"


def test_ten_day_plan():
    name, spare, blocks = build_schedule(INTERVIEW, 14, INTERVIEW - dt.timedelta(days=10))
    assert name == "10-day" and spare == 0 and len(blocks) == 5


def test_under_ten_days_drops_early_blocks():
    name, spare, blocks = build_schedule(INTERVIEW, 14, INTERVIEW - dt.timedelta(days=5))
    assert name == "10-day" and spare == 0
    assert blocks[0].start == INTERVIEW - dt.timedelta(days=5)
    assert blocks[-1].end == INTERVIEW - dt.timedelta(days=1)
    assert all(b.hours > 0 for b in blocks)


def test_clipped_block_gets_proportional_hours():
    _, _, blocks = build_schedule(INTERVIEW, 14, INTERVIEW - dt.timedelta(days=3))
    # 3 days: a 2-day block clipped to 1 day (2 h) plus the final block at load 0.5 (2 h)
    assert sum(b.hours for b in blocks) == pytest.approx(4.0)


def test_too_late_raises():
    with pytest.raises(ValueError):
        build_schedule(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=1))


def test_interview_in_past_raises():
    with pytest.raises(ValueError):
        build_schedule(INTERVIEW, 10, INTERVIEW + dt.timedelta(days=1))


@pytest.mark.parametrize("h", [0, -3])
def test_bad_hours(h):
    with pytest.raises(ValueError):
        build_schedule(INTERVIEW, h, INTERVIEW - dt.timedelta(days=60))


def test_bad_types():
    with pytest.raises(TypeError):
        build_schedule("2026-12-21", 10, INTERVIEW)


def test_hours_scale_with_weekly_hours():
    _, _, a = build_schedule(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=56))
    _, _, b = build_schedule(INTERVIEW, 20, INTERVIEW - dt.timedelta(days=56))
    assert b[0].hours == 2 * a[0].hours
    assert a[0].hours == 10.0


def test_final_week_is_tapered():
    _, _, blocks = build_schedule(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=56))
    assert blocks[-1].hours == 6.0


def test_eight_week_plan_covers_each_core_chapter():
    _, _, blocks = build_schedule(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=56))
    text = " ".join(b.chapters for b in blocks)
    for n in list(range(3, 15)) + [15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]:
        assert f"20.{n}" in text


def test_render_and_cli(capsys):
    out = render(INTERVIEW, 10, INTERVIEW - dt.timedelta(days=70))
    assert "spare days" in out and "Interview day" in out
    main([INTERVIEW.isoformat(), "--hours", "6", "--today", "2026-10-01"])
    assert "8-week" in capsys.readouterr().out
