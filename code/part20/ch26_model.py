"""Load and validate incident definitions for the stress-interview drill runner."""
import json
from pathlib import Path

DEFAULT_FILE = Path(__file__).with_name("ch26_incidents.json")
REQUIRED = ["id", "number", "kind", "title", "opening", "questions", "must_ask",
            "likely_first", "root_cause", "root_cause_keywords", "mitigations",
            "destructive", "ideal_mitigation", "scoring_notes"]
MITIGATION_POINTS = 20


def load_incidents(path=DEFAULT_FILE):
    """Return a dict of incident id to incident definition, validated."""
    data = json.loads(Path(path).read_text())
    incidents = {}
    for inc in data["incidents"]:
        validate_incident(inc)
        if inc["id"] in incidents:
            raise ValueError("duplicate incident id: " + inc["id"])
        incidents[inc["id"]] = inc
    return incidents


def validate_incident(inc):
    """Raise ValueError if an incident definition would break the runner."""
    for field in REQUIRED:
        if field not in inc:
            raise ValueError("%s: missing field %s" % (inc.get("id", "?"), field))
    keys = [q["key"] for q in inc["questions"]]
    if len(keys) != len(set(keys)):
        raise ValueError(inc["id"] + ": duplicate question key")
    for q in inc["questions"]:
        if not q["keywords"] or not q["answer"]:
            raise ValueError("%s: question %s needs keywords and answer" % (inc["id"], q["key"]))
    for needed in ("impact", "dashboard", "change"):
        if needed not in keys:
            raise ValueError("%s: every incident needs a %s question" % (inc["id"], needed))
    for key in inc["must_ask"]:
        if key not in keys:
            raise ValueError("%s: must_ask names unknown key %s" % (inc["id"], key))
    total = sum(m["points"] for m in inc["mitigations"])
    if total != MITIGATION_POINTS:
        raise ValueError("%s: mitigation points are %d, need %d" % (inc["id"], total, MITIGATION_POINTS))
    for m in inc["mitigations"]:
        if not m["any"]:
            raise ValueError("%s: mitigation %s has no phrases" % (inc["id"], m["key"]))
