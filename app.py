import argparse
import sys
from wao.validator import validate_flow, FlowValidationError
import importlib

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", help="Path to flow JSON")
    parser.add_argument("--validate", help="Validate flow JSON and exit", action="store_true")
    args = parser.parse_args()

    if not args.run:
        parser.error("--run <flow_json> は必須です")

    # ★ ここで検証を実行
    try:
        flow_dict = validate_flow(args.run)
    except FlowValidationError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    if args.validate:
        print(f"[OK] Flow is valid: {args.run}")
        sys.exit(0)

    # --- Execute with existing Runner implementation ---
    # We don't know the exact API surface of wao.runner in every branch, so we try common patterns.
    try:
        runner_mod = importlib.import_module("wao.runner")
    except Exception as e:
        print(f"Failed to import wao.runner: {e}", file=sys.stderr)
        sys.exit(3)

    def _try_call_success(func, *pargs):
        try:
            func(*pargs)
            return True   # 戻り値が None でも成功扱い
        except TypeError:
            return False  # 引数シグネチャが違う → 次の候補へ

    # Try known entrypoints in order:
    executed = False

    # 1) Function accepting a dict
    for fn_name in ("run_flow_dict", "run_flow", "run"):
        if hasattr(runner_mod, fn_name):
            fn = getattr(runner_mod, fn_name)
            if _try_call_success(fn, flow_dict):
                executed = True
                break

    # 2) Function accepting a path (fallback)
    if not executed:
        for fn_name in ("run_flow_path", "run_flow", "run"):
            if hasattr(runner_mod, fn_name):
                fn = getattr(runner_mod, fn_name)
                if _try_call_success(fn, args.run):
                    executed = True
                    break

    # 3) Class-based runner
    if not executed and hasattr(runner_mod, "Runner"):
        Runner = getattr(runner_mod, "Runner")
        runner = None
        for ctor_args in ((), (flow_dict,), (args.run,)):
            try:
                runner = Runner(*ctor_args)
                break
            except TypeError:
                continue
        if runner:
            for m in ("run", "execute", "start"):
                if hasattr(runner, m):
                    meth = getattr(runner, m)
                    # どれか一つ呼べればOK（戻り値は無視）
                    if (_try_call_success(meth, flow_dict)
                        or _try_call_success(meth, args.run)
                        or _try_call_success(meth)):
                        executed = True
                        break

    if not executed:
        print("Could not locate a compatible entrypoint in wao.runner. "
              "Please expose one of: run_flow_dict(flow: dict), run_flow(flow: dict|path), run(path), "
              "or a Runner class with run(flow|path).", file=sys.stderr)
        sys.exit(4)

if __name__ == "__main__":
    raise SystemExit(main())
