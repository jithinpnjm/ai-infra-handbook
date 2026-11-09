import argparse, sys
import execute_game_day as g

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--scenario", required=True); a = ap.parse_args(argv); return g.main(["--scenario", a.scenario])

if __name__ == "__main__": sys.exit(main())
