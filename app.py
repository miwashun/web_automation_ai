import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from wao.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
