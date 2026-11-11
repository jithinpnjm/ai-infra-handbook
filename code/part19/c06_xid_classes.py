"""Map an Xid to the action class this chapter's policy uses (chapter 19.6).

The classes follow the immediate action in the NVIDIA Xid catalog. The class names
and the choice to leave application and self-healing codes alone are this chapter's
policy, not NVIDIA's. An unknown code is never ignored.
"""

# Xid -> catalog "immediate action" (fetched 2026-11-10, see c06_xid_catalog_snapshot.csv).
CATALOG_IMMEDIATE = {
    13: "RESTART_APP", 31: "RESTART_APP", 32: "RESTART_APP", 43: "IGNORE",
    45: "WORKFLOW_XID_45", 48: "WORKFLOW_XID_48", 62: "RESET_GPU", 63: "IGNORE",
    64: "RESET_GPU", 74: "WORKFLOW_NVLINK_ERR", 79: "RESTART_BM", 92: "IGNORE",
    94: "RESTART_APP", 95: "RESET_GPU", 119: "RESET_GPU", 120: "RESET_GPU",
}

UNRECOVERABLE = "unrecoverable"    # GPU reset or node restart needed: cordon, drain, ticket
INTERCONNECT = "interconnect"      # NVLink: label the node, keep mesh-critical jobs off it
APPLICATION = "application"        # restart the process; escalate only on a pattern
SELF_HEALING = "self_healing"      # track the rate, take no action
SYMPTOM = "symptom"                # Xid 45: read the Xid that came before it
UNKNOWN = "unknown"                # not in the table: a human looks, nothing is ignored

CLASS_OF = {
    13: APPLICATION, 31: APPLICATION, 32: APPLICATION, 94: APPLICATION,
    43: SELF_HEALING, 63: SELF_HEALING, 92: SELF_HEALING,
    45: SYMPTOM, 74: INTERCONNECT,
    48: UNRECOVERABLE, 62: UNRECOVERABLE, 64: UNRECOVERABLE, 79: UNRECOVERABLE,
    95: UNRECOVERABLE, 119: UNRECOVERABLE, 120: UNRECOVERABLE,
}


def classify_xid(xid):
    """Return the action class for an Xid code."""
    return CLASS_OF.get(xid, UNKNOWN)
