import argparse, datetime, sys
import opslib as O

def main(argv=None):
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", required=True) for k in ("item-id", "name", "detection-signal", "category")]; a = ap.parse_args(argv)
    items = O.load_yaml("checklist.yaml", [])
    if any(i["id"] == a.item_id for i in items): print("REFUSED: id already exists"); return 1
    items.append({"id": a.item_id, "name": a.name, "category": a.category, "detection_signal": a.detection_signal, "status": "unimplemented", "last_reviewed": datetime.date.today().isoformat()})
    O.save_yaml("checklist.yaml", items); print(f"added {a.item_id} (unimplemented)"); return 0

if __name__ == "__main__": sys.exit(main())
