"""E11: one shard id is missing from 0..n."""


def missing_shard(ids, n):
    """ids holds n distinct values from 0..n. Return the one that is absent."""
    return n * (n + 1) // 2 - sum(ids)
