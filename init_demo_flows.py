# Ensure local 'src' is importable when running from project root
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
