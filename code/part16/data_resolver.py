import argparse, hashlib, json, os
from pathlib import Path

def resolve(dataset_id: str, metadata_db: str = "metadata.json") -> dict:
    """Look up a dataset by id. The DB is small enough to cache locally."""
    records = json.loads(Path(metadata_db).read_text())
    for r in records:
        if r["dataset_id"] == dataset_id:
            return r
    raise KeyError(f"unknown dataset_id: {dataset_id}")

def verify(record: dict, path: Path) -> None:
    """Refuse to read a file whose bytes do not match the recorded hash."""
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    if h != record["content_hash"]:
        raise ValueError(
            f"hash mismatch at {path}: expected {record['content_hash']}, got {h}"
        )

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-id", required=True)
    ap.add_argument("--local-path", required=True)
    ap.add_argument("--metadata-db", default="metadata.json")
    args = ap.parse_args()

    record = resolve(args.dataset_id, args.metadata_db)
    if not Path(args.local_path).exists():
        raise FileNotFoundError(
            f"{args.local_path} missing; pull with `dvc pull` or the lakeFS CLI"
        )
    verify(record, Path(args.local_path))
    print(f"verified {args.local_path} as {record['content_hash'][:12]}")
