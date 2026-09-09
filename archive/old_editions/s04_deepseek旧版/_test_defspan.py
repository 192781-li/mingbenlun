# -*- coding: utf-8 -*-
"""验证 apply_patch 对'全新引理 + DS 替换单行占位 Definition'的处理（结晶018 机制修复单测）。"""
import io, sys
sys.path.insert(0, r"C:\Users\lison\Desktop\mingbenlun_git\scripts\s04_deepseek")
from proof_loop import apply_patch, lemma_span, def_span
P = r"C:\Users\lison\Desktop\mingbenlun_git\coq\theories\ALL\Layer2.v"
s = io.open(P, encoding="utf-8").read()

# 1) def_span 能定位单行占位
sp = def_span(s, "pick_prefix")
print("def_span placeholder:", sp, "->", repr(s[sp[0]:sp[1]]) if sp else None)
assert sp and ":= None." in s[sp[0]:sp[1]], "def_span 未定位到单行占位"

# 2) lemma_span 能定位占位 Lemma（Admitted）
ls = lemma_span(s, "pick_prefix_correct")
print("lemma_span:", ls, "ends Admitted:", s[ls[0]:ls[1]].rstrip().endswith("Admitted.") if ls else None)
assert ls, "lemma_span 定位不到目标占位"

# 3) 模拟 DS 一轮交：正式（多行）Definition + 目标 Lemma 的 Qed 版
new_def = (
"Definition pick_prefix (g g12 g3 g1 g2 : option (option ty)) : option (option ty) :=\n"
"  match g, g12, g3, g1, g2 with _ => g end.")
new_lemma = (
"Lemma pick_prefix_correct : forall (g g12 g3 g1 g2 : option (option ty)),\n"
"  cell_split g g12 g3 -> cell_split g12 g1 g2 ->\n"
"  cell_split g g1 (pick_prefix g g12 g3 g1 g2) /\\\n"
"  cell_split (pick_prefix g g12 g3 g1 g2) g2 g3.\n"
"Proof. intros. Admitted. Qed.")  # 仅测文本替换机制，不要求真证明（含 Admitted 仅为占位文本）
blocks = ["```coq\n(* INSERT-BEFORE: pick_prefix_correct *)\n"+new_def+"\n```",
          "```coq\n"+new_lemma+"\n```"]
# apply_patch 直接吃已抽取的 block 文本
ok, msg, new_src, inserted, mode = apply_patch(P, "pick_prefix_correct", [new_def, new_lemma])
print("apply:", ok, mode, msg)
assert ok, "apply_patch 失败: %s" % msg
print("Definition pick_prefix 出现次数 =", new_src.count("Definition pick_prefix"), "(应=1)")
print("占位 ':= None.' 残留 =", (":= None." in new_src), "(应False)")
print("目标段仍Admitted占位 =", new_src.count("Proof. Admitted.\n\nLemma split_assoc") , "| split_assoc仍在 =", "Lemma split_assoc : forall G G12 G3 G1 G2" in new_src)
assert new_src.count("Definition pick_prefix") == 1, "旧占位Definition未被切除→重复定义"
assert ":= None." not in new_src, "单行占位实现残留"
assert "match g, g12, g3, g1, g2" in new_src, "DS正式Definition未写入"
assert "Lemma split_assoc : forall G G12 G3 G1 G2" in new_src, "主引理被误伤"
print("ALL ASSERTIONS PASSED")
