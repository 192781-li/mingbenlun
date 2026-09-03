# -*- coding: utf-8 -*-
import py_compile, os, sys
d = os.path.dirname(os.path.abspath(__file__))
for f in ['_paths.py','s04_context.py','proof_loop.py','ds_v4.py']:
    py_compile.compile(os.path.join(d,f), doraise=True)
    print('compile OK', f)

sys.path.insert(0, d)
from s04_context import build_messages, approx_tokens
from _paths import NOTES

cand = [
    r"哲学研究/S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",
    r"哲学研究/S04致S01_OB009深度对话_线性操作权同一性与代换指回_数学哲学一体化_20260902.md",
    r"哲学研究/S01对S04_substitution_general卡点研判_use关系代换_20260902.md",
    r"哲学研究/S01给S04_substitution_general精确证明骨架_防止DeepSeek跑偏_20260902.md",
]
phil = [p for p in cand if (NOTES/p).exists()]
print("哲学文档命中:", len(phil))
for p in phil: print("  -", p)
m = build_messages("test", philos_docs=tuple(phil))
tok = approx_tokens(m)
print("总估算token", tok, "占1M %.2f%%" % (tok/1e6*100))
blob = "\n".join(x["content"] for x in m)
for k in ["操作权","strengthening","存在论","代换","typed_strengthen_unused"]:
    print("  ", "OK" if k in blob else "缺", k, blob.count(k))
