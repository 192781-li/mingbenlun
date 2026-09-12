"""run_all.py — 运行全部 doctest，验证代码包健康。

用法：
    cd 模块化全本
    python core/run_all.py
"""
import doctest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core  # noqa: E402


def main() -> int:
    results = []
    for mod in core.__all__:
        m = getattr(core, mod)
        r = doctest.testmod(m, verbose=False)
        results.append((mod, r.attempted, r.failed))
    total_fail = sum(f for _, _, f in results)
    for mod, attempted, failed in results:
        if attempted == 0:
            status = "EMPTY"
        elif failed == 0:
            status = "OK"
        else:
            status = "FAIL"
        print(f"{mod:18s} doctests={attempted:3d} failed={failed} [{status}]")
    print("---")
    print("ALL PASS" if total_fail == 0 else f"{total_fail} FAILURES")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
