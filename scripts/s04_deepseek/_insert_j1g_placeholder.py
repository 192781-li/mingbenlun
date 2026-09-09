# -*- coding: utf-8 -*-
"""一次性：在 Layer2.v 主引理 split_assoc 前插入 J1g 待证目标占位
（单行 Definition pick_prefix 占位 + Lemma pick_prefix_correct Admitted）。
只立规格、不写 tactic；实现/证明由 DS 主谋闭环替换。幂等：已存在则不重复插。"""
import io, sys
P = r"C:\Users\lison\Desktop\mingbenlun_git\coq\theories\ALL\Layer2.v"
s = io.open(P, encoding="utf-8").read()
if "Lemma pick_prefix_correct" in s:
    print("already inserted, skip"); sys.exit(0)

anchor = (
"Lemma split_assoc : forall G G12 G3 G1 G2,\n"
"  split G G12 G3 -> split G12 G1 G2 ->\n"
"  exists G23, split G G1 G23 /\\ split G23 G2 G3.\n"
"Proof. Admitted."
)
assert s.count(anchor) == 1, "anchor count=%d" % s.count(anchor)

ph = (
"(* =====================================================================\n"
"   J1g placeholder: S04 only states the goal spec (no tactic). The Some-first\n"
"   implementation and proof are produced by DeepSeek loop: the one-line\n"
"   Definition placeholder is cut by def_span, the Lemma by lemma_span.\n"
"   ===================================================================== *)\n"
"Definition pick_prefix (g g12 g3 g1 g2 : option (option ty)) : option (option ty) := None.\n"
"\n"
"Lemma pick_prefix_correct : forall (g g12 g3 g1 g2 : option (option ty)),\n"
"  cell_split g g12 g3 ->\n"
"  cell_split g12 g1 g2 ->\n"
"  cell_split g g1 (pick_prefix g g12 g3 g1 g2) /\\\n"
"  cell_split (pick_prefix g g12 g3 g1 g2) g2 g3.\n"
"Proof. Admitted.\n"
"\n"
)
s2 = s.replace(anchor, ph + anchor, 1)
io.open(P, "w", encoding="utf-8").write(s2)
print("inserted. pick_prefix_correct count =", s2.count("Lemma pick_prefix_correct"))
