# code/part20/c29_schedule.py
"""Dated study schedule for the Nebius SRE loop.

Usage: python3 c29_schedule.py 2026-12-15 --hours 10 [--today 2026-11-09]

Pick the plan from the days left: 56 or more gives the 8-week plan,
21 to 55 gives the 3-week plan, 10 to 20 gives the 10-day plan, and
2 to 9 gives the tail of the 10-day plan. Fewer than 2 days is an error.
The plan always ends the day before the interview.
"""
import argparse
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    name: str
    days: int
    blocks: tuple  # (days, label, stage, chapters, checkpoint, load)


EIGHT_WEEK = Template("8-week", 56, (
    (7, "Week 1", "Linux console", "20.1, 20.3, 20.4",
     "Run the 60-second checklist and read /proc/PID/fd and limits without notes.", 1.0),
    (7, "Week 2", "Linux console", "20.5, 20.6, 20.7",
     "Triage load, memory, disk and a refused or slow connect out loud in 10 minutes each.", 1.0),
    (7, "Week 3", "Coding", "20.8, 20.9, 20.10, 20.11",
     "Solve one medium problem in 30 minutes, tested by hand, complexity stated.", 1.0),
    (7, "Week 4", "System design", "20.12, 20.13, 20.14",
     "Do the GPU-count estimate on a blank page and speak a 45-minute design plan.", 1.0),
    (7, "Week 5", "System design", "20.15, 20.16, 20.19, 20.25",
     "State SLIs, the burn-rate table and three PromQL traps from memory.", 1.0),
    (7, "Week 6", "Inference SRE", "20.18, 20.20, 20.21, 20.22",
     "Name a cause and first check for each failure signature; design a retry policy.", 1.0),
    (7, "Week 7", "Stress interview", "20.23, 20.24, 20.26",
     "Play two 30-minute incident drills, one inference and one general.", 1.0),
    (7, "Week 8", "Final round", "20.27, 20.28, 20.30-20.33, 20.29",
     "Tell the project story in 2 minutes and defend one decision; no new topics.", 0.6),
))

THREE_WEEK = Template("3-week", 21, (
    (7, "Week 1", "Linux console and coding", "20.3, 20.4, 20.5, 20.6, 20.8, 20.9",
     "Triage a box aloud; solve one rate limiter or top-k problem.", 1.0),
    (7, "Week 2", "System design and inference SRE", "20.12, 20.13, 20.18, 20.19, 20.21",
     "Estimate GPUs, state SLIs and burn rates, name the retry rules.", 1.0),
    (7, "Week 3", "Stress interview and final round", "20.26, 20.28, 20.29",
     "Two incident drills and the project story; no new topics in the last 2 days.", 0.7),
))

TEN_DAY = Template("10-day", 10, (
    (2, "Days 1-2", "Linux console", "20.3, 20.4, 20.5",
     "Run the 60-second checklist; explain EMFILE, load average and OOM kill.", 1.0),
    (2, "Days 3-4", "Coding", "20.8, 20.9",
     "One problem aloud with a test; say the seven steps.", 1.0),
    (2, "Days 5-6", "System design", "20.12, 20.13, 20.19",
     "Estimate GPUs and speak the design plan; give the burn-rate table.", 1.0),
    (2, "Days 7-8", "Stress interview", "20.18, 20.21, 20.26",
     "Two incident drills; failure signatures and retry rules.", 1.0),
    (2, "Days 9-10", "Final week", "20.28, 20.29",
     "Project story, cheat sheet once, logistics check, early sleep.", 0.5),
))


def choose_template(days_left):
    if days_left < 2:
        raise ValueError("fewer than 2 days left: use the day-before routine only")
    if days_left >= 56:
        return EIGHT_WEEK
    if days_left >= 21:
        return THREE_WEEK
    return TEN_DAY


@dataclass(frozen=True)
class Block:
    start: dt.date
    end: dt.date
    label: str
    stage: str
    chapters: str
    hours: float
    checkpoint: str


def _round_half(x):
    return round(x * 2) / 2


def build_schedule(interview, weekly_hours, today):
    """Return (template_name, spare_days, blocks, interview_day_note).

    The plan covers the last N days before the interview, N set by the
    template. spare_days is how many days you have before the plan starts.
    """
    if not isinstance(interview, dt.date) or not isinstance(today, dt.date):
        raise TypeError("interview and today must be datetime.date")
    if weekly_hours <= 0:
        raise ValueError("weekly_hours must be positive")
    days_left = (interview - today).days
    if days_left < 0:
        raise ValueError("interview date is in the past")
    tpl = choose_template(days_left)
    window = min(days_left, tpl.days)
    plan_start = interview - dt.timedelta(days=window)
    spare = days_left - window
    blocks = []
    cursor = interview - dt.timedelta(days=tpl.days)
    for days, label, stage, chapters, checkpoint, load in tpl.blocks:
        b_start = cursor
        b_end = cursor + dt.timedelta(days=days - 1)
        cursor = b_end + dt.timedelta(days=1)
        if b_end < plan_start:
            continue
        b_start = max(b_start, plan_start)
        n = (b_end - b_start).days + 1
        hours = _round_half(weekly_hours * n / 7 * load)
        blocks.append(Block(b_start, b_end, label, stage, chapters, hours, checkpoint))
    return tpl.name, spare, blocks


def render(interview, weekly_hours, today):
    name, spare, blocks = build_schedule(interview, weekly_hours, today)
    out = [f"Plan: {name}, {weekly_hours} h per week, interview {interview}"]
    if spare:
        out.append(f"You have {spare} spare days before the plan starts: "
                   "use them to set up the lab and re-read your weakest chapters.")
    for b in blocks:
        out.append(f"{b.start} to {b.end} | {b.label} | {b.stage} | "
                   f"chapters {b.chapters} | {b.hours} h")
        out.append(f"    checkpoint: {b.checkpoint}")
    out.append(f"{interview} | Interview day | morning routine only, no new study")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("interview", help="interview date, YYYY-MM-DD")
    p.add_argument("--hours", type=float, default=10.0, help="study hours per week")
    p.add_argument("--today", default=None, help="override today, YYYY-MM-DD")
    a = p.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    print(render(dt.date.fromisoformat(a.interview), a.hours, today))


if __name__ == "__main__":
    main()
