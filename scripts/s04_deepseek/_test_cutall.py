# -*- coding: utf-8 -*-
"""验证 apply_patch 循环全切：历史残留多份同名 Def + DS 把 Def 内嵌在目标块里，
写入后必须只剩本轮一份，不产生 already exists。"""
import io, os, sys, shutil, tempfile
sys.path.insert(0, r"C:\Users\lison\Desktop\mingbenlun_git\scripts\s04_deepseek")
from proof_loop import apply_patch

SRC = r"C:\Users\lison\Desktop\mingbenlun_git\coq\theories\ALL\Layer2.v"
base = io.open(SRC, encoding="utf-8").read()

# 造一个污染临时文件：占位 Def 之外，再残留一份多行旧 Def（模拟 run5 的累积）
stale = (
"Definition pick_prefix (g g12 g3 g1 g2 : option (option ty)) : option (option ty) :=\n"
"  if excluded_middle_informative True then None else g.\n\n")
polluted = base.replace("Lemma pick_prefix_correct", stale + "Lemma pick_prefix_correct", 1)
tmp = tempfile.NamedTemporaryFile("w", suffix=".v", delete=False, encoding="utf-8")
tmp.write(polluted); tmp.close()
assert polluted.count("Definition pick_prefix") == 2, "污染前置条件失败"

# DS 单块同时给 Def（多行正式版）+ 目标 Lemma（模拟 round2 的同块内嵌交法）
one_block = (
"Definition pick_prefix (g g12 g3 g1 g2 : option (option ty)) : option (option ty) :=\n"
"  match g with | Some _ => g | None => g end.\n\n"
"Lemma pick_prefix_correct : forall (g g12 g3 g1 g2 : option (option ty)),\n"
"  cell_split g g12 g3 -> cell_split g12 g1 g2 ->\n"
"  cell_split g g1 (pick_prefix g g12 g3 g1 g2) /\\\n"
"  cell_split (pick_prefix g g12 g3 g1 g2) g2 g3.\n"
"Proof. intros. Admitted. Qed.")
ok, msg, new_src, inserted, mode = apply_patch(tmp.name, "pick_prefix_correct", [one_block])
print("apply:", ok, mode, msg)
assert ok, msg
n = new_src.count("Definition pick_prefix")
print("最终 Definition pick_prefix 次数 =", n, "(应=1)")
assert n == 1, "循环全切失败，仍有重复定义"
assert ":= None." not in new_src, "单行占位残留"
assert "excluded_middle_informative True then None" not in new_src, "历史残留多行Def未切除"
assert "match g with | Some _ => g" in new_src, "本轮正式Def未保留"
assert "Lemma split_assoc : forall G G12 G3 G1 G2" in new_src, "主引理被误伤"
os.remove(tmp.name)
print("CUT-ALL ASSERTIONS PASSED")
